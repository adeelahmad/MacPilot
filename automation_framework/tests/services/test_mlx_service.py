import pytest
from unittest.mock import AsyncMock

from automation_framework.core.config import AutomationConfig
from automation_framework.models.pydantic_models import ActionStep, AnalysisResult
from automation_framework.services.ai.local_mlx_service import MLXLMService


@pytest.fixture
def config():
    return AutomationConfig(
        llm_provider="mlx",
        max_retries=1,
        mlx_model="dummy",
    )


@pytest.mark.asyncio
async def test_mlx_analyze_instruction(monkeypatch, config):
    service = MLXLMService(config)
    monkeypatch.setattr(
        service,
        "_run_completion",
        AsyncMock(
            return_value='{"goal":"Test goal","required_actions":["chrome.open_url"],"constraints":[],"prerequisites":[],"estimated_steps":2}'
        ),
    )

    result = await service.analyze_instruction(
        "Test",
        {"active_window": "Chrome"},
        {"chrome": {"open_url": {}}},
    )

    assert result.goal == "Test goal"


@pytest.mark.asyncio
async def test_mlx_generate_action_plan(monkeypatch, config):
    service = MLXLMService(config)
    monkeypatch.setattr(
        service,
        "_run_completion",
        AsyncMock(
            return_value='Plan:\n[{"step":1,"actor":"chrome","action":"open_url","params":{"url":"https://example.com"}}]'
        ),
    )

    analysis = AnalysisResult(
        goal="Test",
        required_actions=[],
        constraints=[],
        prerequisites=[],
        estimated_steps=1,
    )

    plan = await service.generate_action_plan(analysis, {"chrome": {"open_url": {}}})

    assert isinstance(plan, list)
    assert plan and plan[0].actor == "chrome"


@pytest.mark.asyncio
async def test_mlx_validate_results(monkeypatch, config):
    service = MLXLMService(config)
    monkeypatch.setattr(
        service,
        "_run_completion",
        AsyncMock(
            return_value='{"success":true,"goal_achieved":true,"issues":[],"recommendations":[]}'
        ),
    )

    result = await service.validate_results(
        "Instruction",
        [],
        [],
        {},
    )

    assert result.success is True
    assert result.goal_achieved is True


@pytest.mark.asyncio
async def test_mlx_generate_recovery_plan(monkeypatch, config):
    service = MLXLMService(config)
    monkeypatch.setattr(
        service,
        "_run_completion",
        AsyncMock(
            return_value='{"steps":[{"step":1,"action":"retry","params":{}}]}'
        ),
    )

    steps = await service.generate_recovery_plan(
        ActionStep(step=1, actor="chrome", action="open_url", params={}),
        ["failure"],
        {},
    )

    assert steps and steps[0].action == "retry"


def test_mlx_extracts_tool_call_payload(config):
    service = MLXLMService(config)
    text = """
    <tool_call>
      <arguments>
        {"steps":[{"step":1,"actor":"chrome","action":"open_url"}]}
      </arguments>
    </tool_call>
    """

    snippet = service._extract_structured_json(text)
    assert "steps" in snippet


def test_mlx_strip_code_fences_and_think(config):
    service = MLXLMService(config)
    text = """
    ```
    <think>internal chain</think>
    {"success":true}
    ```
    """

    snippet = service._extract_structured_json(text)
    assert snippet == '{"success":true}'
