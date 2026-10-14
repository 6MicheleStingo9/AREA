"""The strings of the interface (locales/, utils/i18n.py): the same in every language, and how t() reads them."""

import json
import re

import pytest

from quiz.logic import validate_answer
from utils import i18n
from utils.paths import LOCALES

NAMESPACES = sorted(p.stem for p in (LOCALES / i18n.DEFAULT_LANGUAGE).glob("*.json"))


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
    assert NAMESPACES == ["common", "gallery", "quiz", "report"]
    for lang in i18n.LANGUAGES:
        assert sorted(p.stem for p in (LOCALES / lang).glob("*.json")) == NAMESPACES


@pytest.mark.parametrize("namespace", NAMESPACES)
def test_every_language_has_the_same_strings_with_the_same_placeholders(namespace):
    english = dict(_leaves(json.loads((LOCALES / "en" / f"{namespace}.json").read_text(encoding="utf-8"))))
    for lang in i18n.LANGUAGES:
        strings = dict(_leaves(json.loads((LOCALES / lang / f"{namespace}.json").read_text(encoding="utf-8"))))
        assert strings.keys() == english.keys(), lang
        for path, entry in strings.items():
            assert type(entry) is type(english[path]), f"{lang}: {namespace}.{path}"
            assert _placeholders(entry) == _placeholders(english[path]), f"{lang}: {namespace}.{path}"
            assert "{{" not in str(entry), f"{lang}: {namespace}.{path} has a placeholder in double braces"


def test_t_reads_a_dotted_key_in_the_language():
    assert i18n.t("quiz.next_button", "it") == "Avanti →"
    assert i18n.t("common.theme.to_dark", "en") == "Switch to the dark theme"


def test_t_fills_the_placeholders():
    assert i18n.t("quiz.min_length_validation", "en", min_length=10) == "The answer must contain at least 10 characters"
    # A placeholder without a value stays visible, and braces that are not placeholders stay as they are
    assert i18n.fill("{count} of {total}", count=3) == "3 of {total}"
    assert i18n.fill("a {b c}", b=1) == "a {b c}"


def test_t_picks_the_plural_form_from_count():
    assert i18n.t("gallery.badges.risks", "en", count=1) == "1 risk"
    assert i18n.t("gallery.badges.risks", "it", count=34) == "34 rischi"
    assert i18n.t("gallery.badges.risks", "it", count=0) == "0 rischi"


def test_t_falls_back_to_english_then_to_the_key(monkeypatch, tmp_path):
    for lang, strings in (("en", {"only_english": "English", "both": "English"}), ("it", {"both": "Italiano"})):
        (tmp_path / lang).mkdir()
        (tmp_path / lang / "test.json").write_text(json.dumps(strings), encoding="utf-8")
    monkeypatch.setattr(i18n, "LOCALES", tmp_path)
    i18n.strings.cache_clear()
    try:
        assert i18n.t("test.both", "it") == "Italiano"
        assert i18n.t("test.only_english", "it") == "English"
        assert i18n.t("test.missing", "it") == "test.missing"
        assert i18n.t("nonexistent.key", "it") == "nonexistent.key"
        assert i18n.t("test.both", "fr") == "English"  # an unknown language reads English
    finally:
        i18n.strings.cache_clear()


def test_a_key_that_stops_at_a_group_is_not_a_string():
    assert i18n.t("common.theme", "en") == "common.theme"


def test_the_questionnaire_validation_speaks_the_language_of_the_questionnaire():
    question = {"type": "free_text", "required": True, "validation": {"min_length": 10}}
    assert validate_answer(question, "", "it") == (False, "Questa domanda è obbligatoria")
    assert validate_answer(question, "short", "en") == (False, "The answer must contain at least 10 characters")
