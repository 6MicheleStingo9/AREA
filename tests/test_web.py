"""The build of the new web interface, served by FastAPI (api/web.py)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api import web


def _client(build):
    app = FastAPI()
    web.install(app, build)
    return TestClient(app)


def _build(path):
    (path / "assets").mkdir(parents=True)
    (path / "index.html").write_text('<!doctype html><script src="/assets/index-1a2b.js"></script>', encoding="utf-8")
    (path / "assets" / "index-1a2b.js").write_text("console.log('ui')", encoding="utf-8")


def test_the_page_is_checked_on_every_visit_and_its_files_kept_for_good(tmp_path):
    _build(tmp_path)
    client = _client(tmp_path)
    page = client.get("/ui")
    assert page.status_code == 200 and "/assets/index-1a2b.js" in page.text
    assert page.headers["cache-control"] == "no-cache"
    script = client.get("/assets/index-1a2b.js")
    assert script.status_code == 200 and script.text == "console.log('ui')"
    assert script.headers["cache-control"] == "public, max-age=31536000, immutable"
    assert client.get("/assets/missing.js").status_code == 404


def test_without_a_build_the_page_says_how_to_build_it(tmp_path):
    client = _client(tmp_path / "dist")
    page = client.get("/ui")
    assert page.status_code == 503 and web.BUILD_COMMAND in page.text
    assert client.get("/assets/index-1a2b.js").status_code == 404


def test_a_build_made_while_the_server_runs_is_served(tmp_path):
    client = _client(tmp_path)
    assert client.get("/assets/index-1a2b.js").status_code == 404
    _build(tmp_path)
    assert client.get("/ui").status_code == 200
    assert client.get("/assets/index-1a2b.js").status_code == 200
