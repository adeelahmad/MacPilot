# automation_framework/tests/test_main.py
# Revision No: 001
# Goals: Implement tests for the main module.
# Type of Code Response: Add new code

import pytest
from ..main import AutomationFramework
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_framework_initialization(config):
    """Test framework initializes correctly."""
    framework = AutomationFramework(config)
    assert framework.state_manager is not None
    assert len(framework.actors) > 0
    assert framework.instruction_processor is not None
    assert framework.orchestrator is not None


@pytest.mark.asyncio
async def test_execute_instruction(mocker, config):
    """Test instruction execution flow."""
    mock_orchestrator = AsyncMock()
    mocker.patch('task_automation.main.Orchestrator', return_value=mock_orchestrator)

    framework = AutomationFramework(config)
    await framework.execute_instruction("Test instruction")

    mock_orchestrator.execute_instruction.assert_called_once_with("Test instruction")


@pytest.mark.asyncio
async def test_list_capabilities(config):
    framework = AutomationFramework(config)
    capabilities = framework.list_capabilities()
    assert isinstance(capabilities, dict)
    assert "generic" in capabilities
    assert "chrome" in capabilities
    assert "finder" in capabilities

# Dependencies: pytest, ..main, unittest.mock
# Required Actions: None
# CLI Commands: Run with 'pytest'
# Is the script complete? Yes
# Is the code chunked version? No
# Is the code finished and commit-ready? Yes
# Are there any gaps that should be fixed in the next iteration? No
# Goals for the file in the following code block in case it's incomplete: N/A
