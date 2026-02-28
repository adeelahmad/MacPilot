# File: automation_framework/services/ai/base.py

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from pydantic import BaseModel

from ...core.config import AutomationConfig
from ...models.pydantic_models import (
    ActionStep,
    AnalysisResult,
    DynamicBaseModel,
    RecoveryStep,
    ValidationResult,
)
from ..shared.serialization import DateTimeEncoder, recursive_dict_conversion

SYSTEM_PROMPT = """You are an advanced AI Agent Controller specializing in UI automation. Your role is to:
1. Analyze user instructions and break them down into concrete UI automation steps
2. Generate precise action sequences using available tools/actors
3. Handle UI state changes and validations
4. Provide recovery strategies when actions fail

Important Guidelines:
- Break complex tasks into atomic actions
- Use exact parameters required by each action
- Consider UI state changes between steps
- Plan for potential failures and edge cases
- Always verify action results

When generating plans, focus on:
1. Pre-conditions required for each step
2. Exact parameters needed for actions
3. Expected UI state changes
4. Verification steps
5. Potential error states and recovery paths"""


class BaseLLMService(ABC):
    """Abstract base class for all LLM backends."""

    def __init__(self, config: AutomationConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def analyze_instruction(
        self,
        instruction: str,
        current_state: Any,
        available_actions: Dict[str, Any],
    ) -> AnalysisResult:
        """Analyze a plain-language instruction."""

    @abstractmethod
    async def generate_action_plan(
        self,
        analysis: AnalysisResult,
        available_actions: Dict[str, Any],
    ) -> List[ActionStep]:
        """Translate analysis into executable steps."""

    @abstractmethod
    async def validate_results(
        self,
        original_instruction: str,
        action_plan: List[ActionStep],
        execution_results: List[Dict[str, Any]],
        current_state: Dict[str, Any],
    ) -> ValidationResult:
        """Validate execution output."""

    @abstractmethod
    async def generate_recovery_plan(
        self,
        step: ActionStep,
        failures: List[str],
        current_state: DynamicBaseModel,
    ) -> List[RecoveryStep]:
        """Generate recovery steps for a failed action."""

    # ---------------------------------------------------------------------- #
    # Shared prompt builders
    # ---------------------------------------------------------------------- #

    def _serialize_payload(self, payload: Any) -> str:
        """Safely serialize payloads that might include datetimes."""
        normalized = self._normalize_payload(payload)
        try:
            return json.dumps(normalized, cls=DateTimeEncoder, indent=2)
        except TypeError:
            return json.dumps(str(normalized))

    def _normalize_payload(self, payload: Any) -> Any:
        """Convert arbitrary objects into serializable dictionaries."""
        if payload is None:
            return {}

        if isinstance(payload, BaseModel):
            payload = payload.model_dump()
        elif hasattr(payload, "model_dump"):
            # Handles dynamically created models from create_model
            payload = payload.model_dump()
        elif hasattr(payload, "dict"):
            payload = payload.dict()
        elif isinstance(payload, dict):
            pass
        elif hasattr(payload, "__dict__"):
            payload = dict(payload.__dict__)

        return recursive_dict_conversion(payload)

    def _create_analysis_prompt(
        self,
        instruction: str,
        current_state: Any,
        available_actions: Dict[str, Any],
    ) -> str:
        """Build prompt for instruction analysis."""
        state_json = self._serialize_payload(current_state)
        actions_json = self._serialize_payload(available_actions)

        return f"""As an AI Agent Controller, analyze the following macOS automation instruction.

Instruction:
{instruction}

Current System/UI State Snapshot:
{state_json}

Available Actions:
{actions_json}

Produce a JSON object that matches the AnalysisResult schema with:
- goal
- required_actions
- constraints
- prerequisites
- estimated_steps

Ensure the plan reflects the current state, available actions, and includes any implicit prerequisites."""

    def _create_plan_prompt(
        self,
        analysis: AnalysisResult,
        available_actions: Dict[str, Any],
    ) -> str:
        """Build prompt for plan generation."""
        analysis_json = self._serialize_payload(analysis)
        actions_json = self._serialize_payload(available_actions)

        return f"""Using the analysis below, create a concrete automation action plan.

Analysis:
{analysis_json}

Available Actors/Actions:
{actions_json}

Respond with a JSON array of ActionStep objects. Each step must include:
1. step (integer)
2. actor (must exist in available actions)
3. action (must exist for the selected actor)
4. params (complete parameter dictionary)
5. expected_outcome (state validation hints when relevant)
6. fallback (optional fallback steps)

Make sure to include initialization steps (e.g., launching required apps) and validation after critical actions."""

    def _create_validation_prompt(
        self,
        original_instruction: str,
        action_plan: List[ActionStep],
        execution_results: List[Dict[str, Any]],
        current_state: Dict[str, Any],
    ) -> str:
        """Build prompt for validation."""
        plan_json = self._serialize_payload([step.model_dump() for step in action_plan])
        results_json = self._serialize_payload(execution_results)
        state_json = self._serialize_payload(current_state)

        return f"""Validate the execution of the automation instruction below.

Instruction:
{original_instruction}

Planned Steps:
{plan_json}

Execution Results:
{results_json}

Current State:
{state_json}

Return a ValidationResult JSON object that details:
- success (bool)
- goal_achieved (bool)
- issues (list of strings)
- recommendations (list of strings)

Call out incomplete goals, broken assumptions, or UI mismatches."""

    def _create_recovery_prompt(
        self,
        step: ActionStep,
        failures: List[str],
        current_state: DynamicBaseModel,
    ) -> str:
        """Build prompt for recovery planning."""
        step_json = self._serialize_payload(step)
        failures_json = self._serialize_payload(failures)
        state_json = self._serialize_payload(current_state)

        return f"""The following automation step failed. Devise a recovery plan.

Failed Step:
{step_json}

Failures:
{failures_json}

Current State:
{state_json}

Return a JSON array of RecoveryStep objects (same shape as ActionStep but for recovery) that brings the system back to a known good state, validates success, and resumes the original workflow."""
