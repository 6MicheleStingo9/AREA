"""LLM client configuration (utils/utils.py)."""

from utils.utils import get_llm_instance


def test_apply_retry_is_the_only_retry_layer(monkeypatch):
    # SDK retries would run inside every apply_retry() attempt (5 x 6 calls).
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    assert get_llm_instance().max_retries == 0
