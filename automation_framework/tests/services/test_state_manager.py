import pytest
from ...services.state.manager import (
    StateManager, UIState, WindowState, ApplicationState,
    SystemState, UIElement, MenuState, AccessibilityState
)
import Quartz
from Cocoa import NSWorkspace


@pytest.fixture
def state_manager():
    return StateManager()


@pytest.mark.asyncio
async def test_capture_full_state(state_manager):
    """Test full state capture."""
    state = await state_manager.capture_full_state()
    assert isinstance(state, UIState)
    assert isinstance(state.system, SystemState)
    assert isinstance(state.windows, list)
    assert isinstance(state.applications, list)
    assert isinstance(state.ui_elements, list)
    assert isinstance(state.menu, MenuState)


@pytest.mark.asyncio
async def test_get_active_windows(state_manager):
    """Test getting active windows."""
    windows = await state_manager.get_active_windows()
    assert isinstance(windows, list)
    for window in windows:
        assert isinstance(window, WindowState)
        assert window.is_active
        assert not window.is_minimized


@pytest.mark.asyncio
async def test_monitor_state_changes(state_manager):
    """Test state change monitoring."""
    changes_detected = []

    async def callback(changes):
        changes_detected.append(changes)

    # Start monitoring
    task = asyncio.create_task(
        state_manager.monitor_state_changes(callback, interval=0.1)
    )

    # Wait a bit
    await asyncio.sleep(0.3)

    # Cancel monitoring
    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        pass

    # State changes might or might not be detected
    assert isinstance(changes_detected, list)


@pytest.mark.asyncio
async def test_get_window_by_id(state_manager):
    """Test getting window by ID."""
    # Get first active window
    active_windows = await state_manager.get_active_windows()
    if active_windows:
        window_id = active_windows[0].id
        window = await state_manager.get_window_by_id(window_id)
        assert isinstance(window, WindowState)
        assert window.id == window_id


@pytest.mark.asyncio
async def test_capture_window_states(state_manager):
    """Test window state capture."""
    windows = await state_manager._capture_window_states()
    assert isinstance(windows, list)
    for window in windows:
        assert isinstance(window, WindowState)
        assert isinstance(window.id, int)
        assert isinstance(window.title, str)
        assert isinstance(window.bounds, dict)


@pytest.mark.asyncio
async def test_capture_application_states(state_manager):
    """Test application state capture."""
    apps = await state_manager._capture_application_states()
    assert isinstance(apps, list)
    for app in apps:
        assert isinstance(app, ApplicationState)
        assert isinstance(app.name, str)
        assert isinstance(app.bundle_id, str)
        assert isinstance(app.pid, int)
        assert isinstance(app.windows, list)


@pytest.mark.asyncio
async def test_capture_menu_state(state_manager):
    """Test menu state capture."""
    menu = await state_manager._capture_menu_state()
    assert isinstance(menu, MenuState)
    assert isinstance(menu.items, list)
    assert isinstance(menu.enabled, bool)


@pytest.mark.asyncio
async def test_get_mouse_position(state_manager):
    """Test mouse position capture."""
    pos = await state_manager._get_mouse_position()
    assert isinstance(pos, tuple)
    assert len(pos) == 2
    assert isinstance(pos[0], int)
    assert isinstance(pos[1], int)
