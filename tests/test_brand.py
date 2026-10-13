"""The Kindynos logo in the web pages and in the HTML report (utils/brand.py)."""

import base64
import json
from pathlib import Path

from fastapi.testclient import TestClient

import agents.report_generator.html_generator as html_generator
from api.main import app
from utils import brand

SAMPLE = (
    Path(__file__).resolve().parent.parent
    / "files/analysis/heuristic/heuristic_analysis_23d095a19c9c45c89af5c66b5ffcea63.json"
)


def test_the_favicon_is_the_mark():
    uri = brand.favicon()
    assert uri.startswith("data:image/svg+xml;base64,")
    assert base64.b64decode(uri.split(",", 1)[1]).decode("utf-8") == brand.svg("kindynos-mark")


def test_without_the_logo_files_the_pages_have_no_logo(tmp_path, monkeypatch):
    monkeypatch.setattr(brand, "BRAND_DIR", tmp_path)
    brand.svg.cache_clear()
    try:
        assert brand.svg("kindynos-mark") == "" and brand.favicon() == ""
    finally:
        brand.svg.cache_clear()


def test_the_web_pages_show_the_logo_and_the_owl():
    client = TestClient(app)
    page = client.get("/").text
    assert 'rel="icon" href="data:image/svg+xml;base64,' in page
    assert 'class="logo-mark"' in page and 'aria-label="Kindynos"' in page
    assert 'src="/brand/kindynos-owl.png"' in page
    owl = client.get("/brand/kindynos-owl.png")
    assert owl.status_code == 200 and owl.headers["content-type"] == "image/png"


def test_the_report_carries_the_mark_and_the_favicon(tmp_path, monkeypatch):
    monkeypatch.setattr(html_generator, "REPORT_DIR", tmp_path)
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    path = html_generator.generate_html_report(dict(data["metadata"], run_id="pytest"), data["heuristic"], data["analysis"], {})
    html = Path(path).read_text(encoding="utf-8")
    assert f'<link rel="icon" href="{brand.favicon()}">' in html
    assert '<span class="report-mark" aria-hidden="true"><svg' in html
