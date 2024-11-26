# automation_framework/core/metaclasses/actor_meta.py
# Revision No: 001
# Goals: Define metaclass for actor stacks.
# Type of Code Response: Add new code

from typing import Dict, Any, Type, ClassVar
from abc import ABCMeta


class ActorStackMeta(ABCMeta):
    """Metaclass for actor stacks that registers capabilities and validates methods."""

    _registry: ClassVar[Dict[str, Type['ActorStack']]] = {}

    def __new__(mcs, name, bases, namespace):
        # Create class
        cls = super().__new__(mcs, name, bases, namespace)

        # Don't register abstract base class
        if name == 'ActorStack':
            return cls

        # Register concrete actor stack
        mcs._registry[name] = cls

        # Validate required methods
        required_methods = {'get_capabilities', 'execute_action', 'validate_state'}
        missing = required_methods - set(namespace.keys())
        if missing:
            raise TypeError(f"Actor stack {name} missing required methods: {missing}")

        return cls

    @classmethod
    def get_registered_actors(mcs) -> Dict[str, Type['ActorStack']]:
        """Get all registered actor stacks."""
        return mcs._registry.copy()

# Dependencies: typing, abc
# Required Actions: None
# CLI Commands: None
# Is the script complete? Yes
# Is the code chunked version? No
# Is the code finished and commit-ready? Yes
# Are there any gaps that should be fixed in the next iteration? No
# Goals for the file in the following code block in case it's incomplete: N/A
