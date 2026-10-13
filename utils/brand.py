"""
The Kindynos logo (files/img/brand/), embedded in the web pages and in the HTML report.

The pages inline the SVG markup instead of linking it: the report is a standalone file that must
keep its logo offline, and the web interface then needs no copy of the files among its static
assets. A missing file leaves the pages without the logo.
"""

import base64
from functools import lru_cache
from pathlib import Path

BRAND_DIR = Path(__file__).resolve().parent.parent / "files" / "img" / "brand"


@lru_cache(maxsize=None)
def svg(name: str) -> str:
    """The SVG markup of files/img/brand/<name>.svg, or "" when the file is missing."""
    try:
        return (BRAND_DIR / f"{name}.svg").read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def favicon() -> str:
    """The square mark as a data URI for <link rel="icon">, or "" without the mark."""
    mark = svg("kindynos-mark")
    return "data:image/svg+xml;base64," + base64.b64encode(mark.encode("utf-8")).decode("ascii") if mark else ""
