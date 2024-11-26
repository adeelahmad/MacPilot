import asyncio
from typing import Dict, Any, List, Optional, cast
import logging
from core.config import AutomationConfig
from services.state.manager import StateManager
from core.metaclasses.actor_meta import ActorStackMeta
from services.patterns.pattern_matcher import PatternMatcher
from services.patterns.interaction_patterns import PatternExecutor
import Quartz
from Cocoa import NSWorkspace

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """Native macOS execution engine."""

    def __init__(self, config: AutomationConfig):
        self.config = config
        self.state_manager = StateManager()
        self.pattern_matcher = PatternMatcher(self.state_manager)
        self.pattern_executor = PatternExecutor()
        self.workspace = NSWorkspace.sharedWorkspace()
        self.semaphore = asyncio.Semaphore(config.max_concurrent_actions)
        self.active_actors: Dict[str, Any] = {}

    async def execute_plan(self, action_plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute action plan with pattern matching and state validation."""
        results = []
        context = {'state_manager': self.state_manager}

        for step in action_plan:
            try:
                # Capture initial state
                initial_state = await self.state_manager.capture_full_state()
                context['initial_state'] = initial_state.__dict__

                # Try to match patterns first
                patterns = await self.pattern_matcher.match_patterns(
                    recursive_nsobject_to_python(initial_state.model_dump())
                )

                if patterns and patterns[0]['confidence'] > 0.8:
                    # Execute matched pattern
                    pattern = patterns[0]['pattern']
                    success = await self.pattern_executor.execute_pattern(pattern, context)
                    results.append({
                        'step': step,
                        'pattern_matched': pattern.type.value,
                        'success': success,
                        'error': None
                    })
                else:
                    # Execute individual action
                    result = await self._execute_step(step)
                    results.append(result)

                # Capture and validate final state
                final_state = await self.state_manager.capture_full_state()
                context[
                    "final_state"
                ] = recursive_nsobject_to_python(final_state.model_dump())

                if not self._validate_state_change(step, initial_state, final_state):
                    logger.warning(f"State validation failed for step: {step}")
                    results[-1]['state_valid'] = False
                else:
                    results[-1]['state_valid'] = True

            except Exception as e:
                logger.exception(f"Error executing step: {step}")
                results.append({
                    'step': step,
                    'success': False,
                    'error': str(e),
                    'state_valid': False
                })

                if not step.get('continue_on_error', False):
                    break

        return results

    async def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute single action step with native macOS support."""
        try:
            actor_name = step.get('actor', 'generic')
            action = step.get('action')
            params = step.get('parameters', {})

            # Get or create actor instance
            actor = await self._get_actor(actor_name)
            if not actor:
                raise ValueError(f"Actor '{actor_name}' not found or invalid")

            # Execute with semaphore
            async with self.semaphore:
                # Validate actor state
                if not actor.validate_state():
                    raise RuntimeError(f"Actor {actor_name} is not in a valid state")

                # Execute action
                result = await actor.execute_action(action, **params)

                return {
                    'step': step,
                    'success': True if result else False,
                    'result': result,
                    'error': None
                }

        except Exception as e:
            logger.exception(f"Error in _execute_step: {e}")
            return {
                'step': step,
                'success': False,
                'error': str(e),
                'result': None
            }

    async def _get_actor(self, actor_name: str) -> Optional[Any]:
        """Get or create actor instance with caching."""
        if actor_name not in self.active_actors:
            actor_class = ActorStackMeta.get_registered_actors().get(actor_name)
            if actor_class:
                try:
                    actor = actor_class()
                    if await self._validate_actor_requirements(actor):
                        self.active_actors[actor_name] = actor
                    else:
                        logger.error(f"Actor {actor_name} failed requirements validation")
                        return None
                except Exception as e:
                    logger.error(f"Error creating actor {actor_name}: {e}")
                    return None
            else:
                return None
        return self.active_actors.get(actor_name)

    async def _validate_actor_requirements(self, actor: Any) -> bool:
        """Validate actor system requirements."""
        try:
            # Check basic state
            if not actor.validate_state():
                return False

            # For Chrome actor
            if actor.name == 'chrome':
                chrome_bundle = self.workspace.URLForApplicationWithBundleIdentifier_(
                    'com.google.Chrome'
                )
                if not chrome_bundle:
                    return False

            # For Finder actor
            elif actor.name == 'finder':
                finder_bundle = self.workspace.URLForApplicationWithBundleIdentifier_(
                    'com.apple.finder'
                )
                if not finder_bundle:
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating actor requirements: {e}")
            return False

    def _validate_state_change(self, step: Dict[str, Any],
                               initial_state: Any, final_state: Any) -> bool:
        """Validate state changes after action execution."""
        try:
            expected_changes = step.get('expected_state_changes', {})

            for key, expected_value in expected_changes.items():
                if hasattr(final_state, key):
                    final_value = getattr(final_state, key)
                    initial_value = getattr(initial_state, key)

                    # Check if value changed as expected
                    if expected_value is not None:
                        if final_value != expected_value:
                            return False
                    elif final_value == initial_value:
                        return False

            return True

        except Exception as e:
            logger.error(f"Error validating state change: {e}")
            return False

    async def cleanup(self):
        """Cleanup active actors and resources."""
        for actor in self.active_actors.values():
            try:
                if hasattr(actor, 'cleanup'):
                    await actor.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up actor: {e}")

        self.active_actors.clear()
