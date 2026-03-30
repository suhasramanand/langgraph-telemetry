from __future__ import annotations

from langchain_core.outputs import Generation, LLMResult
from prometheus_client import CollectorRegistry

from langgraph_telemetry.handler import TelemetryCallbackHandler
from langgraph_telemetry.types import TelemetryConfig


def test_on_llm_end_with_usage(registry: CollectorRegistry) -> None:
    cfg = TelemetryConfig(registry=registry, graph_name="g")
    h = TelemetryCallbackHandler(config=cfg)
    res = LLMResult(
        generations=[[Generation(text="hi")]],
        llm_output={"token_usage": {"prompt_tokens": 3, "completion_tokens": 5, "total_tokens": 8}},
    )
    h.on_llm_end(res)
    assert registry.get_sample_value("langgraph_llm_calls_total", {"graph": "g"}) == 1.0
    assert registry.get_sample_value("langgraph_llm_tokens_total", {"graph": "g", "token_type": "prompt"}) == 3.0
    assert registry.get_sample_value("langgraph_llm_tokens_total", {"graph": "g", "token_type": "completion"}) == 5.0
    assert registry.get_sample_value("langgraph_llm_tokens_total", {"graph": "g", "token_type": "total"}) == 8.0
    missing = registry.get_sample_value("langgraph_llm_usage_missing_total", {"graph": "g"})
    assert missing is None or missing == 0.0


def test_on_llm_end_missing_usage(registry: CollectorRegistry) -> None:
    cfg = TelemetryConfig(registry=registry, graph_name="g")
    h = TelemetryCallbackHandler(config=cfg)
    res = LLMResult(generations=[[Generation(text="x")]], llm_output={})
    h.on_llm_end(res)
    assert registry.get_sample_value("langgraph_llm_calls_total", {"graph": "g"}) == 1.0
    assert registry.get_sample_value("langgraph_llm_usage_missing_total", {"graph": "g"}) == 1.0
