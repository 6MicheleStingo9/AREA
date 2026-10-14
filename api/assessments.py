"""The JSON API of the web interface: the questionnaire, and the assessments that it starts.

An assessment is a run of the pipeline on a set of answers, in the background. Its job (api/jobs.py)
says where the run is: the step in course and its counts, then the outcome.
"""

import uuid
from pathlib import Path
from typing import Annotated, Dict, List, Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from agents.orchestrator import run_orchestrator
from api import reports
from api.jobs import create_job, get_job, update_job
from quiz.logic import load_questions, responses, save_answers, validate_assessment
from utils import progress

router = APIRouter(prefix="/api")

Language = Literal["en", "it"]
Text = Annotated[str, Field(max_length=10_000)]


class AnswerIn(BaseModel):
    """The answer to one question: text for a written answer, the index of the option for a choice,
    the indices of the options and the text of "Other" (absent while not ticked) for a checkbox."""

    text: Optional[Text] = None
    choice: Optional[int] = None
    choices: Optional[List[int]] = Field(None, max_length=100)
    other: Optional[Text] = None
    followups: Dict[str, Text] = Field(default_factory=dict, max_length=10)


class AssessmentIn(BaseModel):
    lang: Language
    # The name stays on this computer: it goes to the report, never to the LLM (quiz/logic.py)
    system_name: Optional[str] = Field(None, max_length=120)
    answers: Dict[str, AnswerIn] = Field(max_length=100)


@router.get("/questionnaire")
async def questionnaire(lang: Language = "en"):
    return {"lang": lang, "questions": load_questions(lang)}


def _error_code(error: Exception) -> str:
    """quota when Gemini refused the request for the quota (429), failed otherwise."""
    text = str(error)
    return "quota" if "RESOURCE_EXHAUSTED" in text or "429" in text else "failed"


def _run_pipeline(run_id: str, answers_path: Path) -> None:
    progress.listen(run_id, lambda step, **counts: update_job(run_id, step=step, **counts))
    try:
        update_job(run_id, status="running", step="domain")
        final_state = run_orchestrator(str(answers_path))
        html_path = final_state.get("report_state", {}).get("html_path")
        if html_path and Path(html_path).exists():
            update_job(run_id, status="done", html_path=html_path)
        else:
            update_job(run_id, status="error", error="Report file not found after pipeline run", error_code="failed")
    except Exception as exc:
        update_job(run_id, status="error", error=str(exc), error_code=_error_code(exc))
    finally:
        progress.forget(run_id)


@router.post("/assessments", status_code=201)
async def start_assessment(assessment: AssessmentIn, background_tasks: BackgroundTasks, response: Response):
    """Check the answers, save them and start the analysis. 422 with the errors of each question that
    has some (codes: quiz/logic.py)."""
    questions = load_questions(assessment.lang)
    answers = {qid: answer.model_dump(exclude_none=True) for qid, answer in assessment.answers.items()}
    errors = validate_assessment(questions, answers)
    if errors:
        return JSONResponse({"detail": "invalid_answers", "errors": errors}, status_code=422)
    run_id = uuid.uuid4().hex[:8]
    name = (assessment.system_name or "").strip() or None
    path = save_answers(responses(questions, answers), assessment.lang, len(questions), run_id=run_id, system_name=name)
    create_job(run_id, lang=assessment.lang, system_name=name)
    background_tasks.add_task(_run_pipeline, run_id, path)
    response.headers["Location"] = f"/api/assessments/{run_id}"
    return {"id": run_id}


@router.get("/assessments/{run_id}")
async def assessment_status(run_id: str):
    """Where an assessment is: pending, running (with its step), done (with its main results), error
    or interrupted (the server stopped during the run)."""
    job = get_job(run_id)
    if job is None:
        if reports.report_path(run_id) is None:
            return JSONResponse({"id": run_id, "status": "not_found"}, status_code=404)
        job = {"status": "done"}  # a report from before the jobs were kept on disk
    body = {
        "id": run_id,
        "status": job["status"],
        "step": job.get("step"),
        "risks": job.get("risks"),
        "labelled": job.get("labelled"),
        "lang": job.get("lang"),
        "system_name": job.get("system_name"),
        "error": job.get("error"),
        "error_code": job.get("error_code"),
    }
    if job["status"] == "done":
        body.update(
            result=reports.results(run_id),
            report_url=f"/report/{run_id}",
            archive_url=f"/api/assessments/{run_id}/archive",
        )
    return body


@router.get("/assessments/{run_id}/archive")
async def assessment_archive(run_id: str):
    data = reports.archive(run_id)
    if data is None:
        return JSONResponse({"id": run_id, "status": "not_found"}, status_code=404)
    disposition = f'attachment; filename="kindynos-{run_id}.zip"'
    return Response(data, media_type="application/zip", headers={"Content-Disposition": disposition})
