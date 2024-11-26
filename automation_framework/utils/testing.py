# automation_framework/utils/testing.py
# Revision No: 001
# Goals: Implement testing utilities.
# Type of Code Response: Add new code


import asyncio
from typing import Any, Dict, Generator, AsyncGenerator, List
import pytest
from unittest.mock import MagicMock, AsyncMock
from ..core.config import AutomationConfig
from ..services.state.manager import UIElement


@pytest.fixture
def config() -> AutomationConfig:
    """Fixture providing test configuration."""
    return AutomationConfig(
        openai_api_key="test-key",
        max_retries=1,
        timeout=5,
        database_url="sqlite:///:memory:"
    )


@pytest.fixture
def mock_state() -> Dict[str, Any]:
    """Fixture providing mock UI state."""
    return {
        "active_window": "Test Window",
        "mouse_position": (100, 100),
        "screen_size": (1440, 900),
        "running_apps": [
            {"name": "Finder", "pid": 123},
            {"name": "Google Chrome", "pid": 456}
        ],
        "visible_elements": [
            {
                "text": "Test Button",
                "type": "button",
                "position": (200, 300),
                "size": (100, 30)
            }
        ]
    }


@pytest.fixture
def mock_openai() -> AsyncMock:
    """Fixture providing mock OpenAI client."""
    mock = AsyncMock()
    mock.ChatCompletion.acreate.return_value.choices = [
        MagicMock(message=MagicMock(content="Test response"))
    ]
    return mock


@pytest.fixture
async def mock_actor_stack() -> AsyncGenerator[AsyncMock, None]:
    """Fixture providing mock actor stack."""
    mock = AsyncMock()
    mock.get_capabilities.return_value = {
        "click": {
            "params": ["x", "y"],
            "description": "Click at coordinates"
        },
        "type_text": {
            "params": ["text"],
            "description": "Type text"
        }
    }
    mock.execute_action.return_value = True
    yield mock


class MockVisionProcessor:
    """Mock Vision framework processor for testing."""

    async def capture_screen(self) -> bytes:
        """Return mock screenshot data."""
        return b"mock_screenshot_data"

    async def detect_ui_elements(self, image: bytes) -> List[Dict[str, Any]]:
        """Return mock UI elements."""
        return [
            {
                "text": "Test Button",
                "bounds": {"x": 100, "y": 100, "width": 50, "height": 30},
                "type": "button"
            },
            {
                "text": "Test Link",
                "bounds": {"x": 200, "y": 200, "width": 100, "height": 20},
                "type": "link"
            }
        ]

    async def capture_window(self, window_id: int) -> Image.Image:
        return Image.new('RGB', (100, 100))


@pytest.fixture
def mock_vision() -> MockVisionProcessor:
    """Fixture providing mock Vision processor."""
    return MockVisionProcessor()


def async_return(result: Any) -> asyncio.Future:
    """Helper to create completed future with result."""
    future = asyncio.Future()
    future.set_result(result)
    return future


class MockExecutionEngine:
    """Mock execution engine for testing."""

    def __init__(self):
        self.executed_steps = []

    async def execute_plan(self, plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Record and return mock execution results."""
        self.executed_steps.extend(plan)
        return [
            {
                "step": step,
                "success": True,
                "result": {"status": "completed"}
            }
            for step in plan
        ]


@pytest.fixture
def mock_engine() -> MockExecutionEngine:
    """Fixture providing mock execution engine."""
    return MockExecutionEngine()


@pytest.fixture
def mock_ui_elements() -> List[UIElement]:
    return [
        UIElement("Button 1", 10, 10, 100, 50, "button", True, 0.9),
        UIElement("Link 1", 200, 50, 50, 20, "link", True, 0.8),
    ]

# Dependencies: asyncio, typing, pytest, unittest.mock, ..core.config, ..services.state.manager
# Required Actions: None
# CLI Commands: None
# Is the script complete? Yes
# Is the code chunked version? No
# Is the code finished and commit-ready? Yes
# Are there any gaps that should be fixed in the next iteration? No
# Goals for the file in the following code block in case it's incomplete: N/A
