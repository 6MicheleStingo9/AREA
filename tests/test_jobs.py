"""The state of the analyses started from the web interface survives a restart (api/jobs.py)."""

import pytest
from api import jobs


@pytest.fixture
def jobs_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(jobs, "JOBS", tmp_path)
    monkeypatch.setattr(jobs, "_jobs", {})
    return tmp_path


def _restart():
    jobs._jobs.clear()  # a new process knows only what is on disk


def test_a_finished_analysis_keeps_its_outcome_after_a_restart(jobs_dir):
    jobs.create_job("abc123")
    jobs.update_job("abc123", status="error", error="429 RESOURCE_EXHAUSTED")
    _restart()
    assert jobs.get_job("abc123") == {"status": "error", "html_path": None, "error": "429 RESOURCE_EXHAUSTED"}


def test_an_analysis_cut_short_by_a_restart_is_interrupted(jobs_dir):
    jobs.create_job("abc123")
    jobs.update_job("abc123", status="running")
    jobs.create_job("def456")
    jobs.update_job("def456", status="done", html_path="/x.html")
    _restart()
    assert jobs.mark_interrupted() == 1
    assert jobs.get_job("abc123")["status"] == "interrupted"
    assert jobs.get_job("def456")["status"] == "done"


def test_an_id_that_is_not_a_run_id_never_reaches_the_disk(jobs_dir):
    assert jobs.get_job("..") is None and jobs.get_job("a/b") is None
    jobs.create_job("../x")
    assert list(jobs_dir.iterdir()) == []
