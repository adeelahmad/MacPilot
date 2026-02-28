from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

import instructor
from openai import OpenAI

from core.config import AutomationConfig
from models.pydantic_models import (
    ActionStep,
    AnalysisResult,
    DynamicBaseModel,
    RecoveryStep,
    ValidationResult,
)
from .base import BaseLLMService, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class OpenAIService(BaseLLMService):
    """LLM backend that proxies requests to the OpenAI-compatible API."""

    def __init__(self, config: AutomationConfig):
        super().__init__(config)
        base_url = getattr(config, "openai_base_url", None) or getattr(
            config, "BASE_URL", os.getenv("OPENAI_BASE_URL", "http://0.0.0.0:8080/v1")
        )
        api_key = config.openai_api_key or os.getenv("OPENAI_API_KEY", "sk-adminas123")
        try:
            self.client = instructor.from_openai(
                OpenAI(base_url=base_url, api_key=api_key),
                instructor.Mode.MD_JSON,
            )
        except Exception as exc:
            logger.error(f"Error initializing OpenAI client: {exc}")
            raise

    async def analyze_instruction(
        self,
        instruction: str,
        current_state: Any,
        available_actions: Dict[str, Any],
    ) -> AnalysisResult:
        """Analyzes a user instruction and generates an AnalysisResult."""
        try:
            prompt = self._create_analysis_prompt(instruction, current_state, available_actions)

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_retries=5,
                response_model=AnalysisResult,
            )
            return response
        except Exception as e:
            logger.exception(f"Error analyzing instruction: {e}")
            return AnalysisResult(
                goal="Error analyzing instruction",
                estimated_steps=0,
                required_actions=[
                    "chrome.open_url",
                    "chrome.type_text",
                    "chrome.click",
                ],
                constraints=["Handle browser state"],
                prerequisites=["Browser must be installed"],
            )

    async def generate_action_plan(
        self, analysis: AnalysisResult, available_actions: Dict[str, Any]
    ) -> List[ActionStep]:
        try:
            prompt = self._create_plan_prompt(analysis, available_actions)

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_retries=5,
                response_model=List[ActionStep],
            )
            return response
        except Exception as e:
            logger.exception(f"Error generating action plan: {e}")
            return []

    async def validate_results(
        self,
        original_instruction: str,
        action_plan: List[ActionStep],
        execution_results: List[Dict[str, Any]],
        current_state: Dict[str, Any],
    ) -> ValidationResult:
        """Validates execution results."""
        try:
            prompt = self._create_validation_prompt(
                original_instruction,
                action_plan,
                execution_results,
                current_state,
            )

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_retries=5,
                response_model=ValidationResult,
            )
            return response
        except Exception as e:
            logger.exception(f"Error validating results: {e}")
            return ValidationResult(
                success=False,
                goal_achieved=False,
                issues=["Error during validation"],
                recommendations=["Retry the operation"],
            )

    async def generate_recovery_plan(
        self, step: ActionStep, failures: List[str], current_state: DynamicBaseModel
    ) -> List[RecoveryStep]:
        """Generates recovery plan for failed actions."""
        try:
            prompt = self._create_recovery_prompt(step, failures, current_state)

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_retries=5,
                response_model=List[RecoveryStep],
            )
            return response
        except Exception as e:
            logger.exception(f"Error generating recovery plan: {e}")
            return []
