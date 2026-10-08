from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.routes_quiz import router as quiz_router
from api.routes_run import router as run_router

app = FastAPI(title="AREA — AI Risk Assessment")

app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).parent / "static")),
    name="static",
)

app.include_router(quiz_router)
app.include_router(run_router)
