# File Path: automation_framework/services/validation/state_validator.py
from typing import Dict, Any, List, Optional
import re
from dataclasses import dataclass
from enum import Enum


class ValidationLevel(Enum):
    STRICT = "strict"
    NORMAL = "normal"
    LENIENT = "lenient"


@dataclass
class ValidationRule:
    """Rule for state validation."""
    path: str  # JSON path to value
    condition: str  # Condition to check
    value: Any  # Expected value or pattern
    level: ValidationLevel = ValidationLevel.NORMAL


@dataclass
class ValidationResult:
    """Result of state validation."""
    success: bool
    failures: List[str]
    warnings: List[str]


class StateValidator:
    """Validates UI state against expected conditions."""

    def __init__(self, validation_level: ValidationLevel = ValidationLevel.NORMAL):
        self.validation_level = validation_level

    def validate_state(self, current_state: Dict[str, Any],
                       expected_state: Dict[str, Any]) -> ValidationResult:
        """
        Validate current state against expected state.

        Args:
            current_state: Current UI state
            expected_state: Expected UI state

        Returns:
            ValidationResult containing success status and any failures/warnings
        """
        failures = []
        warnings = []

        # Extract validation rules
        rules = self._extract_rules(expected_state)

        # Apply each rule
        for rule in rules:
            result = self._apply_rule(current_state, rule)
            if not result.success:
                if rule.level == ValidationLevel.STRICT:
                    failures.extend(result.failures)
                else:
                    warnings.extend(result.failures)

        return ValidationResult(
            success=len(failures) == 0,
            failures=failures,
            warnings=warnings
        )

    def _extract_rules(self, expected_state: Dict[str, Any]) -> List[ValidationRule]:
        """Extract validation rules from expected state."""
        rules = []

        def process_dict(d: Dict[str, Any], path: str = ""):
            for key, value in d.items():
                current_path = f"{path}.{key}" if path else key

                if isinstance(value, dict):
                    if "_validation" in value:
                        # Extract explicit validation rule
                        rules.append(ValidationRule(
                            path=current_path,
                            condition=value["_validation"].get("condition", "equals"),
                            value=value["_validation"].get("value"),
                            level=ValidationLevel(
                                value["_validation"].get("level", "normal")
                            )
                        ))
                    else:
                        process_dict(value, current_path)
                elif isinstance(value, list):
                    process_list(value, current_path)
                else:
                    # Create implicit equals rule
                    rules.append(ValidationRule(
                        path=current_path,
                        condition="equals",
                        value=value
                    ))

        def process_list(lst: List[Any], path: str):
            for i, value in enumerate(lst):
                current_path = f"{path}[{i}]"
                if isinstance(value, dict):
                    process_dict(value, current_path)
                elif isinstance(value, list):
                    process_list(value, current_path)
                else:
                    rules.append(ValidationRule(
                        path=current_path,
                        condition="equals",
                        value=value
                    ))

        process_dict(expected_state)
        return rules

    def _apply_rule(self, state: Dict[str, Any],
                    rule: ValidationRule) -> ValidationResult:
        """Apply validation rule to state."""
        try:
            # Get actual value using JSON path
            actual = self._get_value(state, rule.path)

            if actual is None:
                return ValidationResult(
                    success=False,
                    failures=[f"Path {rule.path} not found in state"],
                    warnings=[]
                )

            # Apply condition
            if rule.condition == "equals":
                success = actual == rule.value
            elif rule.condition == "contains":
                success = rule.value in actual
            elif rule.condition == "matches":
                success = bool(re.match(rule.value, actual))
            elif rule.condition == "greater_than":
                success = actual > rule.value
            elif rule.condition == "less_than":
                success = actual < rule.value
            else:
                raise ValueError(f"Unknown condition: {rule.condition}")

            if not success:
                return ValidationResult(
                    success=False,
                    failures=[
                        f"Validation failed for {rule.path}: "
                        f"expected {rule.value} ({rule.condition}), "
                        f"got {actual}"
                    ],
                    warnings=[]
                )

            return ValidationResult(success=True, failures=[], warnings=[])

        except Exception as e:
            return ValidationResult(
                success=False,
                failures=[f"Error validating {rule.path}: {str(e)}"],
                warnings=[]
            )

    def _get_value(self, state: Dict[str, Any], path: str) -> Any:
        """Get value from state using JSON path."""
        parts = path.split('.')
        current = state

        for part in parts:
            # Handle array indexing
            match = re.match(r'(.*)\[(\d+)\]', part)
            if match:
                name, index = match.groups()
                current = current.get(name, [])[int(index)]
            else:
                current = current.get(part)

            if current is None:
                break

        return current
