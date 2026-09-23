"""Tests for LLM token/latency tracking and performance logs."""



from __future__ import annotations



from datetime import datetime, timezone

from unittest.mock import MagicMock, patch



from src.agents.llm_client import LLMClient

from src.agents.llm_observability import parse_ollama_usage, parse_openai_usage

from src.common.models import (

    AgentTrace,

    LLMCallMetrics,

    PhaseTiming,

    RunStatus,

    RunSummary,

    TestReport,

)

from src.reporting.detailed_log import render_detailed_log

from src.reporting.performance_summary import render_performance_summary





def test_parse_openai_usage():

    body = {"usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}}

    assert parse_openai_usage(body) == (10, 20, 30)





def test_parse_ollama_usage():

    body = {"prompt_eval_count": 5, "eval_count": 7}

    assert parse_ollama_usage(body) == (5, 7, 12)





@patch("src.agents.llm_client.settings")

@patch("httpx.post")

def test_llm_client_records_tokens(mock_post, mock_settings):

    mock_settings.groq_api_key = "test-key"

    mock_settings.llm_provider = "groq"

    mock_settings.langsmith_tracing_enabled = False

    mock_settings.langsmith_api_key = None



    mock_resp = MagicMock()

    mock_resp.json.return_value = {

        "choices": [{"message": {"content": "hello"}}],

        "usage": {"prompt_tokens": 11, "completion_tokens": 4, "total_tokens": 15},

    }

    mock_post.return_value = mock_resp



    client = LLMClient(provider="groq", model="test-model")

    assert client.is_available()

    out = client.chat("sys", "user", caller="planner")

    assert out == "hello"

    assert len(client.call_log) == 1

    record = client.call_log[0]

    assert record.caller == "planner"

    assert record.prompt_tokens == 11

    assert record.completion_tokens == 4

    assert record.total_tokens == 15

    assert record.latency_ms >= 0





def test_detailed_log_includes_performance_and_llm_sections():

    report = TestReport(

        run_id="run-perf-001",

        suite_id="T1",

        status=RunStatus.PASSED,

        started_at=datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc),

        finished_at=datetime(2026, 9, 1, 10, 0, 30, tzinfo=timezone.utc),

        duration_ms=30000,

        summary=RunSummary(total=1, passed=1, failed=0, skipped=0),

        steps=[],

        agent_traces=[

            AgentTrace(

                agent="step_agent",

                phase="planner",

                detail="planned steps",

                duration_ms=1200,

                tokens_prompt=100,

                tokens_completion=50,

            )

        ],

        llm_calls=[

            LLMCallMetrics(

                caller="planner",

                provider="groq",

                model="test",

                prompt_tokens=100,

                completion_tokens=50,

                total_tokens=150,

                latency_ms=900,

            )

        ],

        phase_timings=[

            PhaseTiming(phase="step_agent", duration_ms=5000),

            PhaseTiming(phase="execute", duration_ms=20000),

        ],

    )

    text = render_detailed_log(report)

    assert "Performance Breakdown" in text

    assert "LLM Token Usage" in text

    assert "planner" in text

    assert "Slowest phase" in text



    perf = render_performance_summary(report)

    assert any("execute" in line for line in perf)


