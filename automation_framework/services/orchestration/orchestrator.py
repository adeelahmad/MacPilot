# File: automation_framework/services/orchestration/orchestrator.py

import asyncio
from typing import Dict, Any, Optional, List, Union
import logging
from rich.console import Console
from services.state.manager import WindowState, ApplicationState, UIElement, UIState
from core.context import AutomationContext
from services.ai.openai_service import OpenAIService as AIService
from services.validation.validator import StateValidator
from models.pydantic_models import ActionStep, AnalysisResult, DynamicBaseModel, ValidationResult
from pydantic import create_model
from ..shared.serialization import recursive_dict_conversion, DateTimeEncoder

logger = logging.getLogger(__name__)


class Orchestrator:
    """Orchestrates the automation workflow."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.ai = AIService(config)
        self.state_validator = StateValidator()
        self.available_actions = self._get_available_actions()
        self.encoder = DateTimeEncoder()

    async def _validate_step(self, step: ActionStep, context: AutomationContext) -> ValidationResult:
        """Validate step execution results."""
        try:
            # Get current state
            current_state = await self.config['state_manager'].capture_full_state()
            current_state_dict = recursive_dict_conversion(current_state)

            # Get expected state
            expected_state = recursive_dict_conversion(step.expected_outcome) if step.expected_outcome else {}

            # Let the actor validate its own state
            actor = self._get_actor(step.actor)
            if not actor:
                return ValidationResult(
                    success=False,
                    failures=[f"Unknown actor: {step.actor}"],
                    warnings=[]
                )

            return await actor.validate_state(current_state_dict, expected_state)

        except Exception as e:
            logger.error(f"Validation error: {e}")
            return ValidationResult(
                success=False,
                failures=[f"Validation error: {str(e)}"],
                warnings=[]
            )

    async def _execute_plan(self, plan: List[ActionStep], context: AutomationContext) -> bool:
        """Execute the generated action plan."""
        for i, step in enumerate(plan):
            try:
                self.logger.debug(f"Executing step {i + 1}: {step.action} {step.params}")

                # Capture and convert current state
                current_state = await self.config['state_manager'].capture_full_state()
                current_state_dict = recursive_dict_conversion(current_state)

                # Execute action
                actor = self._get_actor(step.actor)
                if not actor:
                    raise ValueError(f"Unknown actor: {step.actor}")

                await context.set_actor(step.actor)
                success = await actor.execute_action(step.action, **step.params)

                if not success:
                    raise RuntimeError(f"Action {step.action} failed")

                # Store state safely
                await context.push_state(current_state_dict)

                # Validate with proper state handling
                if step.expected_outcome:
                    validation = await self._validate_step(step, context)
                    if not validation.success:
                        logger.warning(f"Validation failed for step {i + 1}")
                        if not await self._handle_validation_failure(validation, step, context):
                            return False

                # Add delay between steps
                await asyncio.sleep(1)

            except Exception as e:
                self.logger.error(f"Error executing step {i + 1}: {e}")
                return False

        return True

    async def _validate_stepx(self, step: ActionStep, context: AutomationContext) -> ValidationResult:
        """Validate step execution results with proper state handling."""
        try:
            # Capture current state and convert to dictionary
            current_state = await self.config['state_manager'].capture_full_state()
            current_dict = recursive_dict_conversion(current_state)

            # Convert expected outcome to dictionary if present
            expected_dict = recursive_dict_conversion(step.expected_outcome) if step.expected_outcome else {}

            # Basic validation checks
            validation_result = ValidationResult(
                success=True,
                failures=[],
                warnings=[]
            )

            # Check for required state fields
            if expected_dict.get('application'):
                apps = current_dict.get('applications', [])
                if not any(app.get('name') == expected_dict['application'] for app in apps):
                    validation_result.success = False
                    validation_result.failures.append(f"Application {expected_dict['application']} not found")

            # Check browser state if relevant
            if step.actor == 'chrome':
                browser_active = any(
                    app.get('name') == 'Google Chrome' and app.get('is_active')
                    for app in current_dict.get('applications', [])
                )
                if not browser_active:
                    validation_result.warnings.append("Chrome browser not active")

            return validation_result

        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return ValidationResult(
                success=False,
                failures=[f"Validation error: {str(e)}"],
                warnings=[]
            )

    async def _handle_validation_failure(self, validation: ValidationResult, step: ActionStep,
                                         context: AutomationContext) -> bool:
        """Handle validation failure with recovery."""
        self.logger.warning(
            f"Validation failed:\nFailures: {validation.failures}\nWarnings: {validation.warnings}"
        )

        try:
            # Get current state for recovery
            current_state = await self.config['state_manager'].capture_full_state()
            state_dict = recursive_dict_conversion(current_state)

            # Create dynamic model for current state
            DynamicModel = self._create_dynamic_model(state_dict)
            current_state_model = DynamicModel(**state_dict)

            # Generate recovery plan
            recovery_plan = await self.ai.generate_recovery_plan(
                step,
                validation.failures,
                current_state_model
            )

            if recovery_plan:
                self.logger.info("Attempting recovery")
                return await self._execute_plan(recovery_plan, context)

            return False

        except Exception as e:
            self.logger.error(f"Recovery handling error: {e}")
            return False
    async def execute_instruction(self, instruction: str, context: Optional[AutomationContext] = None) -> bool:
        """Execute automation instruction."""
        context = context or AutomationContext(
            instruction=instruction,
            state_manager=self.config['state_manager']
        )
        try:
            # 1. Capture current state
            current_state: UIState = await self.config['state_manager'].capture_full_state()

            # 2. Convert state to dictionary format safely
            state_dict = recursive_dict_conversion(current_state)

            # 3. Create dynamic model
            DynamicModel = self._create_dynamic_model(state_dict)
            current_state_model = DynamicModel(**state_dict)

            # 4. Analyze instruction
            analysis: AnalysisResult = await self.ai.analyze_instruction(
                instruction,
                current_state_model,
                self.available_actions
            )

            if not analysis:
                logger.error("Failed to analyze instruction")
                return False

            # 5. Generate action plan
            plan: List[ActionStep] = await self.ai.generate_action_plan(
                analysis,
                self.available_actions
            )

            if not plan:
                logger.error("Failed to generate action plan")
                return False

            # 6. Execute plan
            success = await self._execute_plan(plan, context)

            if success:
                self.logger.info(
                    f"Instruction '{instruction}' completed successfully in {await context.get_execution_time():.2f}s")
            else:
                self.logger.error(f"Instruction '{instruction}' failed after {await context.get_execution_time():.2f}s")

            return success

        except Exception as e:
            self.logger.exception(f"Error executing instruction: {e}")
            return False

    def _create_dynamic_model(self, state: Dict[str, Any]):
        """
        Create a Pydantic-compatible dynamic model based on the provided state dictionary.
        """
        fields = {}

        # Generate fields dynamically
        for field_name, field_value in state.items():
            field_type = self._infer_field_type(field_value)
            fields[field_name] = (field_type, ...)  # Required field by default

        # Return a dynamically created Pydantic model
        return create_model("DynamicStateModel", **fields, __base__=DynamicBaseModel)

    def _infer_field_type(self, value: Any) -> Any:
        """
        Infer the field type dynamically based on the value's type.
        """
        if isinstance(value, list):
            if value:
                element_type = self._infer_field_type(value[0])
                return List[element_type]
            return List[Any]  # Empty list fallback
        elif isinstance(value, dict):
            return Dict[str, Any]
        elif isinstance(value, str):
            return str
        elif isinstance(value, int):
            return int
        elif isinstance(value, float):
            return float
        elif isinstance(value, bool):
            return bool
        elif value is None:
            return Optional[Any]
        else:
            return type(value)  # Fallback for custom types



    def _get_available_actions(self) -> Dict[str, Any]:
        """Get available actions from registered actors."""
        actions = {}
        for actor_name, actor in self.config['actors'].items():
            actions[actor_name] = actor.get_capabilities()
        return actions

    def _get_actor(self, actor_type: str):
        """Get actor for given type."""
        return self.config['actors'].get(actor_type)
