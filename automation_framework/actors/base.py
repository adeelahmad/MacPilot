from abc import ABC
from typing import Dict, Any, ClassVar
from core.metaclasses.actor_meta import ActorStackMeta


class ActorStack(ABC, metaclass=ActorStackMeta):
    """Base class for all actor stacks."""

    # Class variables
    name: ClassVar[str]
    description: ClassVar[str]
    capabilities: ClassVar[Dict[str, Any]]

    @classmethod
    def get_capabilities(cls) -> Dict[str, Any]:
        """Get actor stack capabilities."""
        raise NotImplementedError

    def execute_action(self, action: str, **kwargs) -> bool:
        """Execute an action with given parameters."""
        raise NotImplementedError

    def validate_state(self) -> bool:
        """Validate actor stack is in valid state."""
        raise NotImplementedError
