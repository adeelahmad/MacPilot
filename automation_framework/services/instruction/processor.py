import asyncio
from typing import Dict, Any, List, Union
from core.config import AutomationConfig
from ..ai.factory import get_ai_service
from ..state.manager import StateManager, UIState
from models.pydantic_models import ActionStep
import logging

logger = logging.getLogger(__name__)


class InstructionProcessor:
    """Processes natural language instructions into executable action plans."""

    def __init__(self, config: AutomationConfig):
        self.config = config
        self.llm = get_ai_service(config)
        self.state_manager = StateManager()

    async def process_instruction(self, instruction: str) -> Dict[str, Any]:
        """
        Process an instruction and generate executable plan.
        """
        try:
            # Get current state
            current_state: UIState = await self.state_manager.capture_full_state()

            # Get available actions from registered actors
            from ...core.metaclasses.actor_meta import ActorStackMeta
            available_actions = {
                name: actor.get_capabilities()
                for name, actor in ActorStackMeta.get_registered_actors().items()
            }

            # Analyze instruction
            analysis = await self.llm.analyze_instruction(
                instruction,
                current_state.__dict__,  # Pass state as dictionary
                available_actions
            )

            # Generate action plan
            action_plan = await self.llm.generate_action_plan(
                analysis,
                available_actions
            )

            return {
                "instruction": instruction,
                "analysis": analysis.model_dump() if hasattr(analysis, "model_dump") else analysis,
                "action_plan": [
                    step.model_dump() if hasattr(step, "model_dump") else step
                    for step in action_plan
                ],
                "initial_state": current_state.__dict__
            }

        except Exception as e:
            logger.exception(f"Error processing instruction: {e}")
            return {}  # Return empty dict on error

    async def validate_execution(self,
                                 instruction: str,
                                 action_plan: List[Union[ActionStep, Dict[str, Any]]],
                                 execution_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate execution results and determine next steps.
        """
        try:
            current_state = await self.state_manager.capture_full_state()

            action_steps: List[ActionStep] = []
            for step in action_plan:
                if isinstance(step, ActionStep):
                    action_steps.append(step)
                elif isinstance(step, dict):
                    action_steps.append(ActionStep(**step))
                else:
                    raise TypeError(
                        f"Invalid action plan step type: {type(step)}"
                    )

            validation = await self.llm.validate_results(
                instruction,
                action_steps,
                execution_results,
                current_state.__dict__
            )

            return {
                "validation": validation.model_dump() if hasattr(validation, "model_dump") else validation,
                "final_state": current_state.__dict__
            }
        except Exception as e:
            logger.exception(f"Error validating execution: {e}")
            return {}  # Return empty dict on error
