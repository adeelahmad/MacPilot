import pytest
from ...services.execution.engine import ExecutionEngine
from ...core.config import AutomationConfig
import asyncio


@pytest.fixture
def config():
    return AutomationConfig()


@pytest.fixture
def engine(config):
    return ExecutionEngine(config)


@pytest.mark.asyncio
async def test_execute_plan(engine):
    plan = [
        {
            'actor': 'generic',
            'action': 'click',
            'parameters': {'x': 100, 'y': 100}
        }
    ]

    results = await engine.execute_plan(plan)
    assert isinstance(results, list)
    assert len(results) == 1
    assert 'success' in results[0]


@pytest.mark.asyncio
async def test_actor_validation(engine):
    actor = await engine._get_actor('chrome')
    assert actor is not None
    assert await engine._validate_actor_requirements(actor)


@pytest.mark.asyncio
async def test_cleanup(engine):
    await engine.cleanup()
    assert len(engine.active_actors) == 0
