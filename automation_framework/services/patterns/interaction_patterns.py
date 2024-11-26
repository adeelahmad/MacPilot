# File Path: automation_framework/services/patterns/interaction_patterns.py
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging


class PatternType(Enum):
    CLICK_AND_WAIT = "click_and_wait"
    FILL_AND_SUBMIT = "fill_and_submit"
    SCROLL_TO_FIND = "scroll_to_find"
    DRAG_AND_DROP = "drag_and_drop"
    MODAL_DIALOG = "modal_dialog"
    DROPDOWN_SELECT = "dropdown_select"


@dataclass
class InteractionPattern:
    """Represents a UI interaction pattern."""
    type: PatternType
    steps: List[Dict[str, Any]]
    success_criteria: Dict[str, Any]
    timeout: float = 30.0
    retry_count: int = 3


class PatternExecutor:
    """Executes UI interaction patterns."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.active_patterns: Dict[str, InteractionPattern] = {}

    async def execute_pattern(self, pattern: InteractionPattern,
                              context: Dict[str, Any]) -> bool:
        """Execute an interaction pattern."""
        pattern_id = f"{pattern.type.value}_{id(pattern)}"
        self.active_patterns[pattern_id] = pattern

        try:
            for attempt in range(pattern.retry_count):
                try:
                    result = await self._execute_steps(pattern.steps, context)
                    if await self._verify_success(pattern.success_criteria, context):
                        return True

                    self.logger.warning(
                        f"Pattern {pattern_id} success criteria not met, "
                        f"attempt {attempt + 1}/{pattern.retry_count}"
                    )
                except Exception as e:
                    self.logger.error(
                        f"Error executing pattern {pattern_id}: {str(e)}"
                    )

                if attempt < pattern.retry_count - 1:
                    await asyncio.sleep(1 * (attempt + 1))

            return False

        finally:
            del self.active_patterns[pattern_id]

    async def _execute_steps(self, steps: List[Dict[str, Any]],
                             context: Dict[str, Any]) -> bool:
        """Execute pattern steps."""
        for step in steps:
            action = step["action"]
            params = step.get("params", {})

            # Substitute context variables in params
            params = self._substitute_variables(params, context)

            # Execute action with retry
            success = False
            for attempt in range(3):
                try:
                    if await self._execute_action(action, params, context):
                        success = True
                        break
                except Exception as e:
                    self.logger.warning(
                        f"Step failed, attempt {attempt + 1}/3: {str(e)}"
                    )
                    await asyncio.sleep(1)

            if not success:
                return False

            # Update context with results if specified
            if "store_result" in step:
                context[step["store_result"]] = True

        return True

    def _substitute_variables(self, params: Dict[str, Any],
                              context: Dict[str, Any]) -> Dict[str, Any]:
        """Substitute context variables in parameters."""
        result = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("$"):
                var_name = value[1:]
                if var_name not in context:
                    raise ValueError(f"Context variable not found: {var_name}")
                result[key] = context[var_name]
            else:
                result[key] = value
        return result

    async def _execute_action(self, action: str, params: Dict[str, Any],
                              context: Dict[str, Any]) -> bool:
        """Execute a single action."""
        actor = context.get("actor")
        if not actor:
            raise ValueError("No actor found in context")

        return await actor.execute_action(action, **params)

    async def _verify_success(self, criteria: Dict[str, Any],
                              context: Dict[str, Any]) -> bool:
        """Verify pattern success criteria."""
        if "element_visible" in criteria:
            element = await self._find_element(
                criteria["element_visible"],
                context
            )
            if not element:
                return False

        if "element_clickable" in criteria:
            element = await self._find_element(
                criteria["element_clickable"],
                context
            )
            if not element or not element.get("clickable"):
                return False

        if "text_present" in criteria:
            if not await self._find_text(criteria["text_present"], context):
                return False

        if "state_changed" in criteria:
            return await self._verify_state_change(
                criteria["state_changed"],
                context
            )

        return True

    async def _find_element(self, criteria: Dict[str, Any],
                            context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find UI element matching criteria."""
        state_manager = context.get("state_manager")
        if not state_manager:
            raise ValueError("No state manager found in context")

        current_state = await state_manager.capture_full_state()

        for element in current_state.ui_elements:
            if all(
                getattr(element, key) == value
                for key, value in criteria.items()
            ):
                return element.__dict__

        return None

    async def _find_text(self, text: str, context: Dict[str, Any]) -> bool:
        """Find text in current state."""
        state_manager = context.get("state_manager")
        if not state_manager:
            raise ValueError("No state manager found in context")

        current_state = await state_manager.capture_full_state()

        for element in current_state.ui_elements:
            if element.text and text in element.text:
                return True

        return False

    async def _verify_state_change(self, expected_changes: Dict[str, Any],
                                   context: Dict[str, Any]) -> bool:
        """Verify state changes."""
        state_manager = context.get("state_manager")
        if not state_manager:
            raise ValueError("No state manager found in context")

        current_state = await state_manager.capture_full_state()
        previous_state = context.get("previous_state")

        if not previous_state:
            return False

        for path, expected_value in expected_changes.items():
            current_value = self._get_nested_value(
                current_state.__dict__,
                path.split(".")
            )
            previous_value = self._get_nested_value(
                previous_state.__dict__,
                path.split(".")
            )

            if current_value == previous_value:
                return False

            if expected_value is not None and current_value != expected_value:
                return False

        return True

    def _get_nested_value(self, obj: Any, path: List[str]) -> Any:
        """Get nested dictionary value using path."""
        for key in path:
            if isinstance(obj, dict):
                if key not in obj:
                    return None
                obj = obj[key]
            else:
                if not hasattr(obj, key):
                    return None
                obj = getattr(obj, key)
        return obj


class PatternLibrary:
    """Library of common UI interaction patterns."""

    @staticmethod
    def click_and_wait(element_criteria: Dict[str, Any],
                       wait_criteria: Dict[str, Any]) -> InteractionPattern:
        """Create click and wait pattern."""
        return InteractionPattern(
            type=PatternType.CLICK_AND_WAIT,
            steps=[
                {
                    "action": "click",
                    "params": {
                        "element": element_criteria
                    }
                }
            ],
            success_criteria=wait_criteria
        )

    @staticmethod
    def fill_and_submit(form_criteria: Dict[str, Any],
                        field_values: Dict[str, str],
                        submit_criteria: Dict[str, Any]) -> InteractionPattern:
        """Create form fill and submit pattern."""
        steps = []

        for field, value in field_values.items():
            steps.append({
                "action": "type_text",
                "params": {
                    "element": {"name": field},
                    "text": value
                }
            })

        steps.append({
            "action": "click",
            "params": {
                "element": submit_criteria
            }
        })

        return InteractionPattern(
            type=PatternType.FILL_AND_SUBMIT,
            steps=steps,
            success_criteria={
                "element_visible": {"type": "success_message"}
            }
        )

    @staticmethod
    def scroll_to_find(scroll_container: Dict[str, Any],
                       target_criteria: Dict[str, Any]) -> InteractionPattern:
        """Create scroll to find pattern."""
        return InteractionPattern(
            type=PatternType.SCROLL_TO_FIND,
            steps=[
                {
                    "action": "scroll",
                    "params": {
                        "element": scroll_container,
                        "direction": "down",
                        "amount": 100
                    },
                    "repeat_until": {
                        "element_visible": target_criteria
                    }
                }
            ],
            success_criteria={
                "element_visible": target_criteria,
                "element_clickable": target_criteria
            }
        )

    @staticmethod
    def drag_and_drop(source_criteria: Dict[str, Any],
                      target_criteria: Dict[str, Any]) -> InteractionPattern:
        """Create drag and drop pattern."""
        return InteractionPattern(
            type=PatternType.DRAG_AND_DROP,
            steps=[
                {
                    "action": "drag",
                    "params": {
                        "source": source_criteria,
                        "target": target_criteria
                    }
                }
            ],
            success_criteria={
                "state_changed": {
                    f"elements[?(@.id=='{source_criteria.get('id')}')].position": None
                }
            }
        )

    @staticmethod
    def handle_modal(trigger_criteria: Dict[str, Any],
                     modal_criteria: Dict[str, Any],
                     action_criteria: Dict[str, Any]) -> InteractionPattern:
        """Create modal dialog pattern."""
        return InteractionPattern(
            type=PatternType.MODAL_DIALOG,
            steps=[
                {
                    "action": "click",
                    "params": {
                        "element": trigger_criteria
                    }
                },
                {
                    "action": "wait",
                    "params": {
                        "condition": {
                            "element_visible": modal_criteria
                        }
                    }
                },
                {
                    "action": "click",
                    "params": {
                        "element": action_criteria
                    }
                }
            ],
            success_criteria={
                "element_visible": {"type": "success_message"}
            }
        )
