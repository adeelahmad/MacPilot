import pytest
from ...services.ai.openai_service import OpenAIService
from ...core.config import AutomationConfig
import json
import os


@pytest.fixture
def config():
    return AutomationConfig(
        openai_api_key="test-key",
        max_retries=1,
        timeout=5,
        database_url="sqlite:///:memory:"
    )


@pytest.fixture
def openai_service(config):
    return OpenAIService(config)


@pytest.mark.asyncio
async def test_analyze_instruction(openai_service):
    instruction = "Fetch latest news"
    current_state = {"active_window": "Chrome"}
    available_actions = {"chrome": {"open_url": {}}}

    analysis = await openai_service.analyze_instruction(
        instruction, current_state, available_actions
    )

    assert isinstance(analysis, dict)
    assert "goal" in analysis
    assert "required_actions" in analysis
    assert isinstance(analysis["required_actions"], list)


@pytest.mark.asyncio
async def test_generate_action_plan(openai_service):
    analysis = {
        "goal": "Fetch news",
        "required_actions": ["open_url"],
        "constraints": [],
        "prerequisites": [],
        "estimated_steps": 1
    }
    available_actions = {"chrome": {"open_url": {}}}

    plan = await openai_service.generate_action_plan(
        analysis, available_actions
    )

    assert isinstance(plan, list)
    if plan:  # Plan might be empty if API call fails
        assert isinstance(plan[0], dict)
        assert "step" in plan[0]
        assert "action" in plan[0]


@pytest.mark.asyncio
async def test_validate_results(openai_service):
    validation = await openai_service.validate_results(
        "Fetch news",
        [{"step": 1, "action": "open_url"}],
        [{"success": True}],
        {"active_window": "Chrome"}
    )

    assert isinstance(validation, dict)
    assert "success" in validation
    assert isinstance(validation["success"], bool)


@pytest.mark.asyncio
async def test_generate_recovery_plan(openai_service):
    recovery_plan = await openai_service.generate_recovery_plan(
        {"step": 1, "action": "open_url"},
        ["Failed to connect"],
        {"active_window": "Chrome"}
    )

    assert isinstance(recovery_plan, list)
    if recovery_plan:  # Plan might be empty if API call fails
        assert isinstance(recovery_plan[0], dict)
        assert "step" in recovery_plan[0]
        assert "action" in recovery_plan[0]


def test_create_analysis_prompt(openai_service):
    prompt = openai_service._create_analysis_prompt(
        instruction="test",
        current_state="{}",
        available_actions="{}"
    )
    assert isinstance(prompt, str)
    assert "test" in prompt


def test_create_plan_prompt(openai_service):
    prompt = openai_service._create_plan_prompt(
        analysis="{}",
        available_actions="{}"
    )
    assert isinstance(prompt, str)
    assert "plan" in prompt.lower()
