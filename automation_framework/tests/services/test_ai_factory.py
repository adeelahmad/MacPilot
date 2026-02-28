from automation_framework.core.config import AutomationConfig
from automation_framework.services.ai.factory import get_ai_service
from automation_framework.services.ai.local_mlx_service import MLXLMService
from automation_framework.services.ai.openai_service import OpenAIService


def test_factory_returns_openai():
    config = AutomationConfig(llm_provider="openai")
    assert isinstance(get_ai_service(config), OpenAIService)


def test_factory_returns_mlx():
    config = AutomationConfig(llm_provider="mlx", mlx_model="dummy")
    assert isinstance(get_ai_service(config), MLXLMService)
