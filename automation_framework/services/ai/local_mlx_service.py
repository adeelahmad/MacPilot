# File: automation_framework/services/ai/local_mlx_service.py

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Dict, List

try:  # Optional dependency – only needed for local models
    from mlx_lm import generate, load
    from mlx_lm.sample_utils import make_sampler
except ImportError:  # pragma: no cover - handled via runtime guard
    generate = load = None
    make_sampler = None
from pydantic import BaseModel, ValidationError

from core.config import AutomationConfig
from models.pydantic_models import (
    ActionStep,
    AnalysisResult,
    DynamicBaseModel,
    RecoveryStep,
    ValidationResult,
)
from .base import BaseLLMService, SYSTEM_PROMPT

TOOL_CALL_PATTERN = re.compile(r"<tool_call(?:\s+[^>]*)?>(.*?)</tool_call>", re.IGNORECASE | re.DOTALL)
THINK_PATTERN = re.compile(r"<think>(.*?)</think>", re.IGNORECASE | re.DOTALL)


class MLXLMService(BaseLLMService):
    """LLM backend that uses local MLX-LM models on Apple Silicon."""

    def __init__(self, config: AutomationConfig):
        super().__init__(config)
        self.model_id = config.mlx_model or "mlx-community/Meta-Llama-3-8B-Instruct-4bit"
        self.temperature = config.mlx_temperature
        self.max_new_tokens = config.mlx_max_output_tokens
        self.max_retries = config.max_retries
        self._model = None
        self._tokenizer = None

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    async def analyze_instruction(
        self,
        instruction: str,
        current_state: Any,
        available_actions: Dict[str, Any],
    ) -> AnalysisResult:
        prompt = self._create_analysis_prompt(instruction, current_state, available_actions)
        text = await self._run_completion(prompt)
        return self._parse_single_model(text, AnalysisResult, AnalysisResult(
            goal="Failed to analyze instruction",
            estimated_steps=0,
            required_actions=[],
            constraints=[],
            prerequisites=[],
        ))

    async def generate_action_plan(
        self,
        analysis: AnalysisResult,
        available_actions: Dict[str, Any],
    ) -> List[ActionStep]:
        prompt = self._create_plan_prompt(analysis, available_actions)
        text = await self._run_completion(prompt)
        return self._parse_steps(text, ActionStep)

    async def validate_results(
        self,
        original_instruction: str,
        action_plan: List[ActionStep],
        execution_results: List[Dict[str, Any]],
        current_state: Dict[str, Any],
    ) -> ValidationResult:
        prompt = self._create_validation_prompt(
            original_instruction,
            action_plan,
            execution_results,
            current_state,
        )
        text = await self._run_completion(prompt)
        return self._parse_single_model(
            text,
            ValidationResult,
            ValidationResult(
                success=False,
                goal_achieved=False,
                issues=["Failed to validate results"],
                recommendations=["Retry validation"],
            ),
        )

    async def generate_recovery_plan(
        self,
        step: ActionStep,
        failures: List[str],
        current_state: DynamicBaseModel,
    ) -> List[RecoveryStep]:
        prompt = self._create_recovery_prompt(step, failures, current_state)
        text = await self._run_completion(prompt)
        return self._parse_steps(text, RecoveryStep)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    async def _run_completion(self, prompt: str) -> str:
        """Execute generation on a worker thread to avoid blocking."""
        for attempt in range(1, self.max_retries + 1):
            try:
                return await asyncio.to_thread(self._generate_text, prompt)
            except Exception as exc:
                self.logger.warning(f"MLX generation attempt {attempt} failed: {exc}")
        raise RuntimeError("Exceeded local MLX retries")

    def _ensure_model(self):
        if self._model is None or self._tokenizer is None:
            if load is None:
                raise RuntimeError(
                    "mlx-lm is not installed. Install it with `pip install mlx-lm` to use the local provider."
                )
            self.logger.info(f"Loading MLX model '{self.model_id}'")
            self._model, self._tokenizer = load(self.model_id)

    def _generate_text(self, prompt: str) -> str:
        self._ensure_model()
        if generate is None or make_sampler is None:
            raise RuntimeError(
                "mlx-lm is not installed. Install it with `pip install mlx-lm` to use the local provider."
            )

        sampler = None
        if (self.temperature or 0) > 0:
            sampler = make_sampler(temp=self.temperature)

        result = generate(
            self._model,
            self._tokenizer,
            self._format_prompt(prompt),
            max_tokens=self.max_new_tokens,
            sampler=sampler,
        )
        if isinstance(result, str):
            return result
        if isinstance(result, dict):
            return result.get("text") or result.get("choices", [{}])[0].get("text", "")
        return str(result)

    def _format_prompt(self, user_prompt: str) -> str:
        """MLX-LM uses pure text, so stitch system and user prompts."""
        return f"{SYSTEM_PROMPT}\n\nUser Request:\n{user_prompt}\n\nReturn structured JSON only."

    def _extract_structured_json(self, raw: str) -> str:
        text = self._remove_think_tags(raw.strip())
        text = self._strip_code_fences(text)
        tool_payload = self._extract_tool_call_payload(text)
        if tool_payload:
            text = self._strip_code_fences(self._remove_think_tags(tool_payload))
        for open_char, close_char in [("{", "}"), ("[", "]")]:
            start = text.find(open_char)
            end = text.rfind(close_char)
            if 0 <= start < end:
                snippet = text[start : end + 1]
                try:
                    json.loads(snippet)
                    return snippet
                except json.JSONDecodeError:
                    continue
        return text

    def _extract_tool_call_payload(self, text: str) -> str | None:
        match = TOOL_CALL_PATTERN.search(text)
        if not match:
            return None
        content = match.group(1).strip()
        if not content:
            return None

        arguments_match = re.search(r"<arguments>(.*?)</arguments>", content, re.IGNORECASE | re.DOTALL)
        if arguments_match:
            content = arguments_match.group(1).strip()

        # Some models wrap JSON inside <tool_call_arguments> tags
        arguments_match = re.search(
            r"<tool_call_arguments>(.*?)</tool_call_arguments>", content, re.IGNORECASE | re.DOTALL
        )
        if arguments_match:
            content = arguments_match.group(1).strip()

        return content or None

    def _strip_code_fences(self, text: str) -> str:
        stripped = text.strip()
        if not stripped.startswith("```"):
            return stripped

        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        while lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()

    def _remove_think_tags(self, text: str) -> str:
        """Strip internal <think> blocks so they do not leak to parsing."""
        return THINK_PATTERN.sub("", text)

    def _parse_single_model(
        self,
        raw_text: str,
        model_cls: type[BaseModel],
        fallback: BaseModel,
    ) -> BaseModel:
        snippet = self._extract_structured_json(raw_text)
        try:
            data = json.loads(snippet)
            if model_cls is AnalysisResult:
                data = self._normalize_analysis_fields(data)
            return model_cls.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            self.logger.error(f"Failed to parse MLX output: {exc}")
            return fallback

    def _parse_steps(self, raw_text: str, model_cls: type[BaseModel]) -> List[Any]:
        snippet = self._extract_structured_json(raw_text)
        try:
            data = json.loads(snippet)
            if isinstance(data, dict):
                data = data.get("steps") or data.get("plan") or [data]
            return [model_cls.model_validate(item) for item in data]
        except (json.JSONDecodeError, ValidationError) as exc:
            self.logger.error(f"Failed to parse MLX step output: {exc}")
            return []

    def _normalize_analysis_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure AnalysisResult lists are represented as strings."""
        def _stringify(item: Any) -> str:
            if isinstance(item, str):
                return item
            return json.dumps(item, ensure_ascii=False)

        for key in ("required_actions", "constraints", "prerequisites"):
            if isinstance(data.get(key), list):
                data[key] = [_stringify(item) for item in data[key]]
        return data
