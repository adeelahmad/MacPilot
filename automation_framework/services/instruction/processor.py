import asyncio
from typing import Dict, Any, List, Optional, cast
from core.config import AutomationConfig
from ..ai.openai_service import OpenAIService
from ..state.manager import StateManager, UIState
import json
import logging

logger = logging.getLogger(__name__)


class InstructionProcessor:
    """Processes natural language instructions into executable action plans."""

    def __init__(self, config: AutomationConfig):
        self.config = config
        self.openai = OpenAIService(config)
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
            analysis = await self.openai.analyze_instruction(
                instruction,
                current_state.__dict__,  # Pass state as dictionary
                available_actions
            )

            # Generate action plan
            action_plan = await self.openai.generate_action_plan(
                analysis,
                available_actions
            )

            return {
                "instruction": instruction,
                "analysis": analysis,
                "action_plan": json.loads(action_plan),  # Ensure action plan is a list
                "initial_state": current_state.__dict__
            }

        except Exception as e:
            logger.exception(f"Error processing instruction: {e}")
            return {}  # Return empty dict on error

    async def validate_execution(self,
                                 instruction: str,
                                 action_plan: List[Dict[str, Any]],
                                 execution_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate execution results and determine next steps.
        """
        try:
            current_state = await self.state_manager.capture_full_state()

            validation = await self.openai.validate_results(
                instruction,
                action_plan,
                execution_results,
                current_state.__dict__
            )

            return {
                "validation": validation,
                "final_state": current_state.__dict__
            }
        except Exception as e:
            logger.exception(f"Error validating execution: {e}")
            return {}  # Return empty dict on error
