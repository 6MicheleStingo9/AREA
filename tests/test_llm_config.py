"""LLM client configuration (utils/utils.py)."""

from langchain_core.runnables import RunnableLambda

from utils.utils import apply_retry, get_llm_instance


def test_apply_retry_is_the_only_retry_layer(monkeypatch):
    # SDK retries would run inside every apply_retry() attempt (5 x 6 calls).
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    llm = get_llm_instance()
    assert llm.max_retries == 0
    assert llm.timeout  # a stuck request must fail for apply_retry() to retry it


def test_json_mode_is_opt_in(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    assert get_llm_instance().response_mime_type is None
    assert get_llm_instance(json_mode=True).response_mime_type == "application/json"


def test_retry_window_rides_out_short_demand_spikes():
    # 503 "high demand" errors are transient: retries should span about a minute
    retry = apply_retry(RunnableLambda(lambda x: x))
    params = retry.exponential_jitter_params
    waits = [min(params["initial"] * 2**k, params["max"]) for k in range(retry.max_attempt_number - 1)]
    assert 45 <= sum(waits) <= 120
