"""
The Kindynos logo (files/img/brand/), embedded in the HTML report.

The report inlines the SVG markup instead of linking it: it is a standalone file that must keep its
logo offline. A missing file leaves the report without the logo. The web interface (frontend/)
imports the same files.
"""

import base64
from functools import lru_cache
from utils.paths import FILES

BRAND_DIR = FILES / "img" / "brand"


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
