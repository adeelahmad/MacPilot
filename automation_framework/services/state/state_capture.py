#!/usr/bin/env python3

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field
import Quartz
from Cocoa import NSWorkspace, NSScreen, NSEvent
import Vision
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StateChangeType(Enum):
    """Types of state changes that can occur in the UI"""
    WINDOW_CREATED = "window_created"
    WINDOW_CLOSED = "window_closed"
    WINDOW_FOCUSED = "window_focused"
    APP_LAUNCHED = "app_launched"
    APP_TERMINATED = "app_terminated"
    MOUSE_MOVED = "mouse_moved"
    KEYBOARD_INPUT = "keyboard_input"
    SCREEN_CHANGED = "screen_changed"

class UIElementState(BaseModel):
    """Represents the state of a UI element"""
    id: str = Field(..., description="Unique identifier for the UI element")
    type: str = Field(..., description="Type of UI element (button, text field, etc)")
    bounds: Dict[str, float] = Field(..., description="Element's position and size {x, y, width, height}")
    text: Optional[str] = Field(None, description="Text content of the element if any")
    enabled: bool = Field(True, description="Whether the element is interactive")
    focused: bool = Field(False, description="Whether the element has input focus")
    value: Optional[str] = Field(None, description="Current value for input elements")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Additional element attributes")
    children: List["UIElementState"] = Field(default_factory=list, description="Child UI elements")
    parent_id: Optional[str] = Field(None, description="ID of parent element if any")
    accessibility_role: Optional[str] = Field(None, description="Accessibility role of the element")
    clickable: bool = Field(False, description="Whether element appears clickable")
    visible: bool = Field(True, description="Whether element is visible on screen")
    z_index: int = Field(0, description="Stack order of element")
    opacity: float = Field(1.0, description="Element opacity from 0-1")
    timestamp: datetime = Field(default_factory=datetime.now, description="When this state was captured")

class WindowState(BaseModel):
    """Represents the state of a window"""
    id: int = Field(..., description="Unique window identifier")
    pid: int = Field(..., description="Process ID owning the window") 
    app_name: str = Field(..., description="Name of application owning window")
    title: str = Field(..., description="Window title")
    bounds: Dict[str, float] = Field(..., description="Window position and size")
    minimized: bool = Field(False, description="Whether window is minimized")
    focused: bool = Field(False, description="Whether window has focus")
    main: bool = Field(False, description="Whether this is the main window")
    closable: bool = Field(True, description="Whether window can be closed")
    resizable: bool = Field(True, description="Whether window can be resized")
    movable: bool = Field(True, description="Whether window can be moved")
    level: int = Field(0, description="Window level/layer")
    opacity: float = Field(1.0, description="Window opacity from 0-1")
    shadow: bool = Field(True, description="Whether window has shadow")
    toolbar_visible: bool = Field(True, description="Whether toolbar is shown")
    elements: List[UIElementState] = Field(default_factory=list, description="UI elements in window")
    timestamp: datetime = Field(default_factory=datetime.now, description="When state was captured")

class ApplicationState(BaseModel):
    """Represents the state of an application"""
    name: str = Field(..., description="Application name")
    bundle_id: str = Field(..., description="Bundle identifier")
    pid: int = Field(..., description="Process ID")
    focused: bool = Field(False, description="Whether app has focus")
    hidden: bool = Field(False, description="Whether app is hidden")
    windows: List[WindowState] = Field(default_factory=list, description="Application windows")
    memory_usage: float = Field(0.0, description="Memory usage in bytes")
    cpu_usage: float = Field(0.0, description="CPU usage percentage")
    responding: bool = Field(True, description="Whether app is responding")
    launch_time: datetime = Field(default_factory=datetime.now, description="When app was launched")
    timestamp: datetime = Field(default_factory=datetime.now, description="When state was captured")

class ScreenState(BaseModel):
    """Represents display/monitor state"""
    id: int = Field(..., description="Screen identifier")
    bounds: Dict[str, float] = Field(..., description="Screen dimensions")
    scaling: float = Field(1.0, description="Display scaling factor")
    rotation: int = Field(0, description="Screen rotation in degrees")
    primary: bool = Field(False, description="Whether this is primary display")
    built_in: bool = Field(False, description="Whether this is built-in display")
    resolution: Tuple[int, int] = Field(..., description="Screen resolution")
    refresh_rate: int = Field(60, description="Refresh rate in Hz")
    color_space: str = Field("sRGB", description="Color space name")
    timestamp: datetime = Field(default_factory=datetime.now, description="When state was captured")

class MouseState(BaseModel):
    """Represents mouse/cursor state"""
    position: Tuple[int, int] = Field(..., description="Cursor coordinates")
    buttons: List[bool] = Field(default_factory=list, description="Button press states")
    scroll_delta: Tuple[float, float] = Field((0.0, 0.0), description="Scroll wheel delta")
    speed: float = Field(1.0, description="Cursor movement speed")
    acceleration: bool = Field(True, description="Whether acceleration is enabled")
    confined: bool = Field(False, description="Whether cursor is confined")
    hidden: bool = Field(False, description="Whether cursor is hidden")
    timestamp: datetime = Field(default_factory=datetime.now, description="When state was captured")

class KeyboardState(BaseModel):
    """Represents keyboard input state"""
    modifiers: List[str] = Field(default_factory=list, description="Active modifier keys")
    keys_down: List[str] = Field(default_factory=list, description="Currently pressed keys")
    caps_lock: bool = Field(False, description="Caps lock state")
    num_lock: bool = Field(False, description="Num lock state")
    function_keys: bool = Field(True, description="Whether function keys are standard")
    layout: str = Field("US", description="Keyboard layout")
    input_source: str = Field("en-US", description="Active input source")
    timestamp: datetime = Field(default_factory=datetime.now, description="When state was captured")

class ClipboardState(BaseModel):
    """Represents clipboard/pasteboard state"""
    types: List[str] = Field(default_factory=list, description="Available content types")
    text: Optional[str] = Field(None, description="Text content if available")
    rtf: Optional[str] = Field(None, description="RTF content if available")
    html: Optional[str] = Field(None, description="HTML content if available")
    image: Optional[bytes] = Field(None, description="Image data if available")
    file_paths: List[str] = Field(default_factory=list, description="Copied file paths")
    change_count: int = Field(0, description="Clipboard change counter")
    timestamp: datetime = Field(default_factory=datetime.now, description="When state was captured")

class SystemState(BaseModel):
    """Represents overall system state"""
    screens: List[ScreenState] = Field(default_factory=list, description="Connected displays")
    mouse: MouseState = Field(..., description="Mouse/cursor state")
    keyboard: KeyboardState = Field(..., description="Keyboard state")
    clipboard: ClipboardState = Field(..., description="Clipboard state")
    focused_app: Optional[str] = Field(None, description="Currently focused application")
    frontmost_window: Optional[int] = Field(None, description="ID of frontmost window")
    running_apps: List[ApplicationState] = Field(default_factory=list, description="Running applications")
    cpu_usage: float = Field(0.0, description="Overall CPU usage")
    memory_usage: float = Field(0.0, description="Overall memory usage")
    timestamp: datetime = Field(default_factory=datetime.now, description="When state was captured")

class StateCapture:
    """Captures and manages UI state"""
    
    def __init__(self):
        self.workspace = NSWorkspace.sharedWorkspace()
        self.last_state: Optional[SystemState] = None
        self._setup_vision()

    def _setup_vision(self):
        """Initialize Vision framework requests"""
        self.text_request = Vision.VNRecognizeTextRequest.alloc().init()
        self.text_request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
        
        self.element_request = Vision.VNDetectTextRectanglesRequest.alloc().init()
        self.element_request.setReportCharacterBoxes_(True)

    async def capture_full_state(self) -> SystemState:
        """Capture complete system UI state"""
        try:
            screens = await self._capture_screens()
            mouse = await self._capture_mouse()
            keyboard = await self._capture_keyboard()
            clipboard = await self._capture_clipboard()
            apps = await self._capture_applications()

            focused_app = None
            frontmost_window = None
            
            for app in apps:
                if app.focused:
                    focused_app = app.name
                    for window in app.windows:
                        if window.focused:
                            frontmost_window = window.id
                            break
                    break

            return SystemState(
                screens=screens,
                mouse=mouse,
                keyboard=keyboard,
                clipboard=clipboard,
                focused_app=focused_app,
                frontmost_window=frontmost_window,
                running_apps=apps,
                cpu_usage=await self._get_cpu_usage(),
                memory_usage=await self._get_memory_usage()
            )
        except Exception as e:
            logger.error(f"Error capturing state: {e}")
            raise

    async def _capture_screens(self) -> List[ScreenState]:
        """Capture state of all displays"""
        screens = []
        for screen in NSScreen.screens():
            frame = screen.frame()
            screens.append(ScreenState(
                id=hash(screen),
                bounds={
                    'x': frame.origin.x,
                    'y': frame.origin.y,
                    'width': frame.size.width,
                    'height': frame.size.height
                },
                scaling=screen.backingScaleFactor(),
                primary=screen == NSScreen.mainScreen(),
                resolution=(
                    int(frame.size.width * screen.backingScaleFactor()),
                    int(frame.size.height * screen.backingScaleFactor())
                )
            ))
        return screens

    async def _capture_mouse(self) -> MouseState:
        """Capture mouse/cursor state"""
        pos = NSEvent.mouseLocation()
        return MouseState(
            position=(int(pos.x), int(pos.y)),
            buttons=[
                NSEvent.pressedMouseButtons() & (1 << i) != 0
                for i in range(5)
            ]
        )

    async def _capture_keyboard(self) -> KeyboardState:
        """Capture keyboard state"""
        flags = NSEvent.modifierFlags()
        modifiers = []
        
        if flags & NSEventModifierFlagCommand:
            modifiers.append('command')
        if flags & NSEventModifierFlagOption:
            modifiers.append('option')
        if flags & NSEventModifierFlagControl:
            modifiers.append('control')
        if flags & NSEventModifierFlagShift:
            modifiers.append('shift')
            
        return KeyboardState(
            modifiers=modifiers,
            caps_lock=flags & NSEventModifierFlagCapsLock != 0
        )

    async def _capture_clipboard(self) -> ClipboardState:
        """Capture clipboard/pasteboard state"""
        pb = NSPasteboard.generalPasteboard()
        types = pb.types()
        
        state = ClipboardState(
            types=[str(t) for t in types],
            change_count=pb.changeCount()
        )
        
        if NSPasteboardTypeString in types:
            state.text = pb.stringForType_(NSPasteboardTypeString)
            
        if NSPasteboardTypeRTF in types:
            state.rtf = pb.dataForType_(NSPasteboardTypeRTF)
            
        if NSPasteboardTypeHTML in types:
            state.html = pb.stringForType_(NSPasteboardTypeHTML)
            
        return state

    async def _capture_applications(self) -> List[ApplicationState]:
        """Capture state of running applications"""
        apps = []
        for app in self.workspace.runningApplications():
            windows = await self._capture_windows(app)
            apps.append(ApplicationState(
                name=app.localizedName(),
                bundle_id=app.bundleIdentifier(),
                pid=app.processIdentifier(),
                focused=app.isActive(),
                hidden=app.isHidden(),
                windows=windows,
                launch_time=app.launchDate()
            ))
        return apps

    async def _capture_windows(self, app) -> List[WindowState]:
        """Capture window states for an application"""
        windows = []
        
        # Get window list
        window_list = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly |
            Quartz.kCGWindowListExcludeDesktopElements,
            Quartz.kCGNullWindowID
        )
        
        for window in window_list:
            if window.get(Quartz.kCGWindowOwnerPID) == app.processIdentifier():
                # Capture window elements
                elements = await self._capture_window_elements(
                    window.get(Quartz.kCGWindowNumber, 0)
                )
                
                windows.append(WindowState(
                    id=window.get(Quartz.kCGWindowNumber, 0),
                    pid=app.processIdentifier(),
                    app_name=app.localizedName(),
                    title=window.get(Quartz.kCGWindowName, ""),
                    bounds=window.get(Quartz.kCGWindowBounds, {}),
                    minimized=window.get(Quartz.kCGWindowIsMinimized, False),
                    focused=window.get(Quartz.kCGWindowIsOnscreen, False),
                    level=window.get(Quartz.kCGWindowLayer, 0),
                    opacity=window.get(Quartz.kCGWindowAlpha, 1.0),
                    elements=elements
                ))
                
        return windows

    async def _capture_window_elements(self, window_id: int) -> List[UIElementState]:
        """Capture UI elements in a window"""
        elements = []
        
        try:
            #
#!/usr/bin/env python3

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field
import Quartz
from Cocoa import NSWorkspace, NSScreen, NSEvent
import Vision
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StateChangeType(Enum):
    """Types of state changes that can occur in the UI"""
    WINDOW_CREATED = "window_created"
    WINDOW_CLOSED = "window_closed"
    WINDOW_FOCUSED = "window_focused"
    APP_LAUNCHED = "app_launched"
    APP_TERMINATED = "app_terminated"
    MOUSE_MOVED = "mouse_moved"
    KEYBOARD_INPUT = "keyboard_input"
    SCREEN_CHANGED = "screen_changed"

class UIElementState(BaseModel):
    """Represents the state of a UI element"""
    id: str = Field(..., description="Unique identifier for the UI element")
    type: str = Field(..., description="Type of UI element (button, text field, etc)")
    bounds: Dict[str, float] = Field(..., description="Element's position and size {x, y, width, height}")
    text: Optional[str] = Field(None, description="Text content of the element if any")
    enabled: bool = Field(True, description="Whether the element is interactive")
    focused: bool = Field(False, description="Whether the element has input focus")
    value: Optional[str] = Field(None, description="Current value for input elements")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Additional element attributes")
    children: List["UIElementState"] = Field(default_factory=list, description="Child UI elements")
    parent_id: Optional[str] = Field(None, description="ID of parent element if any")
    accessibility_role: Optional[str] = Field(None, description="Accessibility role of the element")
    clickable: bool = Field(False, description="Whether element appears clickable")
    visible: bool = Field(True, description="Whether element is visible on screen")
    z_index: int = Field(0, description="Stack order of element")
    opacity: float = Field(1.0, description="Element opacity from 0-1")
    timestamp: datetime = Field(default_factory=datetime.now, description="When this state was captured")

class WindowState(BaseModel):
    """Represents the state of a window"""
    id: int = Field(..., description="Unique window identifier")
    pid: int = Field(..., description="Process ID owning the window") 
    app_name: str = Field(..., description="Name of application owning window")
    title: str = Field(..., description="Window title")
    bounds: Dict[str, float] = Field(..., description="Window position and size")
    minimized: bool = Field(False, description="Whether window is minimized")
    focused: bool = Field(False, description="Whether window has focus")
    main: bool = Field(False, description="Whether this is the main window")
    closable: bool = Field(True, description="Whether window can be closed")
    resizable: bool = Field(True, description="Whether window can be resized")
    movable: bool = Field(True, description="Whether window can be moved")
    level: int = Field(0, description="Window level/layer")
    opacity: float = Field(1.0, description="Window opacity from 0-1")
    shadow: bool = Field(True, description="Whether window has shadow")
    toolbar_visible: bool = Field(True, description="Whether toolbar is shown")
    elements: List[UIElementState] = Field(default_factory=list, description="UI elements in window")
    timestamp: datetime = Field(default_factory=datetime.now, description="When state was captured")

class ApplicationState(BaseModel):
    """Represents the state of an application"""
    name: str = Field(..., description="Application name")
    bundle_id: str = Field(..., description="Bundle identifier")
    pid: int = Field(..., description="Process ID")
    focused: bool = Field(False, description="Whether app has focus")
    hidden: bool = Field(False, description="Whether app is hidden")
    windows: List[WindowState] = Field(default_factory=list, description="Application windows")
    memory_usage: float = Field(0.0, description="Memory usage in bytes")
    cpu_usage: float = Field(0.0, description="CPU usage percentage")
    responding: bool = Field(True, description="Whether app is responding")
    launch_time: datetime = Field(default_factory=datetime.now, description="When app was launched")
    timestamp: datetime = Field(default_factory=datetime.now, description="When state was captured")

class ScreenState(BaseModel):
    """Represents display/monitor state"""
    id: int = Field(..., description="Screen identifier")
    bounds: Dict[str, float] = Field(..., description="Screen dimensions")
    scaling: float = Field(1.0, description="Display scaling factor")
    rotation: int = Field(0, description="Screen rotation in degrees")
    primary: bool = Field(False, description="Whether this is primary display")
    built_in: bool = Field(False, description="Whether this is built-in display")
    resolution: Tuple[int, int] = Field(..., description="Screen resolution")
    refresh_rate: int = Field(60, description="Refresh rate in Hz")
    color_space: str = Field("sRGB", description="Color space name")
    timestamp: datetime = Field(default_factory=datetime.now, description="When state was captured")

class MouseState(BaseModel):
    """Represents mouse/cursor state"""
    position: Tuple[int, int] = Field(..., description="Cursor coordinates")
    buttons: List[bool] = Field(default_factory=list, description="Button press states")
    scroll_delta: Tuple[float, float] = Field((0.0, 0.0), description="Scroll wheel delta")
    speed: float = Field(1.0, description="Cursor movement speed")
    acceleration: bool = Field(True, description="Whether acceleration is enabled")
    confined: bool = Field(False, description="Whether cursor is confined")
    hidden: bool = Field(False, description="Whether cursor is hidden")
    timestamp: datetime = Field(default_factory=datetime.now, description="When state was captured")

class KeyboardState(BaseModel):
    """Represents keyboard input state"""
    modifiers: List[str] = Field(default_factory=list, description="Active modifier keys")
    keys_down: List[str] = Field(default_factory=list, description="Currently pressed keys")
    caps_lock: bool = Field(False, description="Caps lock state")
    num_lock: bool = Field(False, description="Num lock state")
    function_keys: bool = Field(True, description="Whether function keys are standard")
    layout: str = Field("US", description="Keyboard layout")
    input_source: str = Field("en-US", description="Active input source")
    timestamp: datetime = Field(default_factory=datetime.now, description="When state was captured")

class ClipboardState(BaseModel):
    """Represents clipboard/pasteboard state"""
    types: List[str] = Field(default_factory=list, description="Available content types")
    text: Optional[str] = Field(None, description="Text content if available")
    rtf: Optional[str] = Field(None, description="RTF content if available")
    html: Optional[str] = Field(None, description="HTML content if available")
    image: Optional[bytes] = Field(None, description="Image data if available")
    file_paths: List[str] = Field(default_factory=list, description="Copied file paths")
    change_count: int = Field(0, description="Clipboard change counter")
    timestamp: datetime = Field(default_factory=datetime.now, description="When state was captured")

class SystemState(BaseModel):
    """Represents overall system state"""
    screens: List[ScreenState] = Field(default_factory=list, description="Connected displays")
    mouse: MouseState = Field(..., description="Mouse/cursor state")
    keyboard: KeyboardState = Field(..., description="Keyboard state")
    clipboard: ClipboardState = Field(..., description="Clipboard state")
    focused_app: Optional[str] = Field(None, description="Currently focused application")
    frontmost_window: Optional[int] = Field(None, description="ID of frontmost window")
    running_apps: List[ApplicationState] = Field(default_factory=list, description="Running applications")
    cpu_usage: float = Field(0.0, description="Overall CPU usage")
    memory_usage: float = Field(0.0, description="Overall memory usage")
    timestamp: datetime = Field(default_factory=datetime.now, description="When state was captured")

class StateCapture:
    """Captures and manages UI state"""
    
    def __init__(self):
        self.workspace = NSWorkspace.sharedWorkspace()
        self.last_state: Optional[SystemState] = None
        self._setup_vision()

    def _setup_vision(self):
        """Initialize Vision framework requests"""
        self.text_request = Vision.VNRecognizeTextRequest.alloc().init()
        self.text_request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
        
        self.element_request = Vision.VNDetectTextRectanglesRequest.alloc().init()
        self.element_request.setReportCharacterBoxes_(True)

    async def capture_full_state(self) -> SystemState:
        """Capture complete system UI state"""
        try:
            screens = await self._capture_screens()
            mouse = await self._capture_mouse()
            keyboard = await self._capture_keyboard()
            clipboard = await self._capture_clipboard()
            apps = await self._capture_applications()

            focused_app = None
            frontmost_window = None
            
            for app in apps:
                if app.focused:
                    focused_app = app.name
                    for window in app.windows:
                        if window.focused:
                            frontmost_window = window.id
                            break
                    break

            return SystemState(
                screens=screens,
                mouse=mouse,
                keyboard=keyboard,
                clipboard=clipboard,
                focused_app=focused_app,
                frontmost_window=frontmost_window,
                running_apps=apps,
                cpu_usage=await self._get_cpu_usage(),
                memory_usage=await self._get_memory_usage()
            )
        except Exception as e:
            logger.error(f"Error capturing state: {e}")
            raise

    async def _capture_screens(self) -> List[ScreenState]:
        """Capture state of all displays"""
        screens = []
        for screen in NSScreen.screens():
            frame = screen.frame()
            screens.append(ScreenState(
                id=hash(screen),
                bounds={
                    'x': frame.origin.x,
                    'y': frame.origin.y,
                    'width': frame.size.width,
                    'height': frame.size.height
                },
                scaling=screen.backingScaleFactor(),
                primary=screen == NSScreen.mainScreen(),
                resolution=(
                    int(frame.size.width * screen.backingScaleFactor()),
                    int(frame.size.height * screen.backingScaleFactor())
                )
            ))
        return screens

    async def _capture_mouse(self) -> MouseState:
        """Capture mouse/cursor state"""
        pos = NSEvent.mouseLocation()
        return MouseState(
            position=(int(pos.x), int(pos.y)),
            buttons=[
                NSEvent.pressedMouseButtons() & (1 << i) != 0
                for i in range(5)
            ]
        )

    async def _capture_keyboard(self) -> KeyboardState:
        """Capture keyboard state"""
        flags = NSEvent.modifierFlags()
        modifiers = []
        
        if flags & NSEventModifierFlagCommand:
            modifiers.append('command')
        if flags & NSEventModifierFlagOption:
            modifiers.append('option')
        if flags & NSEventModifierFlagControl:
            modifiers.append('control')
        if flags & NSEventModifierFlagShift:
            modifiers.append('shift')
            
        return KeyboardState(
            modifiers=modifiers,
            caps_lock=flags & NSEventModifierFlagCapsLock != 0
        )

    async def _capture_clipboard(self) -> ClipboardState:
        """Capture clipboard/pasteboard state"""
        pb = NSPasteboard.generalPasteboard()
        types = pb.types()
        
        state = ClipboardState(
            types=[str(t) for t in types],
            change_count=pb.changeCount()
        )
        
        if NSPasteboardTypeString in types:
            state.text = pb.stringForType_(NSPasteboardTypeString)
            
        if NSPasteboardTypeRTF in types:
            state.rtf = pb.dataForType_(NSPasteboardTypeRTF)
            
        if NSPasteboardTypeHTML in types:
            state.html = pb.stringForType_(NSPasteboardTypeHTML)
            
        return state

    async def _capture_applications(self) -> List[ApplicationState]:
        """Capture state of running applications"""
        apps = []
        for app in self.workspace.runningApplications():
            windows = await self._capture_windows(app)
            apps.append(ApplicationState(
                name=app.localizedName(),
                bundle_id=app.bundleIdentifier(),
                pid=app.processIdentifier(),
                focused=app.isActive(),
                hidden=app.isHidden(),
                windows=windows,
                launch_time=app.launchDate()
            ))
        return apps

    async def _capture_windows(self, app) -> List[WindowState]:
        """Capture window states for an application"""
        windows = []
        
        # Get window list
        window_list = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly |
            Quartz.kCGWindowListExcludeDesktopElements,
            Quartz.kCGNullWindowID
        )
        
        for window in window_list:
            if window.get(Quartz.kCGWindowOwnerPID) == app.processIdentifier():
                # Capture window elements
                elements = await self._capture_window_elements(
                    window.get(Quartz.kCGWindowNumber, 0)
                )
                
                windows.append(WindowState(
                    id=window.get(Quartz.kCGWindowNumber, 0),
                    pid=app.processIdentifier(),
                    app_name=app.localizedName(),
                    title=window.get(Quartz.kCGWindowName, ""),
                    bounds=window.get(Quartz.kCGWindowBounds, {}),
                    minimized=window.get(Quartz.kCGWindowIsMinimized, False),
                    focused=window.get(Quartz.kCGWindowIsOnscreen, False),
                    level=window.get(Quartz.kCGWindowLayer, 0),
                    opacity=window.get(Quartz.kCGWindowAlpha, 1.0),
                    elements=elements
                ))
                
        return windows

    async def _capture_window_elements(self, window_id: int) -> List[UIElementState]:
        """Capture UI elements in a window"""
        elements = []
        
        try:
            # Capture window image
            image = Quartz.CGWindowListCreateImage(
                Quartz.CGRectNull,
                Quartz.kCGWindowListOptionIncludingWindow,
                window_id,
                Quartz.kCGWindowImageDefault
            )
            
            if not image:
                return elements
                
            # Create Vision handler
            handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(
                image,
                None
            )
            
            # Perform requests
            success = handler.performRequests_error_([
                self.text_request,
                self.element_request
            ], None)
            
            if not success:
                return elements
                
            # Process text results
            for observation in self.text_request.results():
                bbox = observation.boundingBox()
                confidence = observation.confidence()
                
                if confidence > 0.5:
                    elements.append(UIElementState(
                        id=f"text_{hash(observation)}",
                        type="text",
                        bounds={
                            'x': bbox.origin.x,
                            'y': bbox.origin.y,
                            'width': bbox.size.width,
                            'height': bbox.size.height
                        },
                        text=observation.text(),
                        attributes={
                            'confidence': confidence
                        },
                        clickable=self._is_element_clickable(bbox)
                    ))
                    
            # Process rectangle results
            for observation in self.element_request.results():
                bbox = observation.boundingBox()
                elements.append(UIElementState(
                    id=f"element_{hash(observation)}",
                    type="rectangle",
                    bounds={
                        'x': bbox.origin.x,
                        'y': bbox.origin.y,
                        'width': bbox.size.width,
                        'height': bbox.size.height
                    },
                    attributes={
                        'character_boxes': observation.characterBoxes()
                    },
                    clickable=self._is_element_clickable(bbox)
                ))
                
            return elements
            
        except Exception as e:
            logger.error(f"Error capturing window elements: {e}")
            return elements
            
    def _is_element_clickable(self, bounds: Vision.VNRectangleObservation) -> bool:
        """Determine if element is likely clickable based on size"""
        min_size = 20  # Minimum clickable size in pixels
        return bounds.size.width >= min_size and bounds.size.height >= min_size

    async def _get_cpu_usage(self) -> float:
        """Get overall CPU usage percentage"""
        try:
            cmd = "ps -A -o %cpu | awk '{s+=$1} END {print s}'"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            return float(stdout.decode())
        except:
            return 0.0

    async def _get_memory_usage(self) -> float:
        """Get overall memory usage in bytes"""
        try:
            cmd = "vm_stat | grep 'Pages active' | awk '{print $3}'"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            pages = int(stdout.decode().strip().rstrip('.'))
            return pages * 4096  # Convert pages to bytes
        except:
            return 0.0

    async def get_element_at_position(self, x: int, y: int) -> Optional[UIElementState]:
        """Find UI element at given coordinates"""
        if not self.last_state:
            return None
            
        for app in self.last_state.running_apps:
            for window in app.windows:
                for element in window.elements:
                    bounds = element.bounds
                    if (bounds['x'] <= x <= bounds['x'] + bounds['width'] and
                        bounds['y'] <= y <= bounds['y'] + bounds['height']):
                        return element
        return None

    async def find_element_by_text(self, text: str, partial: bool = False) -> Optional[UIElementState]:
        """Find UI element containing specified text"""
        if not self.last_state:
            return None
            
        for app in self.last_state.running_apps:
            for window in app.windows:
                for element in window.elements:
                    if element.text:
                        if partial and text.lower() in element.text.lower():
                            return element
                        elif text.lower() == element.text.lower():
                            return element
        return None

    async def find_elements_by_type(self, element_type: str) -> List[UIElementState]:
        """Find all UI elements of specified type"""
        elements = []
        if not self.last_state:
            return elements
            
        for app in self.last_state.running_apps:
            for window in app.windows:
                for element in window.elements:
                    if element.type == element_type:
                        elements.append(element)
        return elements

    async def find_clickable_elements(self) -> List[UIElementState]:
        """Find all clickable UI elements"""
        elements = []
        if not self.last_state:
            return elements
            
        for app in self.last_state.running_apps:
            for window in app.windows:
                for element in window.elements:
                    if element.clickable:
                        elements.append(element)
        return elements

    async def monitor_state_changes(self, callback: callable, interval: float = 0.5):
        """Monitor UI state changes"""
        while True:
            try:
                current_state = await self.capture_full_state()
                
                if self.last_state:
                    changes = self._detect_state_changes(self.last_state, current_state)
                    if changes:
                        await callback(changes)
                        
                self.last_state = current_state
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring state: {e}")
                await asyncio.sleep(interval)

    def _detect_state_changes(self, old_state: SystemState, new_state: SystemState) -> List[Dict[str, Any]]:
        """Detect changes between UI states"""
        changes = []
        
        # Check application changes
        old_apps = {app.pid: app for app in old_state.running_apps}
        new_apps = {app.pid: app for app in new_state.running_apps}
        
        for pid in set(new_apps) - set(old_apps):
            changes.append({
                'type': StateChangeType.APP_LAUNCHED,
                'app': new_apps[pid].name,
                'pid': pid
            })
            
        for pid in set(old_apps) - set(new_apps):
            changes.append({
                'type': StateChangeType.APP_TERMINATED,
                'app': old_apps[pid].name,
                'pid': pid
            })
            
        # Check window changes
        old_windows = {}
        new_windows = {}
        
        for app in old_state.running_apps:
            for window in app.windows:
                old_windows[window.id] = window
                
        for app in new_state.running_apps:
            for window in app.windows:
                new_windows[window.id] = window
                
        for wid in set(new_windows) - set(old_windows):
            changes.append({
                'type': StateChangeType.WINDOW_CREATED,
                'window_id': wid,
                'title': new_windows[wid].title
            })
            
        for wid in set(old_windows) - set(new_windows):
            changes.append({
                'type': StateChangeType.WINDOW_CLOSED,
                'window_id': wid,
                'title': old_windows[wid].title
            })
            
        # Check focus changes
        if old_state.focused_app != new_state.focused_app:
            changes.append({
                'type': StateChangeType.WINDOW_FOCUSED,
                'old_app': old_state.focused_app,
                'new_app': new_state.focused_app
            })
            
        # Check mouse movement
        if old_state.mouse.position != new_state.mouse.position:
            changes.append({
                'type': StateChangeType.MOUSE_MOVED,
                'old_pos': old_state.mouse.position,
                'new_pos': new_state.mouse.position
            })
            
        # Check keyboard changes
        if old_state.keyboard.modifiers != new_state.keyboard.modifiers:
            changes.append({
                'type': StateChangeType.KEYBOARD_INPUT,
                'old_mods': old_state.keyboard.modifiers,
                'new_mods': new_state.keyboard.modifiers
            })
            
        return changes

class StateCaptureSession:
    """Context manager for state capture sessions"""
    
    def __init__(self):
        self.capturer = StateCapture()
        self.start_state = None
        self.end_state = None
        
    async def __aenter__(self):
        """Start capture session"""
        self.start_state = await self.capturer.capture_full_state()
        return self.capturer
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """End capture session"""
        self.end_state = await self.capturer.capture_full_state()
        
    def get_state_diff(self) -> Dict[str, Any]:
        """Get differences between start and end states"""
        if not self.start_state or not self.end_state:
            return {}
            
        return {
            'changes': self.capturer._detect_state_changes(
                self.start_state,
                self.end_state
            ),
            'duration': (
                self.end_state.timestamp - self.start_state.timestamp
            ).total_seconds()
        }

async def main():
    """Example usage"""
    async with StateCaptureSession() as capturer:
        # Monitor state changes
        changes = []
        
        async def change_callback(change):
            changes.append(change)
            print(f"State change detected: {change}")
            
        # Start monitoring in background
        monitor_task = asyncio.create_task(
            capturer.monitor_state_changes(change_callback)
        )
        
        try:
            # Wait for some time
            await asyncio.sleep(10)
            
        finally:
            # Cancel monitoring
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
                
        # Get final state diff
        diff = capturer.get_state_diff()
        print(f"\nFinal state changes: {json.dumps(diff, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
