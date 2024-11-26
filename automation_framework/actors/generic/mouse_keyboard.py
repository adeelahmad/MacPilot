from typing import Dict, Any, Tuple, Optional, List
import Quartz
from Cocoa import NSEvent, NSPoint, NSMakePoint, NSEventTypeLeftMouseDown, NSEventTypeLeftMouseUp
import logging
from ..base import ActorStack

import Quartz
from Cocoa import (
    NSWorkspace,
    NSScreen,
    NSEvent,
    NSApplication,
    NSApp,
    NSImage,
    NSBitmapImageRep,
    NSData,
    NSMakeRect,
    NSObject,
    NSNotificationCenter
)
import Vision
import objc
import logging
from typing import List, Dict, Any, Optional, Tuple
import Foundation
import AppKit
from PIL import Image
import numpy as np
import os
from datetime import datetime
import subprocess

from Cocoa import (
    NSWorkspace,
    NSRunningApplication,
    NSApplicationActivateIgnoringOtherApps,
    NSApplication,
)

logger = logging.getLogger(__name__)
import asyncio  # Add missing import


class GenericActorStack(ActorStack):
    async def _type_text(self, text: str) -> bool:
        """Type text with proper async handling."""
        try:
            for char in text:
                # Create string event
                key_down = Quartz.CGEventCreateKeyboardEvent(None, 0, True)
                key_up = Quartz.CGEventCreateKeyboardEvent(None, 0, False)

                # Set unicode string
                Quartz.CGEventKeyboardSetUnicodeString(
                    key_down,
                    len(char),
                    chr(ord(char))
                )
                Quartz.CGEventKeyboardSetUnicodeString(
                    key_up,
                    len(char),
                    chr(ord(char))
                )

                # Post events
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_down)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_up)

                # Cleanup
                Quartz.CFRelease(key_down)
                Quartz.CFRelease(key_up)

                # Small delay between chars
                await asyncio.sleep(0.01)

            return True
        except Exception as e:
            logger.error(f"Type text failed: {e}")
            return False

    name = "generic"
    description = "Native macOS mouse/keyboard control"

    capabilities = {
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

    @classmethod
    def get_capabilities(cls) -> Dict[str, Any]:
        return cls.capabilities

    async def execute_action(self, action: str, **kwargs) -> Any:
        try:
            if action == 'click':
                return await self._click(kwargs['x'], kwargs['y'])
            elif action == 'double_click':
                return await self._double_click(kwargs['x'], kwargs['y'])
            elif action == 'right_click':
                return await self._right_click(kwargs['x'], kwargs['y'])
            elif action == 'move_mouse':
                return await self._move_mouse(kwargs['x'], kwargs['y'])
            elif action == 'drag_mouse':
                return await self._drag_mouse(
                    kwargs['start_x'], kwargs['start_y'],
                    kwargs['end_x'], kwargs['end_y']
                )
            elif action == 'type_text':
                return await self._type_text(kwargs['text'])
            elif action == 'press_key':
                return await self._press_key(
                    kwargs['key_code'],
                    kwargs.get('modifiers', [])
                )
            elif action == 'get_mouse_position':
                return await self._get_mouse_position()
            elif action == 'open_application':
                return await self._open_application(kwargs['name'])
            elif action == 'switch_application':
                return await self._switch_application(kwargs['name'])
            elif action == 'find_window':
                return await self._find_window(kwargs['name'])
            elif action == 'activate_app':
                return await self._activate_app(kwargs['bundle_id'])
            elif action == 'switch_to_window':
                return await self._switch_to_window(kwargs['window_title'])
            else:
                raise ValueError(f"Unknown action: {action}")
        except Exception as e:
            logger.error(f"Error executing action {action}: {e}")
            return False

    def validate_state(self) -> bool:
        try:
            # Check if we can create events
            return self._event_source is not None
        except Exception:
            return False

    async def _activate_app(self, bundle_id: str) -> bool:
        """Activate app by bundle ID."""
        try:
            for app in NSWorkspace.sharedWorkspace().runningApplications():
                if app.bundleIdentifier() == bundle_id:
                    app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
                    return True
            return False  # App not found or not running
        except Exception as e:
            logger.error(f"Failed to activate app: {e}")
            return False

    async def _switch_to_window(self, window_title: str) -> bool:
        """Switch to window by title."""
        try:
            # Use AppleScript to switch windows
            script = f"""
            tell application "System Events"
                tell process "{window_title}"
                    perform action "AXRaise" of window 1
                end tell
            end tell
            """
            result = await self._run_apple_script(script)
            return result is not None
        except Exception as e:
            logger.error(f"Failed to switch to window: {e}")
            return False

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

    async def _click(self, x: int, y: int) -> bool:
        try:
            # Move mouse
            await self._move_mouse(x, y)

            # Create click events
            click_down = Quartz.CGEventCreateMouseEvent(
                None,
                Quartz.kCGEventLeftMouseDown,
                (x, y),
                Quartz.kCGMouseButtonLeft
            )
            click_up = Quartz.CGEventCreateMouseEvent(
                None,
                Quartz.kCGEventLeftMouseUp,
                (x, y),
                Quartz.kCGMouseButtonLeft
            )

            # Post events
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, click_down)
            Quartz.CFRelease(click_down)

            Quartz.CGEventPost(Quartz.kCGHIDEventTap, click_up)
            Quartz.CFRelease(click_up)

            return True
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return False

    async def _double_click(self, x: int, y: int) -> bool:
        try:
            # First click
            await self._click(x, y)

            # Short delay
            await asyncio.sleep(0.1)

            # Second click
            await self._click(x, y)
            return True
        except Exception as e:
            logger.error(f"Double click failed: {e}")
            return False

    async def _right_click(self, x: int, y: int) -> bool:
        try:
            await self._move_mouse(x, y)

            click_down = Quartz.CGEventCreateMouseEvent(
                None,
                Quartz.kCGEventRightMouseDown,
                (x, y),
                Quartz.kCGMouseButtonRight
            )
            click_up = Quartz.CGEventCreateMouseEvent(
                None,
                Quartz.kCGEventRightMouseUp,
                (x, y),
                Quartz.kCGMouseButtonRight
            )

            Quartz.CGEventPost(Quartz.kCGHIDEventTap, click_down)
            Quartz.CFRelease(click_down)

            Quartz.CGEventPost(Quartz.kCGHIDEventTap, click_up)
            Quartz.CFRelease(click_up)

            return True
        except Exception as e:
            logger.error(f"Right click failed: {e}")
            return False

    async def _move_mouse(self, x: int, y: int) -> bool:
        try:
            move_event = Quartz.CGEventCreateMouseEvent(
                None,
                Quartz.kCGEventMouseMoved,
                (x, y),
                0
            )
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, move_event)
            Quartz.CFRelease(move_event)
            return True
        except Exception as e:
            logger.error(f"Mouse move failed: {e}")
            return False

    async def _drag_mouse(self, start_x: int, start_y: int, end_x: int, end_y: int) -> bool:
        try:
            # Move to start position
            await self._move_mouse(start_x, start_y)

            # Mouse down
            down_event = Quartz.CGEventCreateMouseEvent(
                None,
                Quartz.kCGEventLeftMouseDown,
                (start_x, start_y),
                Quartz.kCGMouseButtonLeft
            )
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, down_event)
            Quartz.CFRelease(down_event)

            # Drag
            drag_event = Quartz.CGEventCreateMouseEvent(
                None,
                Quartz.kCGEventLeftMouseDragged,
                (end_x, end_y),
                Quartz.kCGMouseButtonLeft
            )
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, drag_event)
            Quartz.CFRelease(drag_event)

            # Mouse up
            up_event = Quartz.CGEventCreateMouseEvent(
                None,
                Quartz.kCGEventLeftMouseUp,
                (end_x, end_y),
                Quartz.kCGMouseButtonLeft
            )
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, up_event)
            Quartz.CFRelease(up_event)

            return True
        except Exception as e:
            logger.error(f"Mouse drag failed: {e}")
            return False

    async def _type_textx(self, text: str) -> bool:
        try:
            for char in text:
                # Create string event
                key_down = Quartz.CGEventCreateKeyboardEvent(None, 0, True)
                key_up = Quartz.CGEventCreateKeyboardEvent(None, 0, False)

                # Set unicode string
                Quartz.CGEventKeyboardSetUnicodeString(
                    key_down,
                    len(char),
                    chr(ord(char))
                )
                Quartz.CGEventKeyboardSetUnicodeString(
                    key_up,
                    len(char),
                    chr(ord(char))
                )

                # Post events
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_down)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_up)

                # Cleanup
                Quartz.CFRelease(key_down)
                Quartz.CFRelease(key_up)

                # Small delay between chars
                await asyncio.sleep(0.01)

            return True
        except Exception as e:
            logger.error(f"Type text failed: {e}")
            return False

    async def _press_key(self, key_code: int, modifiers: List[int] = None) -> bool:
        try:
            # Apply modifiers
            flags = 0
            if modifiers:
                for modifier in modifiers:
                    flags |= modifier

            # Create events
            key_down = Quartz.CGEventCreateKeyboardEvent(None, key_code, True)
            key_up = Quartz.CGEventCreateKeyboardEvent(None, key_code, False)

            # Set flags
            Quartz.CGEventSetFlags(key_down, flags)
            Quartz.CGEventSetFlags(key_up, flags)

            # Post events
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_down)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_up)

            # Cleanup
            Quartz.CFRelease(key_down)
            Quartz.CFRelease(key_up)

            return True
        except Exception as e:
            logger.error(f"Key press failed: {e}")
            return False

    async def _get_mouse_position(self) -> Tuple[int, int]:
        try:
            pos = NSEvent.mouseLocation()
            return (int(pos.x), int(pos.y))
        except Exception as e:
            logger.error(f"Get mouse position failed: {e}")
            return (0, 0)

    async def _open_application(self, name: str) -> bool:
        try:
            workspace = NSWorkspace.sharedWorkspace()
            workspace.launchApplication_(name)
            return True
        except Exception as e:
            logger.error(f"Open application failed: {e}")
            return False

    async def _switch_application(self, name: str) -> bool:
        try:
            workspace = NSWorkspace.sharedWorkspace()
            app = workspace.runningApplications().firstObject()
            while app:
                if app.localizedName() == name:
                    app.activateWithOptions_(AppKit.NSApplicationActivateIgnoringOtherApps)
                    return True
                app = app.nextObject()
            return False
        except Exception as e:
            logger.error(f"Switch application failed: {e}")
            return False

    async def _find_window(self, name: str) -> Optional[Dict[str, Any]]:
        try:
            options = (Quartz.kCGWindowListOptionOnScreenOnly
                       | Quartz.kCGWindowListExcludeDesktopElements)
            windowList = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)
            for window in windowList:
                if (window.get("kCGWindowName", "") == name
                    or window.get("kCGWindowOwnerName", "") == name):
                    return {
                        'id': window.get('kCGWindowNumber', 0),
                        'bounds': window.get('kCGWindowBounds', {}),
                        'app_pid': window.get('kCGWindowOwnerPID', 0)
                    }
            return None
        except Exception as e:
            logger.error(f"Find window failed: {e}")
            return None
