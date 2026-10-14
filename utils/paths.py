"""Where Kindynos keeps its files: the project root and the files/ tree, in one place.

Resources that live next to their module (templates, styles, Prolog rules) stay relative to it.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = ROOT / "files"
ANSWERS = FILES / "answers"  # the questionnaire answers, one file per run
ANALYSIS = FILES / "analysis"  # domain/, causality/, heuristic/: the output of each step
REPORTS = FILES / "reports"
DATA = FILES / "data"  # the MIT AI Risk Repository and the Kindynos training risks
