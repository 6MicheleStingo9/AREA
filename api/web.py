"""The new web interface (frontend/web), served from its build in frontend/web/dist.

For now it is one page, at /ui: the components that the questionnaire and the report will share. Vite
names the files of the build after their content, so a browser can keep them for good; the page that
loads them is checked again on every visit.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from starlette.types import Scope

from utils.paths import WEB_BUILD

BUILD_COMMAND = "cd frontend && npm ci && npm run build"

_NOT_BUILT = f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>Kindynos · Not built</title>
<p>The web interface is not built yet. Build it with <code>{BUILD_COMMAND}</code>, then reload this page.</p>
</html>
"""


class _BuildFiles(StaticFiles):
    """The files of the build. The directory can appear after the server starts: until then, 404."""

    async def check_config(self) -> None:
        if Path(self.directory).is_dir():
            await super().check_config()

    async def get_response(self, path: str, scope: Scope) -> Response:
        response = await super().get_response(path, scope)
        if response.status_code == 200:
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response


def is_built(build: Path = WEB_BUILD) -> bool:
    return (build / "index.html").is_file()


def install(app: FastAPI, build: Path = WEB_BUILD) -> None:
    """Serve the build: its files under /assets, its page at /ui."""
    app.mount("/assets", _BuildFiles(directory=build / "assets", check_dir=False), name="assets")

    @app.get("/ui", include_in_schema=False)
    async def interface():
        if not is_built(build):
            return HTMLResponse(_NOT_BUILT, status_code=503)
        return FileResponse(build / "index.html", headers={"Cache-Control": "no-cache"})
