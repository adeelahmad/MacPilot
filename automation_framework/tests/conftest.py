import pytest
from .helpers.state_helpers import (
    create_mock_window_state,
    create_mock_ui_element,
    create_mock_application_state,
    create_mock_system_state,
    create_complete_mock_state
)
from ..core.config import AutomationConfig
from ..services.state.manager import StateManager
from ..services.validation.validator import StateValidator


@pytest.fixture
def mock_state():
    return create_complete_mock_state()


@pytest.fixture
def config():
    return AutomationConfig()


@pytest.fixture
def state_manager():
    return StateManager()


@pytest.fixture
def validator():
    return StateValidator()


@pytest.fixture
def mock_window():
    return create_mock_window_state()


@pytest.fixture
def mock_ui_element():
    return create_mock_ui_element()


@pytest.fixture
def mock_application():
    return create_mock_application_state()


@pytest.fixture
def mock_system():
    return create_mock_system_state()
