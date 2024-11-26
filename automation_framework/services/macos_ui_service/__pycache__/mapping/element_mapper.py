from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import math

@dataclass
class UIElement:
    """Represents a UI element with spatial information."""
    id: str
    type: str
    text: Optional[str]
    x: int
    y: int
    width: int
    height: int
    confidence: float
    clickable: bool
    children: List['UIElement'] = None

class ElementMapper:
    """Maps and analyzes relationships between UI elements."""

    def __init__(self):
        self.elements: List[UIElement] = []

    def add_element(self, element: UIElement):
        """Add UI element to mapping."""
        self.elements.append(element)

    def find_nearest(self, x: int, y: int) -> Optional[UIElement]:
        """Find nearest element to coordinates."""
        if not self.elements:
            return None

        nearest = min(
            self.elements,
            key=lambda e: math.sqrt(
                (e.x + e.width/2 - x)**2 +
                (e.y + e.height/2 - y)**2
            )
        )
        return nearest

    def find_containing(self, x: int, y: int) -> Optional[UIElement]:
        """Find element containing coordinates."""
        for element in self.elements:
            if (element.x <= x <= element.x + element.width and
                element.y <= y <= element.y + element.height):
                return element
        return None

    def find_overlapping(self, element: UIElement) -> List[UIElement]:
        """Find elements overlapping with given element."""
        overlapping = []
        for other in self.elements:
            if other.id == element.id:
                continue

            if (element.x < other.x + other.width and
                element.x + element.width > other.x and
                element.y < other.y + other.height and
                element.y + element.height > other.y):
                overlapping.append(other)

        return overlapping

    def find_by_text(self, text: str, partial: bool = False) -> List[UIElement]:
        """Find elements containing text."""
        matching = []
        for element in self.elements:
            if element.text:
                if partial and text.lower() in element.text.lower():
                    matching.append(element)
                elif text.lower() == element.text.lower():
                    matching.append(element)
        return matching

    def find_by_type(self, type_name: str) -> List[UIElement]:
        """Find elements of specific type."""
        return [e for e in self.elements if e.type == type_name]

    def build_spatial_tree(self) -> Dict[str, Any]:
        """Build tree representing spatial relationships."""
        # Sort elements by area (largest first)
        sorted_elements = sorted(
            self.elements,
            key=lambda e: e.width * e.height,
            reverse=True
        )

        # Build containment tree
        root = {
            "elements": [],
            "children": []
        }

        def is_contained(inner: UIElement, outer: UIElement) -> bool:
            return (inner.x >= outer.x and
                   inner.y >= outer.y and
                   inner.x + inner.width <= outer.x + outer.width and
                   inner.y + inner.height <= outer.y + outer.height)

        def add_to_tree(element: UIElement, node: Dict[str, Any]):
            # Check if element is contained by any existing children
            for child in node["children"]:
                container = child["elements"][0]  # First element is container
                if is_contained(element, container):
                    add_to_tree(element, child)
                    return

            # Element not contained, create new node
            new_node = {
                "elements": [element],
                "children": []
            }

            # Move any existing children that are contained by this element
            i = 0
            while i < len(node["children"]):
                child = node["children"][i]
                contained = child["elements"][0]
                if is_contained(contained, element):
                    new_node["children"].append(child)
                    node["children"].pop(i)
                else:
                    i += 1

            node["children"].append(new_node)

        # Add all elements to tree
        for element in sorted_elements:
            add_to_tree(element, root)

        return root

    def analyze_layout(self) -> Dict[str, Any]:
        """Analyze layout patterns in UI elements."""
        analysis = {
            "alignment": {
                "left": [],
                "right": [],
                "top": [],
                "bottom": [],
                "center_x": [],
                "center_y": []
            },
            "spacing": {
                "horizontal": [],
                "vertical": []
            },
            "grouping": []
        }

        # Find aligned elements
        for i, elem1 in enumerate(self.elements):
            for elem2 in self.elements[i+1:]:
                # Left alignment
                if abs(elem1.x - elem2.x) < 5:
                    analysis["alignment"]["left"].append((elem1, elem2))

                # Right alignment
                if abs((elem1.x + elem1.width) -
                      (elem2.x + elem2.width)) < 5:
                    analysis["alignment"]["right"].append((elem1, elem2))

                # Top alignment
                if abs(elem1.y - elem2.y) < 5:
                    analysis["alignment"]["top"].append((elem1, elem2))

                # Bottom alignment
                if abs((elem1.y + elem1.height) -
                      (elem2.y + elem2.height)) < 5:
                    analysis["alignment"]["bottom"].append((elem1, elem2))

                # Center alignment
                if abs((elem1.x + elem1.width/2) -
                      (elem2.x + elem2.width/2)) < 5:
                    analysis["alignment"]["center_x"].append((elem1, elem2))

                if abs((elem1.y + elem1.height/2) -
                      (elem2.y + elem2.height/2)) < 5:
                    analysis["alignment"]["center_y"].append((elem1, elem2))

        # Find consistent spacing
        sorted_x = sorted(self.elements, key=lambda e: e.x)
        sorted_y = sorted(self.elements, key=lambda e: e.y)

        for i in range(len(sorted_x)-1):
            spacing = sorted_x[i+1].x - (sorted_x[i].x + sorted_x[i].width)
            if spacing > 0:
                analysis["spacing"]["horizontal"].append(
                    (sorted_x[i], sorted_x[i+1], spacing)
                )

        for i in range(len(sorted_y)-1):
            spacing = sorted_y[i+1].y - (sorted_y[i].y + sorted_y[i].height)
            if spacing > 0:
                analysis["spacing"]["vertical"].append(
                    (sorted_y[i], sorted_y[i+1], spacing)
                )

        # Find potential groupings
        def find_groups(elements:```bash
# Create interaction patterns service
cat > task_automation/services/patterns/interaction_patterns.py << 'EOL'
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging

class PatternType(Enum):
    CLICK_AND_WAIT = "click_and_wait"
    FILL_AND_SUBMIT = "fill_and_submit"
    SCROLL_TO_FIND = "scroll_to_find"
    DRAG_AND_DROP = "drag_and_drop"
    MODAL_DIALOG = "modal_dialog"
    DROPDOWN_SELECT = "dropdown_select"

@dataclass
class InteractionPattern:
    """Represents a UI interaction pattern."""
    type: PatternType
    steps: List[Dict[str, Any]]
    success_criteria: Dict[str, Any]
    timeout: float = 30.0
    retry_count: int = 3

class PatternExecutor:
    """Executes UI interaction patterns."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.active_patterns: Dict[str, InteractionPattern] = {}

    async def execute_pattern(self, pattern: InteractionPattern,
                            context: Dict[str, Any]) -> bool:
        """Execute an interaction pattern."""
        pattern_id = f"{pattern.type.value}_{id(pattern)}"
        self.active_patterns[pattern_id] = pattern

        try:
            for attempt in range(pattern.retry_count):
                try:
                    result = await self._execute_steps(pattern.steps, context)
                    if await self._verify_success(pattern.success_criteria, context):
                        return True

                    self.logger.warning(
                        f"Pattern {pattern_id} success criteria not met, "
                        f"attempt {attempt + 1}/{pattern.retry_count}"
                    )
                except Exception as e:
                    self.logger.error(
                        f"Error executing pattern {pattern_id}: {str(e)}"
                    )

                if attempt < pattern.retry_count - 1:
                    await asyncio.sleep(1 * (attempt + 1))

            return False

        finally:
            del self.active_patterns[pattern_id]

    async def _execute_steps(self, steps: List[Dict[str, Any]],
                           context: Dict[str, Any]) -> bool:
        """Execute pattern steps."""
        for step in steps:
            action = step["action"]
            params = step.get("params", {})

            # Substitute context variables in params
            params = self._substitute_variables(params, context)

            # Execute action with retry
            success = False
            for attempt in range(3):
                try:
                    if await self._execute_action(action, params, context):
                        success = True
                        break
                except Exception as e:
                    self.logger.warning(
                        f"Step failed, attempt {attempt + 1}/3: {str(e)}"
                    )
                    await asyncio.sleep(1)

            if not success:
                return False

            # Update context with results if specified
            if "store_result" in step:
                context[step["store_result"]] = True

        return True

    def _substitute_variables(self, params: Dict[str, Any],
                            context: Dict[str, Any]) -> Dict[str, Any]:
        """Substitute context variables in parameters."""
        result = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("$"):
                var_name = value[1:]
                if var_name not in context:
                    raise ValueError(f"Context variable not found: {var_name}")
                result[key] = context[var_name]
            else:
                result[key] = value
        return result

    async def _execute_action(self, action: str, params: Dict[str, Any],
                            context: Dict[str, Any]) -> bool:
        """Execute a single action."""
        actor = context.get("actor")
        if not actor:
            raise ValueError("No actor found in context")

        return await actor.execute_action(action, **params)

    async def _verify_success(self, criteria: Dict[str, Any],
                            context: Dict[str, Any]) -> bool:
        """Verify pattern success criteria."""
        if "element_visible" in criteria:
            element = await self._find_element(
                criteria["element_visible"],
                context
            )
            if not element:
                return False

        if "element_clickable" in criteria:
            element = await self._find_element(
                criteria["element_clickable"],
                context
            )
            if not element or not element.get("clickable"):
                return False

        if "text_present" in criteria:
            if not await self._find_text(criteria["text_present"], context):
                return False

        if "state_changed" in criteria:
            return await self._verify_state_change(
                criteria["state_changed"],
                context
            )

        return True

    async def _find_element(self, criteria: Dict[str, Any],
                          context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find UI element matching criteria."""
        state_manager = context.get("state_manager")
        if not state_manager:
            raise ValueError("No state manager found in context")

        current_state = await state_manager.capture_full_state()

        for element in current_state.ui_elements:
            if all(
                getattr(element, key) == value
                for key, value in criteria.items()
            ):
                return element.__dict__

        return None

    async def _find_text(self, text: str, context: Dict[str, Any]) -> bool:
        """Find text in current state."""
        state_manager = context.get("state_manager")
        if not state_manager:
            raise ValueError("No state manager found in context")

        current_state = await state_manager.capture_full_state()

        for element in current_state.ui_elements:
            if element.text and text in element.text:
                return True

        return False

    async def _verify_state_change(self, expected_changes: Dict[str, Any],
                                 context: Dict[str, Any]) -> bool:
        """Verify state changes."""
        state_manager = context.get("state_manager")
        if not state_manager:
            raise ValueError("No state manager found in context")

        current_state = await state_manager.capture_full_state()
        previous_state = context.get("previous_state")

        if not previous_state:
            return False

        for path, expected_value in expected_changes.items():
            current_value = self._get_nested_value(
                current_state.__dict__,
                path.split(".")
            )
            previous_value = self._get_nested_value(
                previous_state.__dict__,
                path.split(".")
            )

            if current_value == previous_value:
                return False

            if expected_value is not None and current_value != expected_value:
                return False

        return True

    def _get_nested_value(self, obj: Any, path: List[str]) -> Any:
        """Get nested dictionary value using path."""
        for key in path:
            if isinstance(obj, dict):
                if key not in obj:
                    return None
                obj = obj[key]
            else:
                if not hasattr(obj, key):
                    return None
                obj = getattr(obj, key)
        return obj

class PatternLibrary:
    """Library of common UI interaction patterns."""

    @staticmethod
    def click_and_wait(element_criteria: Dict[str, Any],
                      wait_criteria: Dict[str, Any]) -> InteractionPattern:
        """Create click and wait pattern."""
        return InteractionPattern(
            type=PatternType.CLICK_AND_WAIT,
            steps=[
                {
                    "action": "click",
                    "params": {
                        "element": element_criteria
                    }
                }
            ],
            success_criteria=wait_criteria
        )

    @staticmethod
    def fill_and_submit(form_criteria: Dict[str, Any],
                       field_values: Dict[str, str],
                       submit_criteria: Dict[str, Any]) -> InteractionPattern:
        """Create form fill and submit pattern."""
        steps = []

        for field, value in field_values.items():
            steps.append({
                "action": "type_text",
                "params": {
                    "element": {"name": field},
                    "text": value
                }
            })

        steps.append({
            "action": "click",
            "params": {
                "element": submit_criteria
            }
        })

        return InteractionPattern(
            type=PatternType.FILL_AND_SUBMIT,
            steps=steps,
            success_criteria={
                "element_visible": {"type": "success_message"}
            }
        )

    @staticmethod
    def scroll_to_find(scroll_container: Dict[str, Any],
                      target_criteria: Dict[str, Any]) -> InteractionPattern:
        """Create scroll to find pattern."""
        return InteractionPattern(
            type=PatternType.SCROLL_TO_FIND,
            steps=[
                {
                    "action": "scroll",
                    "params": {
                        "element": scroll_container,
                        "direction": "down",
                        "amount": 100
                    },
                    "repeat_until": {
                        "element_visible": target_criteria
                    }
                }
            ],
            success_criteria={
                "element_visible": target_criteria,
                "element_clickable": target_criteria
            }
        )

    @staticmethod
    def drag_and_drop(source_criteria: Dict[str, Any],
                      target_criteria: Dict[str, Any]) -> InteractionPattern:
        """Create drag and drop pattern."""
        return InteractionPattern(
            type=PatternType.DRAG_AND_DROP,
            steps=[
                {
                    "action": "drag",
                    "params": {
                        "source": source_criteria,
                        "target": target_criteria
                    }
                }
            ],
            success_criteria={
                "state_changed": {
                    f"elements[?(@.id=='{source_criteria.get('id')}')].position": None
                }
            }
        )

    @staticmethod
    def handle_modal(trigger_criteria: Dict[str, Any],
                    modal_criteria: Dict[str, Any],
                    action_criteria: Dict[str, Any]) -> InteractionPattern:
        """Create modal dialog pattern."""
        return InteractionPattern(
            type=PatternType.MODAL_DIALOG,
            steps=[
                {
                    "action": "click",
                    "params": {
                        "element": trigger_criteria
                    }
                },
                {
                    "action": "wait",
                    "params": {
                        "condition": {
                            "element_visible": modal_criteria
                        }
                    }
                },
                {
                    "action": "click",
                    "params": {
                        "element": action_criteria
                    }
                }
            ],
            success_criteria={
                "element_visible": {"type": "success_message"}
            }
        )
