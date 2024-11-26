from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
from typing import TypeVar

# Define a type variable for dynamic models
_DynamicBaseModel = TypeVar('_DynamicBaseModel', bound='DynamicBaseModel')


# Base class for dynamic models
class DynamicBaseModel(BaseModel):
    """Base for dynamically created models."""

    def _get_value(self, obj: Dict[str, Any], path: str) -> Any:
        """Get nested dictionary value using dot notation."""
        try:
            current = obj
            for part in path.split('.'):
                if isinstance(current, dict):
                    if part not in current:
                        return None
                    current = current[part]
                elif isinstance(current, list):  # Handle list access
                    try:
                        current = current[int(part)]
                    except (ValueError, IndexError):
                        return None  # Invalid list index or not an integer
                else:
                    return None
            return current
        except Exception as e:
            logger.error(f"Error getting nested value: {e}")
            return None


class ActionStep(BaseModel):
    """
    Represents a single step in an automation action. This model provides a structured
    format for defining actions to be executed by the automation framework.
    """
    step: int = Field(..., description="Step number in the sequence. Must be a positive integer.")
    actor: str = Field(...,
                       description="The actor responsible for executing this action (e.g., 'generic', 'chrome', 'finder').")
    action: str = Field(...,
                        description="The specific action/method to be performed by the actor (e.g., 'click', 'type', 'open_url').")
    params: Dict[str, Any] = Field(default_factory=dict,
                                   description="Parameters required by the action/method. This should be a dictionary where keys are parameter names and values are the corresponding values.")
    expected_outcome: Optional[Dict[str, Any]] = Field(None,
                                                       description="A dictionary representing the expected state of the UI after the action is performed. This is used for validation.")
    fallback: Optional[List[Dict[str, Any]]] = Field(None,
                                                     description="A list of fallback actions to be attempted if the primary action fails. Each fallback action should be a dictionary with 'actor', 'action', and 'params' keys.")


class AnalysisResult(BaseModel):
    """
    Represents the result of analyzing a user instruction. This model encapsulates the AI's
    understanding of the instruction and what needs to be done.
    """
    goal: str = Field(...,
                      description="The overall goal or objective of the user instruction, as interpreted by the AI.")
    required_actions: List[str] = Field(default_factory=list,
                                        description="A list of potential actions that might be required to achieve the goal. This list may not be exhaustive.")
    constraints: List[str] = Field(default_factory=list,
                                   description="Any constraints or limitations identified in the instruction (e.g., time limits, specific conditions).")
    prerequisites: List[str] = Field(default_factory=list,
                                     description="Any prerequisites that must be met before the instruction can be executed (e.g., specific applications must be open).")
    estimated_steps: int = Field(...,
                                 description="An estimate of the number of steps required to complete the instruction. This is for informational purposes and may not be accurate.")


class ValidationResult(BaseModel):
    """
    Represents the result of validating the execution of an instruction. This model
    provides feedback on the success of the automation and any issues encountered.
    """
    success: bool = Field(..., description="Indicates whether the execution was successful overall.")
    goal_achieved: bool = Field(..., description="Indicates whether the primary goal of the instruction was achieved.")
    issues: List[str] = Field(default_factory=list,
                              description="A list of issues or errors encountered during execution.")
    recommendations: List[str] = Field(default_factory=list,
                                       description="Recommendations for resolving issues or improving the automation process.")


class RecoveryStep(BaseModel):
    """
    Represents a step in a recovery plan when an action fails. This model is similar to
    ActionStep but is specifically for recovery actions.
    """
    step: int = Field(..., description="Step number in the recovery sequence.")
    action: str = Field(..., description="The recovery action to be performed.")
    params: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the recovery action.")
    reason: Optional[str] = Field(None,
                                  description="The reason for this recovery step, explaining why it is necessary.")


class UIElement(BaseModel):
    """
    Represents a UI element detected on the screen. This model captures information
    about UI elements for analysis and interaction.
    """
    id: str = Field(..., description="Unique identifier for the UI element.")
    type: str = Field(..., description="Type of UI element (e.g., 'button', 'text field', 'window').")
    text: Optional[str] = Field(None, description="Text content of the UI element, if any.")
    bounds: Dict[str, float] = Field(...,
                                     description="Bounding box of the UI element, containing 'x', 'y', 'width', and 'height'.")
    attributes: Dict[str, Any] = Field(default_factory=dict,
                                       description="Additional attributes of the UI element (e.g., 'enabled', 'selected').")
    confidence: float = Field(default=1.0, description="Confidence score for the UI element detection (0.0 to 1.0).")
    clickable: bool = Field(default=False, description="Whether the UI element is likely clickable.")
    children: List['UIElement'] = Field(default_factory=list,
                                        description="Child UI elements, if any (used for nested elements).")


class WindowState(BaseModel):
    """
    Represents the state of a window.
    """
    id: int = Field(..., description="Unique identifier for the window.")
    title: str = Field(..., description="Title of the window.")
    app: str = Field(..., description="Application associated with the window.")
    bounds: Dict[str, float] = Field(..., description="Bounding box of the window (x, y, width, height).")
    is_active: bool = Field(default=False, description="Whether the window is currently active.")
    is_minimized: bool = Field(default=False, description="Whether the window is minimized.")
    alpha: float = Field(default=1.0, description="Window transparency (0.0 - 1.0).")
    layer: int = Field(default=0, description="Window layer.")
    memory_usage: int = Field(default=0, description="Memory usage of the window in bytes.")
    sharing_state: int = Field(default=0, description="Window sharing state (e.g., shared between spaces).")


class ApplicationState(BaseModel):
    """
    Represents the state of an application.
    """
    name: str = Field(..., description="Name of the application.")
    bundle_id: str = Field(..., description="Bundle identifier of the application.")
    pid: int = Field(..., description="Process ID of the application.")
    is_active: bool = Field(default=False, description="Whether the application is currently active.")
    windows: List[WindowState] = Field(default_factory=list,
                                       description="List of windows associated with the application.")
    is_frontmost: bool = Field(default=False, description="Whether the application is frontmost.")
    memory_usage: float = Field(default=0.0, description="Memory usage of the application in megabytes.")
    cpu_usage: float = Field(default=0.0, description="CPU usage of the application as a percentage.")


class SystemState(BaseModel):
    """
    Represents the state of the system.
    """
    cpu_percent: float = Field(default=0.0, description="CPU utilization percentage.")
    memory_used: float = Field(default=0.0, description="Amount of memory used in gigabytes.")
    active_displays: int = Field(default=1, description="Number of active displays.")
    screen_resolution: tuple[int, int] = Field(default=(0, 0),
                                               description="Screen resolution (width, height) of the main display.")
    cursor_location: tuple[int, int] = Field(default=(0, 0), description="Current cursor location (x, y).")
    frontmost_app: str = Field(..., description="Name of the frontmost application.")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of the system state.")
    battery_level: Optional[float] = Field(None, description="Battery level (0.0 - 1.0), if available.")
    is_charging: bool = Field(default=False, description="Whether the device is charging, if available.")
    volume_level: float = Field(default=1.0, description="System volume level (0.0 - 1.0).")
    brightness_level: float = Field(default=1.0, description="Screen brightness level (0.0 - 1.0).")


class AccessibilityState(BaseModel):
    """
    Represents the accessibility state of a UI element. This provides information
    relevant to accessibility features.
    """
    role: str = Field(..., description="Accessibility role of the element (e.g., 'button', 'menu', 'dialog').")
    role_description: str = Field(..., description="Description of the accessibility role.")
    title: Optional[str] = Field(None, description="Accessibility title of the element.")
    enabled: bool = Field(default=True, description="Whether the element is enabled.")
    focused: bool = Field(default=False, description="Whether the element is focused.")
    position: Optional[tuple[int, int]] = Field(None, description="Position of the element (x, y).")
    size: Optional[tuple[int, int]] = Field(None, description="Size of the element (width, height).")
    value: Optional[str] = Field(None, description="Value of the element, if applicable.")


class MenuState(BaseModel):
    """
    Represents the state of the menu bar.
    """
    items: List[Dict[str, Any]] = Field(default_factory=list,
                                        description="List of menu items with their properties (e.g., 'name', 'enabled').")
    active_menu: Optional[str] = Field(None, description="Currently active menu, if any.")
    enabled: bool = Field(default=True, description="Whether the menu bar is enabled.")


class UIState(BaseModel):
    """
    Represents the complete UI state. This is a comprehensive snapshot of the
    system's UI at a specific moment.
    """
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of the UI state.")
    system: "SystemState" = Field(..., description="System state information.")
    applications: List["ApplicationState"] = Field(default_factory=list, description="List of running applications.")
    windows: List["WindowState"] = Field(default_factory=list, description="List of open windows.")
    ui_elements: List["UIElement"] = Field(default_factory=list, description="List of detected UI elements.")
    menu: "MenuState" = Field(default_factory=lambda: MenuState(), description="Current menu state.")
    accessibility: Optional["AccessibilityState"] = Field(None, description="Accessibility state information.")
    mouse_position: Tuple[int, int] = Field(default=(0, 0), description="Current mouse position (x, y).")
    keyboard_modifiers: List[str] = Field(default_factory=list,
                                          description="Active keyboard modifiers (e.g., 'shift', 'ctrl', 'alt', 'command').")
    active_window: Optional[str] = Field(None, description="Title of the active window.")

    def dict(self, **kwargs):
        """
        Returns the model's data as a dictionary, preserving Pydantic's default behavior.
        """
        return super().dict(**kwargs)


UIElement.update_forward_refs()
