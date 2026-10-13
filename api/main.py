from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from agents.causality_analyzer import laya_classifier
from agents.causality_analyzer.causality_risk_analyzer_agent import causality_backend
from api.routes_quiz import router as quiz_router
from api.routes_run import router as run_router
from utils import brand
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
    yield


app = FastAPI(title="Kindynos — AI Risk Assessment", lifespan=lifespan)

app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).parent / "static")),
    name="static",
)
# The logo files (files/img/brand/): the welcome page shows the owl mascot
app.mount("/brand", StaticFiles(directory=str(brand.BRAND_DIR), check_dir=False), name="brand")

app.include_router(quiz_router)
app.include_router(run_router)
