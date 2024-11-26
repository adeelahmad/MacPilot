# automation_framework/core/context.py
# Revision No: 001
# Goals: Define AutomationContext for managing automation state.
# Type of Code Response: Add new code

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class AutomationContext:
    """Manages context for automation tasks."""

    instruction: str
    state_manager: Any  # Generic type for state manager
    start_time: datetime = field(default_factory=datetime.now)
    variables: Dict[str, Any] = field(default_factory=dict)
    history: list[Dict[str, Any]] = field(default_factory=list)
    current_actor: Optional[str] = None

    def __post_init__(self):
        self.logger = logging.getLogger(__name__)
        self._lock = asyncio.Lock()

    async def set_variable(self, name: str, value: Any):
        """Set context variable."""
        async with self._lock:
            self.variables[name] = value
            self._log_event('set_variable', {'name': name, 'value': value})

    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get context variable."""
        return self.variables.get(name, default)

    async def push_state(self, state: Dict[str, Any]):
        """Save current state to history."""
        async with self._lock:
            self.history.append({
                'timestamp': datetime.now(),
                'state': state
            })
            self._log_event('push_state', {'state_id': len(self.history)})

    def get_last_state(self) -> Optional[Dict[str, Any]]:
        """Get most recent state from history."""
        if self.history:
            return self.history[-1]['state']
        return None

    async def set_actor(self, actor_name: str):
        """Set current actor."""
        async with self._lock:
            self.current_actor = actor_name
            self._log_event('set_actor', {'actor': actor_name})

    def _log_event(self, event_type: str, details: Dict[str, Any]):
        """Log automation event."""
        self.logger.debug(
            f"Automation event: {event_type}\n"
            f"Details: {details}\n"
            f"Current actor: {self.current_actor}"
        )

    async def get_execution_time(self) -> float:
        """Get total execution time in seconds."""
        return (datetime.now() - self.start_time).total_seconds()

    def summarize(self) -> Dict[str, Any]:
        """Summarize context state."""
        return {
            'instruction': self.instruction,
            'execution_time': (datetime.now() - self.start_time).total_seconds(),
            'steps_completed': len(self.history),
            'current_actor': self.current_actor,
            'variables': self.variables
        }

# Dependencies: typing, dataclasses, datetime, asyncio, logging
# Required Actions: None
# CLI Commands: None
# Is the script complete? Yes
# Is the code chunked version? No
# Is the code finished and commit-ready? Yes
# Are there any gaps that should be fixed in the next iteration? No
# Goals for the file in the following code block in case it's incomplete: N/A
