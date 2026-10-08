import uuid
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from api.jobs import get_job
from api.routes_run import REPORT_DIR
from api.sessions import create_session, get_session, update_session
from quiz.logic import (
    load_questions,
    parse_followup_answers,
    parse_form_answer,
    should_show_followup,
    validate_answer,
)
from quiz.translations import t

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter()


def _is_htmx(request: Request) -> bool:
    return request.headers.get("HX-Request") == "true"


def _quiz_ctx(
    request: Request,
    session_id: str,
    step: int,
    session: Dict[str, Any],
    saved: Dict[str, Any],
    *,
    error: str | None = None,
) -> Dict[str, Any]:
    """Build the template context for a quiz step."""
    question = session["questions"][step]
    lang = session["lang"]
    # Inject parent options into follow-up dicts (needed for condition evaluation)
    for fu in question.get("follow_ups", []):
        if question["type"] in ("multiple_choice", "checkbox"):
            fu["_parent_options"] = question.get("options", [])
    return {
        "request": request,
        "session_id": session_id,
        "step": step,
        "question": question,
        "total": len(session["questions"]),
        "lang": lang,
        "saved": saved,
        "error": error,
        "is_fragment": _is_htmx(request),
        "t": lambda key, **kw: t(key, lang=lang, **kw),
        "should_show_followup": should_show_followup,
    }


# ---------------------------------------------------------------------------
# Welcome page
# ---------------------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
async def welcome(request: Request):
    return templates.TemplateResponse(request, "welcome.html", {"request": request})


@router.post("/quiz/start")
async def start_quiz(request: Request):
    form = await request.form()
    lang = form.get("lang", "en")
    session_id = str(uuid.uuid4())
    questions = load_questions(lang)
    create_session(session_id, lang, questions)
    return RedirectResponse(f"/quiz/{session_id}/0", status_code=303)


# ---------------------------------------------------------------------------
# Sub-paths that must be declared BEFORE the {step: int} catch-all
# ---------------------------------------------------------------------------

@router.get("/quiz/{session_id}/done", response_class=HTMLResponse)
async def quiz_done(request: Request, session_id: str):
    session = get_session(session_id)
    if not session:
        return RedirectResponse("/")
    lang = session["lang"]
    return templates.TemplateResponse(request, "submit.html", {
        "request": request,
        "session_id": session_id,
        "total": len(session["questions"]),
        "answered": len(session["answers"]),
        "lang": lang,
        "t": lambda key, **kw: t(key, lang=lang, **kw),
    })


@router.get("/quiz/{session_id}/progress/{run_id}", response_class=HTMLResponse)
async def quiz_progress(request: Request, session_id: str, run_id: str):
    session = get_session(session_id)
    lang = session["lang"] if session else "en"
    # Status is rendered server-side so the page also works without JS (the
    # no-JS meta refresh stops once the job is finished).
    job = get_job(run_id)
    if job:
        status = job["status"]
    elif (REPORT_DIR / f"ai_risk_report_{run_id}.html").exists():
        # Job lost on restart, but the report is on disk (served by /report).
        status = "done"
    else:
        status = "not_found"
    return templates.TemplateResponse(request, "progress.html", {
        "request": request,
        "session_id": session_id,
        "run_id": run_id,
        "lang": lang,
        "status": status,
        "error": job.get("error") if job else None,
        "t": lambda key, **kw: t(key, lang=lang, **kw),
    })


# ---------------------------------------------------------------------------
# Follow-up fragment endpoint (htmx only)
# ---------------------------------------------------------------------------

@router.post("/quiz/{session_id}/{step:int}/followups", response_class=HTMLResponse)
async def followups_fragment(request: Request, session_id: str, step: int):
    session = get_session(session_id)
    if not session:
        return HTMLResponse("")
    form = await request.form()
    question = session["questions"][step]
    lang = session["lang"]
    for fu in question.get("follow_ups", []):
        if question["type"] in ("multiple_choice", "checkbox"):
            fu["_parent_options"] = question.get("options", [])
    answer = parse_form_answer(question, form)
    # Preserve any follow-up text the user already typed (the form includes the
    # current follow-up inputs via hx-include) so changing the main answer does
    # not wipe their input.
    followups = parse_followup_answers(question, answer, form)
    return templates.TemplateResponse(request, "followups_fragment.html", {
        "request": request,
        "question": question,
        "answer": answer,
        "saved": {"answer": answer, "followups": followups},
        "t": lambda key, **kw: t(key, lang=lang, **kw),
        "should_show_followup": should_show_followup,
        "session_id": session_id,
        "step": step,
    })


# ---------------------------------------------------------------------------
# Quiz step — GET
# ---------------------------------------------------------------------------

@router.get("/quiz/{session_id}/{step:int}", response_class=HTMLResponse)
async def quiz_step_get(request: Request, session_id: str, step: int):
    session = get_session(session_id)
    if not session:
        return RedirectResponse("/")
    if step >= len(session["questions"]):
        return RedirectResponse(f"/quiz/{session_id}/done")

    saved = session["answers"].get(session["questions"][step]["id"], {})
    ctx = _quiz_ctx(request, session_id, step, session, saved)

    if _is_htmx(request):
        resp = templates.TemplateResponse(request, "quiz_card.html", ctx)
        resp.headers["HX-Push-Url"] = f"/quiz/{session_id}/{step}"
        return resp
    return templates.TemplateResponse(request, "quiz.html", ctx)


# ---------------------------------------------------------------------------
# Quiz step — POST (validate + save + advance)
# ---------------------------------------------------------------------------

@router.post("/quiz/{session_id}/{step:int}")
async def quiz_step_post(request: Request, session_id: str, step: int):
    session = get_session(session_id)
    if not session:
        return RedirectResponse("/")

    form = await request.form()
    questions = session["questions"]
    question = questions[step]
    lang = session["lang"]

    for fu in question.get("follow_ups", []):
        if question["type"] in ("multiple_choice", "checkbox"):
            fu["_parent_options"] = question.get("options", [])

    answer = parse_form_answer(question, form)
    is_valid, err_msg = validate_answer(question, answer, lang)

    if not is_valid:
        # Re-render with error; preserve the submitted answer so user doesn't lose input
        saved = {"answer": answer, "followups": {}}
        ctx = _quiz_ctx(request, session_id, step, session, saved, error=err_msg)
        if _is_htmx(request):
            return templates.TemplateResponse(request, "quiz_card.html", ctx, status_code=422)
        return templates.TemplateResponse(request, "quiz.html", ctx, status_code=422)

    followup_answers = parse_followup_answers(question, answer, form)
    session["answers"][question["id"]] = {
        "question": question["question"],
        "answer": answer,
        "followups": followup_answers,
    }
    update_session(session_id, answers=session["answers"])

    next_step = step + 1

    if next_step >= len(questions):
        # Last step done → go to summary/done page
        if _is_htmx(request):
            return Response(
                status_code=204,
                headers={"HX-Redirect": f"/quiz/{session_id}/done"},
            )
        return RedirectResponse(f"/quiz/{session_id}/done", status_code=303)

    # Advance to next step
    next_saved = session["answers"].get(questions[next_step]["id"], {})
    ctx = _quiz_ctx(request, session_id, next_step, session, next_saved)

    if _is_htmx(request):
        resp = templates.TemplateResponse(request, "quiz_card.html", ctx)
        resp.headers["HX-Push-Url"] = f"/quiz/{session_id}/{next_step}"
        return resp
    return RedirectResponse(f"/quiz/{session_id}/{next_step}", status_code=303)
