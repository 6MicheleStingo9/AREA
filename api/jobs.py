"""In-memory job registry for pipeline runs. State is lost on process restart."""

from typing import Any, Dict, Optional

_jobs: Dict[str, Dict[str, Any]] = {}


def create_job(run_id: str) -> None:
    _jobs[run_id] = {"status": "pending", "html_path": None, "error": None}


def update_job(run_id: str, **kwargs: Any) -> None:
    if run_id in _jobs:
        _jobs[run_id].update(kwargs)


def get_job(run_id: str) -> Optional[Dict[str, Any]]:
    return _jobs.get(run_id)
