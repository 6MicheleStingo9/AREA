import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse

from agents.orchestrator import run_orchestrator
from api.jobs import create_job, get_job, update_job
from api.sessions import get_session
from quiz.logic import save_answers

REPORT_DIR = Path(__file__).parent.parent / "files" / "reports"

router = APIRouter()


def _run_pipeline(run_id: str, answers_path: Path) -> None:
    try:
        update_job(run_id, status="running")
        final_state = run_orchestrator(str(answers_path))
        html_path = final_state.get("report_state", {}).get("html_path")
        if html_path and Path(html_path).exists():
            update_job(run_id, status="done", html_path=html_path)
        else:
            update_job(run_id, status="error", error="Report file not found after pipeline run")
    except Exception as exc:
        update_job(run_id, status="error", error=str(exc))


@router.post("/quiz/{session_id}/run")
async def run_analysis(session_id: str, background_tasks: BackgroundTasks):
    session = get_session(session_id)
    if not session:
        return RedirectResponse("/", status_code=303)

    run_id = str(uuid.uuid4())[:8]
    # Pass run_id so the whole pipeline shares one id and the report is
    # addressable as ai_risk_report_{run_id}.html (see serve_report below).
    answers_path = save_answers(
        session["answers"],
        session["lang"],
        len(session["questions"]),
        run_id=run_id,
    )
    create_job(run_id)
    background_tasks.add_task(_run_pipeline, run_id, answers_path)

    return RedirectResponse(f"/quiz/{session_id}/progress/{run_id}", status_code=303)


@router.get("/api/status/{run_id}")
async def job_status(run_id: str):
    job = get_job(run_id)
    if not job:
        return JSONResponse({"error": "Job not found"}, status_code=404)
    return JSONResponse(job)


@router.get("/report/{run_id}", response_class=HTMLResponse)
async def serve_report(run_id: str):
    # Prefer the exact path recorded by the job (correct even if naming changes);
    # fall back to reconstruction so reports survive a process restart.
    job = get_job(run_id)
    if job and job.get("html_path"):
        job_path = Path(job["html_path"])
        if job_path.exists():
            return FileResponse(str(job_path), media_type="text/html")

    html_path = REPORT_DIR / f"ai_risk_report_{run_id}.html"
    if not html_path.exists():
        return HTMLResponse("<h1>404 — Report not found</h1>", status_code=404)
    return FileResponse(str(html_path), media_type="text/html")
