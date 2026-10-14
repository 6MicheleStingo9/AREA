"""The strings of the interface, in English and Italian: locales/<language>/<namespace>.json.

The questionnaire pages (quiz.json) and the report (report.json) read them here; the web interface in
frontend/ imports the same files (common.json, gallery.json). A string names its placeholders in
braces, like "{count}", and a string that depends on a number has one form per plural category:
{"one": "{count} risk", "other": "{count} risks"}.
"""

import json
import re
from functools import lru_cache
from typing import Any, Dict, Optional

from utils.paths import LOCALES

LANGUAGES = ("en", "it")
DEFAULT_LANGUAGE = "en"

_PLACEHOLDER = re.compile(r"\{(\w+)\}")


@lru_cache(maxsize=None)
def strings(namespace: str, lang: str = DEFAULT_LANGUAGE) -> Dict[str, Any]:
    """The strings of a namespace, one file, in a language: English for an unknown language, {} for an
    unknown namespace. The dictionary is shared between callers: read it, never change it."""
    if lang not in LANGUAGES:
        lang = DEFAULT_LANGUAGE
    try:
        return json.loads((LOCALES / lang / f"{namespace}.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def fill(text: str, **params: Any) -> str:
    """The text with its placeholders replaced; a placeholder without a value stays as it is."""
    return _PLACEHOLDER.sub(lambda m: str(params[m[1]]) if m[1] in params else m[0], text)


def t(key: str, lang: str = DEFAULT_LANGUAGE, **params: Any) -> str:
    """The string at a dotted key, "namespace.key" or deeper ("common.theme.to_dark"), filled with params.

    A key missing in the language falls back to English, then to the key itself. For a string with
    plural forms, params gives the number as count.
    """
    namespace, _, path = key.partition(".")
    for language in dict.fromkeys((lang, DEFAULT_LANGUAGE)):
        entry = _lookup(strings(namespace, language), path)
        if entry is not None:
            break
    else:
        return key
    if isinstance(entry, dict):
        # English and Italian have the same two categories: "one" for 1, "other" for every other number
        entry = entry["one"] if params.get("count") == 1 else entry["other"]
    return fill(entry, **params)


def _lookup(node: Any, path: str) -> Optional[Any]:
    """The string, or the plural forms, at a dotted path; None if the path stops before one."""
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    if isinstance(node, str) or (isinstance(node, dict) and set(node) == {"one", "other"}):
        return node
    return None
