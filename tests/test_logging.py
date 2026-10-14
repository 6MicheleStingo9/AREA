"""Logging configuration (utils/utils.py)."""

import pytest

from utils import utils


def test_the_log_level_comes_from_log_level(monkeypatch):
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    assert utils.log_level() == "INFO"
    monkeypatch.setenv("LOG_LEVEL", " debug ")
    assert utils.log_level() == "DEBUG"


def test_an_unknown_log_level_is_an_error(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "verbose")
    with pytest.raises(ValueError, match="LOG_LEVEL must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL, got 'verbose'"):
        utils.log_level()


def test_tracebacks_do_not_print_local_variables():
    # They would print secrets, such as the API key in get_llm_instance()
    assert utils.LOG_HANDLER.tracebacks_show_locals is False
