# File: automation_framework/services/ai/factory.py

from __future__ import annotations

from core.config import AutomationConfig
from .openai_service import OpenAIService


def get_ai_service(config: AutomationConfig):
    """Return the configured LLM backend."""
    provider = (config.llm_provider or "openai").lower()
    if provider in {"mlx", "mlx-lm", "local", "local-mlx"}:
        try:
            from .local_mlx_service import MLXLMService
        except ImportError as exc:  # pragma: no cover - import guard
            raise RuntimeError(
                "mlx-lm is not installed. Install it or switch llm_provider back to 'openai'."
            ) from exc
        return MLXLMService(config)

    return OpenAIService(config)

