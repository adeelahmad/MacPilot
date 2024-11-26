# File: automation_framework/actors/generic/mouse_keyboard.py

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple, ClassVar
import Quartz
from Cocoa import (
    NSEvent, NSWorkspace, NSScreen, NSApplication,
    NSApplicationActivateIgnoringOtherApps
)
import AppKit
from ..base import ActorStack
from models.pydantic_models import ValidationResult

logger = logging.getLogger(__name__)


class GenericActorStack(ActorStack):
    """Native macOS mouse and keyboard control."""

    name: ClassVar[str] = "generic"
    description: ClassVar[str] = "Native macOS mouse/keyboard control"

    capabilities: ClassVar[Dict[str, Any]] = {
        'click': {
            'params': ['x', 'y'],
            'description': 'Click at coordinates using native events'
        },
        'double_click': {
            'params': ['x', 'y'],
            'description': 'Double click using native events'
        },
        'right_click': {
            'params': ['x', 'y'],
            'description': 'Right click using native events'
        },
        'move_mouse': {
            'params': ['x', 'y'],
            'description': 'Move mouse using native events'
        },
        'drag_mouse': {
            'params': ['start_x', 'start_y', 'end_x', 'end_y'],
            'description': 'Drag mouse using native events'
        },
        'type_text': {
            'params': ['text'],
            'description': 'Type text using native events'
        },
        'press_key': {
            'params': ['key_code', 'modifiers'],
            'description': 'Press key with modifiers using native events'
        },
        'get_mouse_position': {
            'params': [],
            'description': 'Get current mouse position'
        },
        'open_application': {
            'params': ['name'],
            'description': 'Open an application by name'
        },
        'switch_application': {
            'params': ['name'],
            'description': 'Switch to an open application by name'
        },
        'find_window': {
            'params': ['name'],
            'description': 'Find a window by name'
        }
    }

    def __init__(self):
        self._event_source = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateHIDSystemState)
        self.workspace = NSWorkspace.sharedWorkspace()

    @classmethod
    def get_capabilities(cls) -> Dict[str, Any]:
        return cls.capabilities

    async def execute_action(self, action: str, **kwargs) -> Any:
        """Execute the requested action with given parameters."""
        try:
            actions = {
                'click': lambda: self._click(kwargs['x'], kwargs['y']),
                'double_click': lambda: self._double_click(kwargs['x'], kwargs['y']),
                'right_click': lambda: self._right_click(kwargs['x'], kwargs['y']),
                'move_mouse': lambda: self._move_mouse(kwargs['x'], kwargs['y']),
                'drag_mouse': lambda: self._drag_mouse(
                    kwargs['start_x'], kwargs['start_y'],
                    kwargs['end_x'], kwargs['end_y']
                ),
                'type_text': lambda: self._type_text(kwargs['text']),
                'press_key': lambda: self._press_key(
                    kwargs['key_code'],
                    kwargs.get('modifiers', [])
                ),
                'get_mouse_position': self._get_mouse_position,
                'open_application': lambda: self._open_application(kwargs['name']),
                'switch_application': lambda: self._switch_application(kwargs['name']),
                'find_window': lambda: self._find_window(kwargs['name'])
            }

            if action not in actions:
                raise ValueError(f"Unknown action: {action}")

            return await actions[action]()

        except Exception as e:
            logger.error(f"Error executing action {action}: {e}")
            return False

    async def validate_state(self, current_state: Dict[str, Any], expected_state: Dict[str, Any]) -> ValidationResult:
        """Validate the actor's state."""
        failures = []
        warnings = []

        try:
            # Check basic requirements
            if not self._event_source:
                failures.append("Event source not available - input control may be restricted")
                return ValidationResult(
                    success=False,
                    goal_achieved=False,
                    failures=failures,
                    warnings=warnings,
                    details={"event_source": None}
                )

            # Get current states
            screen_bounds = await self._get_screen_bounds()
            mouse_pos = await self._get_mouse_position()
            keyboard_mods = await self._get_keyboard_modifiers()
            active_app = await self._get_active_application()

            # Validate states against expected values
            details = {
                "screen_bounds": screen_bounds,
                "mouse_position": mouse_pos,
                "keyboard_modifiers": list(keyboard_mods),
                "active_application": active_app
            }

            if expected_state:
                if 'mouse_position' in expected_state and not self._positions_match(
                    mouse_pos, expected_state['mouse_position'], tolerance=5
                ):
                    failures.append(f"Mouse position mismatch: {mouse_pos} vs {expected_state['mouse_position']}")

                if 'keyboard_modifiers' in expected_state:
                    expected_mods = set(expected_state['keyboard_modifiers'])
                    if keyboard_mods != expected_mods:
                        warnings.append(f"Keyboard modifier mismatch: {keyboard_mods} vs {expected_mods}")

                if 'active_application' in expected_state and active_app != expected_state['active_application']:
                    warnings.append(
                        f"Active application mismatch: {active_app} vs {expected_state['active_application']}")

            success = len(failures) == 0
            goal_achieved = success and len(warnings) == 0

            return ValidationResult(
                success=success,
                goal_achieved=goal_achieved,
                failures=failures,
                warnings=warnings,
                details=details
            )

        except Exception as e:
            logger.error(f"Validation error: {e}")
            return ValidationResult(
                success=False,
                goal_achieved=False,
                failures=[f"Validation error: {str(e)}"],
                warnings=warnings,
                details={}
            )

    async def _click(self, x: int, y: int) -> bool:
        """Perform mouse click at coordinates."""
        try:
            await self._move_mouse(x, y)

            click_down = Quartz.CGEventCreateMouseEvent(
                None, Quartz.kCGEventLeftMouseDown, (x, y), Quartz.kCGMouseButtonLeft
            )
            click_up = Quartz.CGEventCreateMouseEvent(
                None, Quartz.kCGEventLeftMouseUp, (x, y), Quartz.kCGMouseButtonLeft
            )

            Quartz.CGEventPost(Quartz.kCGHIDEventTap, click_down)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, click_up)

            Quartz.CFRelease(click_down)
            Quartz.CFRelease(click_up)

            return True
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return False

    async def _double_click(self, x: int, y: int) -> bool:
        """Perform double click at coordinates."""
        try:
            await self._click(x, y)
            await asyncio.sleep(0.1)
            await self._click(x, y)
            return True
        except Exception as e:
            logger.error(f"Double click failed: {e}")
            return False

    async def _right_click(self, x: int, y: int) -> bool:
        """Perform right click at coordinates."""
        try:
            await self._move_mouse(x, y)

            click_down = Quartz.CGEventCreateMouseEvent(
                None, Quartz.kCGEventRightMouseDown, (x, y), Quartz.kCGMouseButtonRight
            )
            click_up = Quartz.CGEventCreateMouseEvent(
                None, Quartz.kCGEventRightMouseUp, (x, y), Quartz.kCGMouseButtonRight
            )

            Quartz.CGEventPost(Quartz.kCGHIDEventTap, click_down)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, click_up)

            Quartz.CFRelease(click_down)
            Quartz.CFRelease(click_up)

            return True
        except Exception as e:
            logger.error(f"Right click failed: {e}")
            return False

    async def _move_mouse(self, x: int, y: int) -> bool:
        """Move mouse to coordinates."""
        try:
            move_event = Quartz.CGEventCreateMouseEvent(
                None, Quartz.kCGEventMouseMoved, (x, y), 0
            )
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, move_event)
            Quartz.CFRelease(move_event)
            return True
        except Exception as e:
            logger.error(f"Mouse move failed: {e}")
            return False

    async def _drag_mouse(self, start_x: int, start_y: int, end_x: int, end_y: int) -> bool:
        """Drag mouse from start to end coordinates."""
        try:
            await self._move_mouse(start_x, start_y)

            down_event = Quartz.CGEventCreateMouseEvent(
                None, Quartz.kCGEventLeftMouseDown, (start_x, start_y), Quartz.kCGMouseButtonLeft
            )
            drag_event = Quartz.CGEventCreateMouseEvent(
                None, Quartz.kCGEventLeftMouseDragged, (end_x, end_y), Quartz.kCGMouseButtonLeft
            )
            up_event = Quartz.CGEventCreateMouseEvent(
                None, Quartz.kCGEventLeftMouseUp, (end_x, end_y), Quartz.kCGMouseButtonLeft
            )

            Quartz.CGEventPost(Quartz.kCGHIDEventTap, down_event)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, drag_event)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, up_event)

            Quartz.CFRelease(down_event)
            Quartz.CFRelease(drag_event)
            Quartz.CFRelease(up_event)

            return True
        except Exception as e:
            logger.error(f"Mouse drag failed: {e}")
            return False

    async def _type_text(self, text: str) -> bool:
        """Type text string."""
        try:
            for char in text:
                key_down = Quartz.CGEventCreateKeyboardEvent(None, 0, True)
                key_up = Quartz.CGEventCreateKeyboardEvent(None, 0, False)

                Quartz.CGEventKeyboardSetUnicodeString(
                    key_down, len(char), chr(ord(char))
                )
                Quartz.CGEventKeyboardSetUnicodeString(
                    key_up, len(char), chr(ord(char))
                )

                Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_down)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_up)

                Quartz.CFRelease(key_down)
                Quartz.CFRelease(key_up)

                await asyncio.sleep(0.01)

            return True
        except Exception as e:
            logger.error(f"Type text failed: {e}")
            return False

    async def _press_key(self, key_code: int, modifiers: List[int] = None) -> bool:
        """Press key with optional modifiers."""
        try:
            flags = sum(modifiers) if modifiers else 0

            key_down = Quartz.CGEventCreateKeyboardEvent(None, key_code, True)
            key_up = Quartz.CGEventCreateKeyboardEvent(None, key_code, False)

            Quartz.CGEventSetFlags(key_down, flags)
            Quartz.CGEventSetFlags(key_up, flags)

            Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_down)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_up)

            Quartz.CFRelease(key_down)
            Quartz.CFRelease(key_up)

            return True
        except Exception as e:
            logger.error(f"Key press failed: {e}")
            return False

    async def _get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse coordinates."""
        try:
            pos = NSEvent.mouseLocation()
            return (int(pos.x), int(pos.y))
        except Exception as e:
            logger.error(f"Get mouse position failed: {e}")
            return (0, 0)

    async def _open_application(self, name: str) -> bool:
        """Open application by name."""
        try:
            self.workspace.launchApplication_(name)
            return True
        except Exception as e:
            logger.error(f"Open application failed: {e}")
            return False

    async def _switch_application(self, name: str) -> bool:
        """Switch to application by name."""
        try:
            for app in self.workspace.runningApplications():
                if app.localizedName() == name:
                    app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
                    return True
            return False
        except Exception as e:
            logger.error(f"Switch application failed: {e}")
            return False

    async def _find_window(self, name: str) -> Optional[Dict[str, Any]]:
        """Find window by name."""
        try:
            options = (Quartz.kCGWindowListOptionOnScreenOnly |
                       Quartz.kCGWindowListExcludeDesktopElements)
            window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)

            for window in window_list:
                if (window.get("kCGWindowName", "") == name or
                    window.get("kCGWindowOwnerName", "") == name):
                    return {
                        'id': window.get('kCGWindowNumber', 0),
                        'bounds': window.get('kCGWindowBounds', {}),
                        'app_pid': window.get('kCGWindowOwnerPID', 0)
                    }
            return None
        except Exception as e:
            logger.error(f"Find window failed: {e}")
            return None

    async def _get_screen_bounds(self) -> Tuple[float, float, float, float]:
        """Get main screen bounds."""
        screen = NSScreen.mainScreen()

        frame = screen.frame()
        return (frame.origin.x, frame.origin.y, frame.size.width, frame.size.height)

    async def _get_keyboard_modifiers(self) -> set:
        """Get current keyboard modifiers."""
        modifiers = set()
        flags = NSEvent.modifierFlags()

        modifier_map = {
            Quartz.kCGEventFlagMaskCommand: 'command',
            Quartz.kCGEventFlagMaskShift: 'shift',
            Quartz.kCGEventFlagMaskControl: 'control',
            Quartz.kCGEventFlagMaskAlternate: 'option',
            Quartz.kCGEventFlagMaskSecondaryFn: 'fn'
        }

        for flag, name in modifier_map.items():
            if flags & flag:
                modifiers.add(name)

        return modifiers

    async def _get_active_application(self) -> str:
        """Get name of currently active application."""
        try:
            app = self.workspace.frontmostApplication()
            return app.localizedName() if app else ""
        except Exception as e:
            logger.error(f"Get active application failed: {e}")
            return ""

    def _positions_match(self, pos1: Tuple[int, int], pos2: Tuple[int, int], tolerance: int = 5) -> bool:
        """Check if two positions match within tolerance."""
        x1, y1 = pos1
        x2, y2 = pos2
        return (abs(x1 - x2) <= tolerance and abs(y1 - y2) <= tolerance)

    def _is_position_in_bounds(self, pos: Tuple[int, int], bounds: Tuple[float, float, float, float]) -> bool:
        """Check if position is within screen bounds."""
        x, y = pos
        origin_x, origin_y, width, height = bounds
        return (origin_x <= x <= origin_x + width and
                origin_y <= y <= origin_y + height)

    async def _run_apple_script(self, script: str) -> Optional[str]:
        """Run AppleScript and return result."""
        try:
            process = await asyncio.create_subprocess_exec(
                'osascript', '-e', script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if stderr:
                logger.error(f"AppleScript error: {stderr.decode()}")
                return None

            return stdout.decode().strip()
        except Exception as e:
            logger.error(f"AppleScript execution failed: {e}")
            return None

    async def cleanup(self):
        """Clean up resources."""
        try:
            if self._event_source:
                Quartz.CFRelease(self._event_source)
                self._event_source = None
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
