from contextlib import asynccontextmanager

from fastapi import FastAPI

from agents.causality_analyzer import laya_classifier
from agents.causality_analyzer.causality_risk_analyzer_agent import causality_backend
from api import jobs, web
from api.assessments import router as assessments_router
from api.reports import router as reports_router
from utils.utils import create_logger

_logger = create_logger("api")


def check_causality_backend() -> None:
    """Warn at startup, rather than after a questionnaire, when the causality step cannot run."""
    try:
        backend = causality_backend()
    except ValueError as e:
        _logger.warning(f"The causality step will fail: {e}")
        return
    issue = laya_classifier.problem() if backend == "laya" else None
    if issue:
        _logger.warning(f"The causality step will fail: {issue}")
    else:
        _logger.info("Causality backend", backend=backend, model=laya_classifier.model_name() if backend == "laya" else None)


@asynccontextmanager
async def lifespan(app: FastAPI):
    check_causality_backend()
    if not web.is_built():
        _logger.warning(f"The web interface is not built: {web.BUILD_COMMAND}")
    interrupted = jobs.mark_interrupted()
    if interrupted:
        _logger.warning("Analyses interrupted by the last stop of the server", count=interrupted)
    yield


app = FastAPI(title="Kindynos — AI Risk Assessment", lifespan=lifespan)

app.include_router(assessments_router)
app.include_router(reports_router)
# Last: the page of the web interface answers every path that the routes above leave
web.install(app)
