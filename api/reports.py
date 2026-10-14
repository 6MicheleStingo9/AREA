"""The reports of the analyses: the page of each, its main results, and an archive with its data."""

import io
import json
import zipfile
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse

from api.jobs import get_job, is_run_id
from utils.paths import ANALYSIS, ANSWERS, REPORTS

router = APIRouter()


def report_path(run_id: str) -> Optional[Path]:
    """The HTML report of a run, if there is one: where its job recorded it, else where the pipeline
    writes it (the jobs of old runs may be gone)."""
    if not is_run_id(run_id):
        return None
    job = get_job(run_id)
    if job and job.get("html_path") and Path(job["html_path"]).exists():
        return Path(job["html_path"])
    path = REPORTS / f"ai_risk_report_{run_id}.html"
    return path if path.exists() else None


def results(run_id: str) -> Optional[Dict[str, Any]]:
    """The main results of a finished run, from its heuristic analysis: the summary of its report."""
    try:
        path = ANALYSIS / "heuristic" / f"heuristic_analysis_{run_id}.json"
        heuristic = json.loads(path.read_text(encoding="utf-8"))["heuristic"]
    except (OSError, ValueError, KeyError):
        return None
    summary, counting = heuristic.get("executive_summary", {}), heuristic.get("counting", {})
    critical = summary.get("most_critical_domain")  # none without high-severity risks
    return {
        "score": summary.get("global_risk_score"),
        "level": summary.get("overall_risk_level"),
        "concern": summary.get("primary_concern"),
        "action": summary.get("recommended_action"),
        "critical_domain": {"id": str(critical["domain"]), "high": critical["high_count"]} if critical else None,
        "risks": counting.get("total_risks", 0),
        "domains": sum(1 for count in counting.get("by_domain", {}).values() if count),
        "severity": counting.get("by_severity", {}),
    }


def archive(run_id: str) -> Optional[bytes]:
    """A ZIP with the report of a run and the data behind it: the answers and the three analyses."""
    report = report_path(run_id)
    if report is None:
        return None
    files = {
        "report.html": report,
        "report_metadata.json": REPORTS / f"report_metadata_{run_id}.json",
        "answers.json": ANSWERS / f"answers_{run_id}.json",
        "analysis/domain.json": ANALYSIS / "domain" / f"domain_analysis_{run_id}.json",
        "analysis/causality.json": ANALYSIS / "causality" / f"causality_analysis_{run_id}.json",
        "analysis/heuristic.json": ANALYSIS / "heuristic" / f"heuristic_analysis_{run_id}.json",
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, path in files.items():
            if path.exists():
                zf.write(path, name)
    return buffer.getvalue()


@router.get("/report/{run_id}", response_class=HTMLResponse)
async def serve_report(run_id: str):
    path = report_path(run_id)
    if path is None:
        return HTMLResponse("<h1>404 — Report not found</h1>", status_code=404)
    return FileResponse(str(path), media_type="text/html")
