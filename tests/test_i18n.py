"""The strings of the interfaces (locales/): the same in every language, with the same placeholders.

The web interface and the report (frontend/) import them; frontend/ui/src/i18n/translate.ts reads
them, and its tests say how.
"""

import json
import re

import pytest

from quiz.logic import load_questions
from utils.paths import LOCALES

LANGUAGES = ("en", "it")
NAMESPACES = sorted(p.stem for p in (LOCALES / LANGUAGES[0]).glob("*.json"))


def _read(lang, namespace):
    return json.loads((LOCALES / lang / f"{namespace}.json").read_text(encoding="utf-8"))


def _leaves(node, path=""):
    """Every string of a namespace, by dotted path; plural forms count as one string."""
    if isinstance(node, str) or set(node) == {"one", "other"}:
        yield path, node
        return
    for key, value in node.items():
        yield from _leaves(value, f"{path}.{key}" if path else key)


def _placeholders(entry):
    texts = [entry] if isinstance(entry, str) else entry.values()
    return {name for text in texts for name in re.findall(r"\{(\w+)\}", text)}


def test_every_language_has_the_same_files():
    assert NAMESPACES == ["app", "common", "gallery", "report", "taxonomy"]
    for lang in LANGUAGES:
        assert sorted(p.stem for p in (LOCALES / lang).glob("*.json")) == NAMESPACES


@pytest.mark.parametrize("namespace", NAMESPACES)
def test_every_language_has_the_same_strings_with_the_same_placeholders(namespace):
    english = dict(_leaves(_read("en", namespace)))
    for lang in LANGUAGES:
        strings = dict(_leaves(_read(lang, namespace)))
        assert strings.keys() == english.keys(), lang
        for path, entry in strings.items():
            assert type(entry) is type(english[path]), f"{lang}: {namespace}.{path}"
            assert _placeholders(entry) == _placeholders(english[path]), f"{lang}: {namespace}.{path}"
            assert "{{" not in str(entry), f"{lang}: {namespace}.{path} has a placeholder in double braces"


def test_the_taxonomy_names_every_domain_and_subdomain_of_the_questionnaire():
    ids = [q["id"] for q in load_questions("en")]
    for lang in LANGUAGES:
        taxonomy = _read(lang, "taxonomy")
        assert list(taxonomy["subdomains"]) == ids
        assert list(taxonomy["domains"]) == sorted({qid.split(".")[0] for qid in ids})


def test_the_report_names_every_pattern_of_the_rules():
    from agents.report_generator.report_data import PATTERNS

    patterns = {pattern for group in PATTERNS.values() for pattern in group}
    for lang in LANGUAGES:
        report = _read(lang, "report")["patterns"]
        assert set(report["names"]) == set(report["definitions"]) == patterns, lang
