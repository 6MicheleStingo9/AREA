"""Where Kindynos keeps its files: the project root, the files/ tree and the other folders it reads.

Resources that live next to their module (templates, styles, Prolog rules) stay relative to it.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = ROOT / "files"
ANSWERS = FILES / "answers"  # the questionnaire answers, one file per run
ANALYSIS = FILES / "analysis"  # domain/, causality/, heuristic/: the output of each step
REPORTS = FILES / "reports"
JOBS = FILES / "jobs"  # the state of each analysis started from the web interface
DATA = FILES / "data"  # the MIT AI Risk Repository and the Kindynos training risks
LOCALES = ROOT / "locales"  # the strings of the interface and of the report, one folder per language
WEB_BUILD = ROOT / "frontend" / "web" / "dist"  # the web interface, built by `npm run build` in frontend/
REPORT_BUILD = ROOT / "frontend" / "report" / "dist"  # the report app, built with it
