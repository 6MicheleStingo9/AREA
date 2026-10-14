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
LOCALES = ROOT / "locales"  # the strings of the interface, one folder per language (utils/i18n.py)
WEB_BUILD = ROOT / "frontend" / "web" / "dist"  # the web interface, built by `npm run build` in frontend/
