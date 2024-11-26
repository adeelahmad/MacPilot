# automation_framework/tests/core/metaclasses/test_actor_meta.py
# Revision No: 001
# Goals: Implement tests for the actor metaclass.
# Type of Code Response: Add new code

import pytest
from ....core.metaclasses.actor_meta import ActorStackMeta
from ....actors.base import ActorStack


def test_actor_stack_meta_registration():
    """Test that actor stacks are registered correctly."""

    class TestActor(ActorStack):
        name = "test"
        description = "Test Actor"
        capabilities = {}

        @classmethod
        def get_capabilities(cls):
            return cls.capabilities

        async def execute_action(self, action, **kwargs):
            return True

        def validate_state(self):
            return True

    registered_actors = ActorStackMeta.get_registered_actors()
    assert "TestActor" in registered_actors
    assert registered_actors["TestActor"] == TestActor


def test_missing_methods():
    """Test that an error is raised if required methods are missing."""

    with pytest.raises(TypeError):
        class BadActor(ActorStack):
            name = "bad"
            description = "Bad Actor"
            capabilities = {}

            @classmethod
            def get_capabilities(cls):
                return cls.capabilities

            def validate_state(self):
                return True

# Dependencies: pytest, ....core.metaclasses.actor_meta, ....actors.base
# Required Actions: None
# CLI Commands: Run with 'pytest'
# Is the script complete? Yes
# Is the code chunked version? No
# Is the code finished and commit-ready? Yes
# Are there any gaps that should be fixed in the next iteration? No
# Goals for the file in the following code block in case it's incomplete: N/A
