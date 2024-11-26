from typing import Dict, Any, List, Type
from .interaction_patterns import InteractionPattern, PatternType


class PatternRegistry:
    """Registry for UI interaction patterns."""

    _patterns: Dict[PatternType, Dict[str, InteractionPattern]] = {
        pattern_type: {}
        for pattern_type in PatternType
    }

    @classmethod
    def register_pattern(cls, pattern: InteractionPattern, name: str):
        """Register a pattern with given name."""
        cls._patterns[pattern.type][name] = pattern

    @classmethod
    def get_pattern(cls, pattern_type: PatternType, name: str) -> InteractionPattern:
        """Get pattern by type and name."""
        if pattern_type not in cls._patterns:
            raise ValueError(f"Unknown pattern type: {pattern_type}")

        if name not in cls._patterns[pattern_type]:
            raise ValueError(
                f"Pattern {name} not found for type {pattern_type}"
            )

        return cls._patterns[pattern_type][name]

    @classmethod
    def get_all_patterns(cls, pattern_type: PatternType = None) -> Dict[str, List[str]]:
        """List all registered patterns."""
        if pattern_type:
            return {
                pattern_type.value: list(cls._patterns[pattern_type].keys())
            }

        return {
            pt.value: list(patterns.keys())
            for pt, patterns in cls._patterns.items()
        }

    @classmethod
    def clear_patterns(cls):
        """Clear all registered patterns."""
        for pattern_type in cls._patterns:
            cls._patterns[pattern_type].clear()
