from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging

import Quartz
from Cocoa import NSWorkspace

from .interaction_patterns import InteractionPattern, PatternType

logger = logging.getLogger(__name__)


class PatternMatcher:
    """Match high-level interaction patterns from the current UI state."""

    def __init__(self, state_manager: Any):
        self.state_manager = state_manager
        self.workspace = NSWorkspace.sharedWorkspace()

    async def match_patterns(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Return ranked candidate patterns for a captured state dictionary.
        The return shape is compatible with ExecutionEngine expectations.
        """
        matches: List[Dict[str, Any]] = []
        active_app = (state or {}).get("active_app") or {}
        app_name = str(active_app.get("name", "")).lower()

        if "finder" in app_name:
            matches.append(
                {
                    "pattern": InteractionPattern(
                        type=PatternType.SCROLL_TO_FIND,
                        steps=[{"action": "scroll", "params": {"delta_y": -300}}],
                        success_criteria={},
                    ),
                    "confidence": 0.9,
                    "reason": "Finder context favors search/navigation pattern",
                }
            )
        elif active_app:
            matches.append(
                {
                    "pattern": InteractionPattern(
                        type=PatternType.CLICK_AND_WAIT,
                        steps=[{"action": "click", "params": {}}],
                        success_criteria={},
                    ),
                    "confidence": 0.55,
                    "reason": "Generic app context",
                }
            )

        return matches

    async def _get_window_info(self) -> Optional[Dict[str, Any]]:
        """Return frontmost on-screen window details if available."""
        try:
            window_list = Quartz.CGWindowListCopyWindowInfo(
                Quartz.kCGWindowListOptionOnScreenOnly
                | Quartz.kCGWindowListExcludeDesktopElements,
                Quartz.kCGNullWindowID,
            )
            if not window_list:
                return None

            window = window_list[0]
            bounds = window.get("kCGWindowBounds", {})
            return {
                "id": window.get("kCGWindowNumber"),
                "title": window.get("kCGWindowName", ""),
                "bounds": {
                    "x": bounds.get("X", 0),
                    "y": bounds.get("Y", 0),
                    "width": bounds.get("Width", 0),
                    "height": bounds.get("Height", 0),
                },
                "app": window.get("kCGWindowOwnerName", ""),
            }
        except Exception as exc:
            logger.debug("Unable to read focused window info: %s", exc)
            return None

    def _get_active_app(self) -> Optional[Dict[str, Any]]:
        """Return frontmost app details if available."""
        try:
            app = self.workspace.frontmostApplication()
            if not app:
                return None
            return {
                "name": app.localizedName(),
                "bundle_id": app.bundleIdentifier(),
                "pid": app.processIdentifier(),
            }
        except Exception as exc:
            logger.debug("Unable to read active app: %s", exc)
            return None
