import types

import pytest

from ...core.config import AutomationConfig
from ...models.pydantic_models import ActionStep, AnalysisResult, ValidationResult, RecoveryStep
from ...services.ai.openai_service import OpenAIService


class DummyCompletions:
    def __init__(self, response):
        self._response = response

    def create(self, **_: object):
        return self._response


def _set_response(service: OpenAIService, response):
    """Inject a dummy response into the OpenAIService client."""
    service.client = types.SimpleNamespace(
        chat=types.SimpleNamespace(completions=DummyCompletions(response))
    )


@pytest.fixture
def config():
    return AutomationConfig(
        openai_api_key="test-key",
        max_retries=1,
        timeout=5,
        database_url="sqlite:///:memory:",
    )


@pytest.fixture
def openai_service(config):
    return OpenAIService(config)


@pytest.mark.asyncio
async def test_analyze_instruction(openai_service):
    analysis = AnalysisResult(
        goal="Fetch news",
        required_actions=["chrome.open_url"],
        constraints=[],
        prerequisites=[],
        estimated_steps=3,
    )
    _set_response(openai_service, analysis)

    result = await openai_service.analyze_instruction(
        "Fetch latest news",
        {"active_window": "Chrome"},
        {"chrome": {"open_url": {}}},
    )

    assert isinstance(result, AnalysisResult)
    assert result.goal == "Fetch news"


@pytest.mark.asyncio
async def test_generate_action_plan(openai_service):
    plan = [
        ActionStep(step=1, actor="chrome", action="open_url", params={"url": "https://example.com"})
    ]
    _set_response(openai_service, plan)

    result = await openai_service.generate_action_plan(
        AnalysisResult(
            goal="Fetch news",
            required_actions=[],
            constraints=[],
            prerequisites=[],
            estimated_steps=1,
        ),
        {"chrome": {"open_url": {}}},
    )

    assert isinstance(result, list)
    assert isinstance(result[0], ActionStep)


@pytest.mark.asyncio
async def test_validate_results(openai_service):
    validation = ValidationResult(
        success=True,
        goal_achieved=True,
        issues=[],
        recommendations=[],
    )
    _set_response(openai_service, validation)

    result = await openai_service.validate_results(
        "Fetch news",
        [
            ActionStep(step=1, actor="chrome", action="open_url", params={"url": "https://example.com"})
        ],
        [{"success": True}],
        {"active_window": "Chrome"},
    )

    assert isinstance(result, ValidationResult)
    assert result.success is True


@pytest.mark.asyncio
async def test_generate_recovery_plan(openai_service):
    recovery = [RecoveryStep(step=1, action="retry", params={}, reason="Try again")]
    _set_response(openai_service, recovery)

    result = await openai_service.generate_recovery_plan(
        ActionStep(step=1, actor="chrome", action="open_url", params={"url": "https://example.com"}),
        ["timeout"],
        AnalysisResult(
            goal="Fetch news",
            required_actions=[],
            constraints=[],
            prerequisites=[],
            estimated_steps=1,
        ),
    )

    assert isinstance(result, list)
    assert isinstance(result[0], RecoveryStep)


def test_create_analysis_prompt(openai_service):
    prompt = openai_service._create_analysis_prompt(
        instruction="test",
        current_state={"active_window": "Chrome"},
        available_actions={"chrome": {"open_url": {}}},
    )
    assert isinstance(prompt, str)
    assert "test" in prompt


def test_create_plan_prompt(openai_service):
    prompt = openai_service._create_plan_prompt(
        analysis=AnalysisResult(
            goal="Test",
            required_actions=[],
            constraints=[],
            prerequisites=[],
            estimated_steps=1,
        ),
        available_actions={"chrome": {"open_url": {}}},
    )
    assert isinstance(prompt, str)
    assert "ActionStep" in prompt
