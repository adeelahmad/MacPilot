# File Path: automation_framework/services/state/manager.py
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import Quartz
from Cocoa import NSWorkspace, NSScreen, NSEvent, NSApplication
import logging
import psutil
import objc
from pathlib import Path
import AppKit
import Vision
from datetime import datetime
from PIL import Image
import numpy as np
from ..vision.processor import VisionProcessor

logger = logging.getLogger(__name__)


@dataclass
class UIElement:
    """Represents a UI element."""

    id: str
    type: str
    text: Optional[str]
    bounds: Dict[str, float]
    attributes: Dict[str, Any]
    confidence: float
    clickable: bool
    children: List["UIElement"] = field(default_factory=list)


@dataclass
class WindowState:
    """Represents window state."""

    id: int
    title: str = ""
    app: str = ""
    bounds: Dict[str, float] = field(default_factory=dict)
    is_active: bool = False
    is_minimized: bool = False
    alpha: float = 1.0
    layer: int = 0
    memory_usage: int = 0
    sharing_state: int = 0


@dataclass
class ApplicationState:
    """Represents application state."""

    name: str
    bundle_id: str
    pid: int
    is_active: bool
    windows: List[WindowState] = field(default_factory=list)
    is_frontmost: bool = False
    memory_usage: float = 0.0
    cpu_usage: float = 0.0


@dataclass
class MenuState:
    """Represents menu bar state."""

    items: List[Dict[str, Any]] = field(default_factory=list)
    active_menu: Optional[str] = None
    enabled: bool = True


@dataclass
class SystemState:
    """Represents system state."""

    cpu_percent: float = 0.0
    memory_used: float = 0.0
    active_displays: int = 1
    screen_resolution: Tuple[int, int] = (0, 0)
    cursor_location: Tuple[int, int] = (0, 0)
    frontmost_app: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    battery_level: Optional[float] = None
    is_charging: bool = False
    volume_level: float = 1.0
    brightness_level: float = 1.0


@dataclass
class AccessibilityState:
    """Represents accessibility information."""

    role: str = ""
    role_description: str = ""
    title: Optional[str] = None
    enabled: bool = True
    focused: bool = False
    position: Optional[Tuple[int, int]] = None
    size: Optional[Tuple[int, int]] = None
    value: Optional[str] = None


@dataclass
class UIState:
    """Represents complete UI state."""

    timestamp: datetime = field(default_factory=datetime.now)
    system: SystemState = field(default_factory=SystemState)
    applications: List[ApplicationState] = field(default_factory=list)
    windows: List[WindowState] = field(default_factory=list)
    ui_elements: List[UIElement] = field(default_factory=list)
    menu: MenuState = field(default_factory=MenuState)
    accessibility: Optional[AccessibilityState] = None
    mouse_position: Tuple[int, int] = (0, 0)
    keyboard_modifiers: List[str] = field(default_factory=list)
    active_window: Optional[str] = None


class StateManager:
    """Native macOS state management."""

    def __init__(self):
        self.workspace = NSWorkspace.sharedWorkspace()
        self.screen = NSScreen.mainScreen()
        self.vision_processor = VisionProcessor()

    async def capture_full_state(self) -> UIState:
        """Capture complete system and UI state."""
        try:
            timestamp = datetime.now()
            mouse_pos = await self._get_mouse_position()

            # Get all states
            system_state = await self._capture_system_state()
            window_states = await self._capture_window_states()
            app_states = await self._capture_application_states()
            ui_elements = await self._capture_ui_elements()
            # menu_state = await self._capture_menu_state()
            accessibility = await self._capture_accessibility_state()
            modifiers = await self._get_keyboard_modifiers()

            # Determine active window
            active_window = None
            active_window_list = Quartz.CGWindowListCopyWindowInfo(
                Quartz.kCGWindowListOptionOnScreenOnly
                | Quartz.kCGWindowListExcludeDesktopElements,
                Quartz.kCGNullWindowID,
            )

            if active_window_list:
                for window in active_window_list:
                    # Get layer and on-screen status
                    layer = window.get(Quartz.kCGWindowLayer, 0)
                    is_onscreen = window.get(Quartz.kCGWindowIsOnscreen, False)

                    if layer == 0 and is_onscreen:
                        active_window = window.get(Quartz.kCGWindowName, "")
                        break

            return UIState(
                timestamp=timestamp,
                system=system_state,
                applications=app_states,
                windows=window_states,
                ui_elements=ui_elements,
                # menu=menu_state,
                accessibility=accessibility,
                mouse_position=mouse_pos,
                keyboard_modifiers=modifiers,
                active_window=active_window,
            )

        except Exception as e:
            logger.error(f"Error capturing full state: {e}")
            return UIState()

    async def _capture_system_state(self) -> SystemState:
        """Capture system-level state."""
        try:
            # Get screen info
            frame = self.screen.frame()
            resolution = (int(frame.size.width), int(frame.size.height))

            # Get cursor position
            mouse_loc = NSEvent.mouseLocation()
            cursor_loc = (int(mouse_loc.x), int(mouse_loc.y))

            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            displays = NSScreen.screens()
            front_app = self.workspace.frontmostApplication()

            # Get power info if available
            try:
                battery = psutil.sensors_battery()
                battery_level = battery.percent if battery else None
                is_charging = battery.power_plugged if battery else False
            except Exception:
                battery_level = None
                is_charging = False

            return SystemState(
                cpu_percent=cpu_percent,
                memory_used=memory.used / (1024 * 1024 * 1024),
                active_displays=len(displays),
                screen_resolution=resolution,
                cursor_location=cursor_loc,
                frontmost_app=front_app.localizedName() if front_app else "",
                timestamp=datetime.now(),
                battery_level=battery_level,
                is_charging=is_charging,
            )
        except Exception as e:
            logger.error(f"Error capturing system state: {e}")
            return SystemState()

    async def _get_keyboard_modifiers(self) -> List[str]:
        """Get current keyboard modifier keys."""
        try:
            modifiers = []
            flags = NSEvent.modifierFlags()

            if flags & AppKit.NSEventModifierFlagCommand:
                modifiers.append("command")
            if flags & AppKit.NSEventModifierFlagOption:
                modifiers.append("option")
            if flags & AppKit.NSEventModifierFlagControl:
                modifiers.append("control")
            if flags & AppKit.NSEventModifierFlagShift:
                modifiers.append("shift")
            if flags & AppKit.NSEventModifierFlagFunction:
                modifiers.append("function")

            return modifiers
        except Exception as e:
            logger.error(f"Error getting keyboard modifiers: {e}")
            return []

    async def _capture_window_states(self) -> List[WindowState]:
        """Capture window states safely."""
        try:
            window_list = Quartz.CGWindowListCopyWindowInfo(
                Quartz.kCGWindowListOptionOnScreenOnly
                | Quartz.kCGWindowListExcludeDesktopElements,
                Quartz.kCGNullWindowID,
            )

            windows = []
            if window_list:
                for window in window_list:
                    try:
                        # Safely get window properties
                        window_id = window.get(Quartz.kCGWindowNumber, 0)
                        title = window.get(Quartz.kCGWindowName, "")
                        app_name = window.get(Quartz.kCGWindowOwnerName, "")
                        bounds = window.get(Quartz.kCGWindowBounds, {})

                        # Check window flags
                        is_onscreen = bool(
                            window.get(Quartz.kCGWindowIsOnscreen, False)
                        )
                        try:
                            is_minimized = bool(
                                window.get(Quartz.kCGWindowIsMinimized, False)
                            )
                        except Exception:
                            is_minimized = False

                        # Get other properties safely
                        alpha = float(window.get(Quartz.kCGWindowAlpha, 1.0))
                        layer = int(window.get(Quartz.kCGWindowLayer, 0))
                        memory = int(window.get(Quartz.kCGWindowMemoryUsage, 0))
                        sharing = int(window.get(Quartz.kCGWindowSharingState, 0))

                        # Create window state
                        win_state = WindowState(
                            id=window_id,
                            title=title,
                            app=app_name,
                            bounds=bounds,
                            is_active=is_onscreen and not is_minimized,
                            is_minimized=is_minimized,
                            alpha=alpha,
                            layer=layer,
                            memory_usage=memory,
                            sharing_state=sharing,
                        )
                        windows.append(win_state)

                    except Exception as e:
                        logger.debug(f"Skipping window due to error: {e}")
                        continue

            return windows

        except Exception as e:
            logger.error(f"Error capturing window states: {e}")
            return []

    async def _capture_application_states(self) -> List[ApplicationState]:
        """Capture application states."""
        try:
            apps = []
            running_apps = self.workspace.runningApplications()
            frontmost_pid = self.workspace.frontmostApplication().processIdentifier()

            for app in running_apps:
                try:
                    # Get app info
                    pid = app.processIdentifier()
                    windows = await self._get_app_windows(pid)

                    # Get resource usage
                    try:
                        process = psutil.Process(pid)
                        memory_usage = process.memory_info().rss / (1024 * 1024)
                        cpu_usage = process.cpu_percent(interval=0.1)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        memory_usage = 0.0
                        cpu_usage = 0.0

                    app_state = ApplicationState(
                        name=app.localizedName(),
                        bundle_id=app.bundleIdentifier(),
                        pid=pid,
                        is_active=app.isActive(),
                        is_frontmost=pid == frontmost_pid,
                        windows=windows,
                        memory_usage=memory_usage,
                        cpu_usage=cpu_usage,
                    )
                    apps.append(app_state)

                except Exception as e:
                    logger.debug(f"Skipping app due to error: {e}")
                    continue

            return apps

        except Exception as e:
            logger.error(f"Error capturing application states: {e}")
            return []

    async def _get_app_windows(self, pid: int) -> List[WindowState]:
        """Get windows for specific application."""
        try:
            window_list = Quartz.CGWindowListCopyWindowInfo(
                Quartz.kCGWindowListOptionOnScreenOnly
                | Quartz.kCGWindowListExcludeDesktopElements,
                Quartz.kCGNullWindowID,
            )

            windows = []
            if window_list:
                for window in window_list:
                    try:
                        if window.get(Quartz.kCGWindowOwnerPID) == pid:
                            # Safely get window properties
                            window_id = window.get(Quartz.kCGWindowNumber, 0)
                            title = window.get(Quartz.kCGWindowName, "")
                            app_name = window.get(Quartz.kCGWindowOwnerName, "")
                            bounds = window.get(Quartz.kCGWindowBounds, {})

                            # Check window flags safely
                            is_onscreen = bool(
                                window.get(Quartz.kCGWindowIsOnscreen, False)
                            )
                            try:
                                is_minimized = bool(
                                    window.get(Quartz.kCGWindowIsMinimized, False)
                                )
                            except Exception:
                                is_minimized = False

                            win_state = WindowState(
                                id=window_id,
                                title=title,
                                app=app_name,
                                bounds=bounds,
                                is_active=is_onscreen and not is_minimized,
                                is_minimized=is_minimized,
                                alpha=float(window.get(Quartz.kCGWindowAlpha, 1.0)),
                                layer=int(window.get(Quartz.kCGWindowLayer, 0)),
                                memory_usage=int(
                                    window.get(Quartz.kCGWindowMemoryUsage, 0)
                                ),
                                sharing_state=int(
                                    window.get(Quartz.kCGWindowSharingState, 0)
                                ),
                            )
                            windows.append(win_state)

                    except Exception as e:
                        logger.debug(f"Skipping window due to error: {e}")
                        continue

            return windows

        except Exception as e:
            logger.debug(f"Error getting app windows: {e}")
            return []

    async def _capture_ui_elements(self) -> List[UIElement]:
        """Capture UI elements."""
        try:
            # Get screenshot
            screenshot = await self.vision_processor.capture_screen()
            if not screenshot:
                return []

            # Detect elements
            elements = await self.vision_processor.detect_ui_elements(screenshot)

            # Convert to UIElement objects
            ui_elements = []
            for element in elements:
                ui_elements.append(
                    UIElement(
                        id=element.get("id", str(id(element))),
                        type=element.get("type", ""),
                        text=element.get("text"),
                        bounds=element.get("bounds", {}),
                        attributes=element.get("attributes", {}),
                        confidence=element.get("confidence", 1.0),
                        clickable=element.get("clickable", False),
                        children=[],
                    )
                )

            return ui_elements

        except Exception as e:
            logger.error(f"Error capturing UI elements: {e}")
            return []

    async def _capture_menu_state(self) -> MenuState:
        """Capture menu state safely."""
        try:
            script = """
                tell application "System Events"
                    tell process 1 where frontmost is true
                        set menuItems to {}
                        repeat with menubar in menu bars
                            repeat with menuItem in menu bar items of menubar
                                try
                                    set itemInfo to {name:name of menuItem, enabled:enabled of menuItem}
                                    if enabled of menuItem then
                                        try
                                            set itemInfo to itemInfo & {selected:selected of menuItem}
                                        end try
                                    end if
                                    set end of menuItems to itemInfo
                                end try
                            end repeat
                        end repeat
                        return menuItems
                    end tell
                end tell
            """

            ns_script = AppKit.NSAppleScript.alloc().initWithSource_(script)
            result, error = ns_script.executeAndReturnError_(None)

            if error:
                logger.debug(f"AppleScript error: {error}")
                return MenuState()

            items = []
            if result:
                menu_list = result.descriptorAtIndex_(0).properties()
                for item in menu_list:
                    items.append(
                        {
                            "name": item.get("name", ""),
                            "enabled": bool(item.get("enabled", True)),
                            "selected": bool(item.get("selected", False)),
                        }
                    )

            # Get active menu if any
            active_menu = await self._get_active_menu()

            return MenuState(items=items, active_menu=active_menu, enabled=bool(items))

        except Exception as e:
            logger.error(f"Error capturing menu state: {e}")
            return MenuState()

    async def _get_active_menu(self) -> Optional[str]:
        """Get active menu safely."""
        try:
            script = """
                tell application "System Events"
                    tell process 1 where frontmost is true
                        try
                            return name of menu bar item 1 of menu bar 1 where selected is true
                            end try
                end tell
            end tell
            """
            ns_script = AppKit.NSAppleScript.alloc().initWithSource_(script)
            result, error = ns_script.executeAndReturnError_(None)

            if error:
                return None

            return result.stringValue() if result else None

        except Exception:
            return None

    async def _capture_accessibility_state(self) -> Optional[AccessibilityState]:
        """Capture accessibility state safely."""
        try:
            ax = AppKit.NSWorkspace.sharedWorkspace().frontmostApplication()
            if not ax or not ax.respondsToSelector_("accessibilityRole"):
                return None

            state = AccessibilityState(
                role=ax.accessibilityRole() or "",
                role_description=ax.accessibilityRoleDescription() or "",
                title=ax.accessibilityTitle()
                if ax.respondsToSelector_("accessibilityTitle")
                else None,
                enabled=bool(ax.accessibilityEnabled())
                if ax.respondsToSelector_("accessibilityEnabled")
                else True,
                focused=bool(ax.accessibilityFocused())
                if ax.respondsToSelector_("accessibilityFocused")
                else False,
            )

            # Get position and size if available
            if ax.respondsToSelector_("accessibilityPosition"):
                pos = ax.accessibilityPosition()
                state.position = (int(pos.x), int(pos.y))

            if ax.respondsToSelector_("accessibilitySize"):
                size = ax.accessibilitySize()
                state.size = (int(size.width), int(size.height))

            if ax.respondsToSelector_("accessibilityValue"):
                state.value = str(ax.accessibilityValue())

            return state

        except Exception as e:
            logger.debug(f"Error capturing accessibility state: {e}")
            return None

    async def _get_mouse_position(self) -> Tuple[int, int]:
        """Get mouse position safely."""
        try:
            pos = NSEvent.mouseLocation()
            return (int(pos.x), int(pos.y))
        except Exception:
            return (0, 0)

    async def monitor_state_changes(self, callback: callable, interval: float = 0.5):
        """Monitor state changes with error handling."""
        last_state = None

        while True:
            try:
                current_state = await self.capture_full_state()

                if last_state:
                    changes = self._detect_state_changes(last_state, current_state)
                    if changes:
                        await callback(changes)

                last_state = current_state
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring state changes: {e}")
                await asyncio.sleep(interval)

    def _detect_state_changes(
        self, old_state: UIState, new_state: UIState
    ) -> Dict[str, Any]:
        """Detect state changes safely."""
        changes = {}

        try:
            # Window changes
            window_changes = {"added": [], "removed": [], "modified": []}

            old_windows = {w.id: w for w in old_state.windows}
            new_windows = {w.id: w for w in new_state.windows}

            window_changes["added"] = [
                w for w_id, w in new_windows.items() if w_id not in old_windows
            ]

            window_changes["removed"] = [
                w for w_id, w in old_windows.items() if w_id not in new_windows
            ]

            for w_id, new_window in new_windows.items():
                if w_id in old_windows:
                    old_window = old_windows[w_id]
                    if (
                        new_window.bounds != old_window.bounds
                        or new_window.is_active != old_window.is_active
                        or new_window.is_minimized != old_window.is_minimized
                    ):
                        window_changes["modified"].append(new_window)

            if any(window_changes.values()):
                changes["windows"] = window_changes

            # Application changes
            app_changes = {"launched": [], "terminated": [], "modified": []}

            old_apps = {a.pid: a for a in old_state.applications}
            new_apps = {a.pid: a for a in new_state.applications}

            app_changes["launched"] = [
                a for pid, a in new_apps.items() if pid not in old_apps
            ]

            app_changes["terminated"] = [
                a for pid, a in old_apps.items() if pid not in new_apps
            ]

            for pid, new_app in new_apps.items():
                if pid in old_apps:
                    old_app = old_apps[pid]
                    if (
                        new_app.is_active != old_app.is_active
                        or new_app.is_frontmost != old_app.is_frontmost
                    ):
                        app_changes["modified"].append(new_app)

            if any(app_changes.values()):
                changes["applications"] = app_changes

            # System state changes
            if (
                old_state.system.cpu_percent != new_state.system.cpu_percent
                or old_state.system.memory_used != new_state.system.memory_used
                or old_state.system.frontmost_app != new_state.system.frontmost_app
            ):
                changes["system"] = {
                    "cpu_percent": new_state.system.cpu_percent,
                    "memory_used": new_state.system.memory_used,
                    "frontmost_app": new_state.system.frontmost_app,
                }

            # Mouse position changes
            if old_state.mouse_position != new_state.mouse_position:
                changes["mouse"] = {
                    "old": old_state.mouse_position,
                    "new": new_state.mouse_position,
                }

            # Keyboard modifier changes
            if old_state.keyboard_modifiers != new_state.keyboard_modifiers:
                changes["keyboard"] = {
                    "old": old_state.keyboard_modifiers,
                    "new": new_state.keyboard_modifiers,
                }

            # Active window changes
            if old_state.active_window != new_state.active_window:
                changes["active_window"] = {
                    "old": old_state.active_window,
                    "new": new_state.active_window,
                }

            return changes

        except Exception as e:
            logger.error(f"Error detecting state changes: {e}")
            return {}

    async def get_active_windows(self) -> List[WindowState]:
        """Get list of active (non-minimized) windows."""
        try:
            return [
                w
                for w in await self._capture_window_states()
                if w.is_active and not w.is_minimized
            ]
        except Exception as e:
            logger.error(f"Error getting active windows: {e}")
            return []

    async def get_window_by_id(self, window_id: int) -> Optional[WindowState]:
        """Get specific window by ID."""
        try:
            window_list = Quartz.CGWindowListCopyWindowInfo(
                Quartz.kCGWindowListOptionIncludingWindow, window_id
            )

            if window_list and len(window_list) > 0:
                window = window_list[0]
                return WindowState(
                    id=window_id,
                    title=window.get(Quartz.kCGWindowName, ""),
                    app=window.get(Quartz.kCGWindowOwnerName, ""),
                    bounds=window.get(Quartz.kCGWindowBounds, {}),
                    is_active=window.get(Quartz.kCGWindowIsOnscreen, False),
                    is_minimized=bool(window.get(Quartz.kCGWindowIsMinimized, False)),
                    alpha=float(window.get(Quartz.kCGWindowAlpha, 1.0)),
                    layer=int(window.get(Quartz.kCGWindowLayer, 0)),
                )
            return None

        except Exception as e:
            logger.error(f"Error getting window by ID: {e}")
            return None
