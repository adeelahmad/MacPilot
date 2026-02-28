from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple


def create_mock_window_state() -> Dict[str, Any]:
    return {
        "id": 1,
        "title": "Test Window",
        "app": "TestApp",
        "bounds": {"x": 0, "y": 0, "width": 800, "height": 600},
        "is_active": True,
        "is_minimized": False,
        "alpha": 1.0,
        "layer": 0,
        "memory_usage": 0,
        "sharing_state": 0,
    }


def create_mock_ui_element() -> Dict[str, Any]:
    return {
        "id": "btn-1",
        "type": "button",
        "text": "Submit",
        "bounds": {"x": 100, "y": 100, "width": 80, "height": 24},
        "attributes": {"enabled": True},
        "confidence": 0.95,
        "clickable": True,
        "children": [],
    }


def create_mock_application_state() -> Dict[str, Any]:
    return {
        "name": "TestApp",
        "bundle_id": "com.example.test",
        "pid": 1234,
        "is_active": True,
        "windows": [create_mock_window_state()],
        "is_frontmost": True,
        "memory_usage": 256.0,
        "cpu_usage": 5.0,
    }


def create_mock_system_state() -> Dict[str, Any]:
    return {
        "cpu_percent": 12.5,
        "memory_used": 8.0,
        "active_displays": 1,
        "screen_resolution": (1440, 900),
        "cursor_location": (200, 150),
        "frontmost_app": "TestApp",
        "timestamp": datetime.now(),
        "battery_level": 0.78,
        "is_charging": True,
        "volume_level": 0.5,
        "brightness_level": 0.8,
    }


def create_complete_mock_state() -> Dict[str, Any]:
    return {
        "timestamp": datetime.now(),
        "system": create_mock_system_state(),
        "applications": [create_mock_application_state()],
        "windows": [create_mock_window_state()],
        "ui_elements": [create_mock_ui_element()],
        "menu": {"items": [], "active_menu": None, "enabled": True},
        "accessibility": None,
        "mouse_position": (200, 150),
        "keyboard_modifiers": ["command"],
        "active_window": "Test Window",
    }
