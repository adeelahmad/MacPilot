from typing import Dict, Any, List, Optional, Tuple
from pydantic import Field
from dataclasses import dataclass
from enum import Enum
import logging

from automation_framework.services.shared.serialization import recursive_dict_conversion

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    STRICT = "strict"
    NORMAL = "normal"
    LENIENT = "lenient"


@dataclass
class ValidationRule:
    """Rule for state validation."""
    path: str
    condition: str
    expected_value: Any
    level: ValidationLevel = ValidationLevel.NORMAL
    message: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of validation check."""
    success: bool
    failures: List[str] = Field(default_factory=list)  # Initialize as empty list
    warnings: List[str] = Field(default_factory=list)  # Initialize as empty list
    validation_time: float = 0.0
    details: Dict[str, Any] = Field(default_factory=dict)


class StateValidator:
    """Validates UI states with configurable rules."""

    def __init__(self, default_level: ValidationLevel = ValidationLevel.NORMAL):
        self.default_level = default_level
        self.rules: List[ValidationRule] = []

    def add_rule(self, rule: ValidationRule):
        """Add validation rule."""
        self.rules.append(rule)

    def clear_rules(self):
        """Clear all validation rules."""
        self.rules.clear()


    def validate_state(self, current_state: Dict[str, Any], expected_state: Dict[str, Any]) -> ValidationResult:
        """Validate current state against expected state."""
        failures = []
        warnings = []

        try:
            # Convert states if needed
            current = recursive_dict_conversion(current_state)
            expected = recursive_dict_conversion(expected_state)

            # Validate basic structure
            for key in expected:
                if key not in current:
                    failures.append(f"Missing key: {key}")
                    continue

                current_value = current[key]
                expected_value = expected[key]

                if isinstance(expected_value, dict):
                    if not isinstance(current_value, dict):
                        failures.append(f"Type mismatch for {key}")
                    else:
                        # Recursive validation for nested structures
                        nested_result = self.validate_state(current_value, expected_value)
                        failures.extend(nested_result.failures)
                        warnings.extend(nested_result.warnings)

            return ValidationResult(
                success=len(failures) == 0,
                failures=failures,
                warnings=warnings
            )

        except Exception as e:
            logger.error(f"Validation error: {e}")
            return ValidationResult(
                success=False,
                failures=[f"Validation error: {str(e)}"],
                warnings=[]
            )


    def _check_rule(self, state: Dict[str, Any],
                    rule: ValidationRule) -> ValidationResult:
        """Check single validation rule."""
        try:
            # Get actual value using path
            actual_value = self._get_nested_value(state, rule.path)

            if actual_value is None:
                return ValidationResult(
                    success=False,
                    failures=[f"Path {rule.path} not found"],
                    warnings=[],
                    validation_time=0,
                    details={'missing_path': rule.path}
                )

            # Apply condition
            success = False
            message = ""

            if rule.condition == "equals":
                success = actual_value == rule.expected_value
                message = f"Expected {rule.expected_value}, got {actual_value}"
            elif rule.condition == "contains":
                success = rule.expected_value in actual_value
                message = f"Expected to contain {rule.expected_value}"
            elif rule.condition == "greater_than":
                success = actual_value > rule.expected_value
                message = f"Expected > {rule.expected_value}, got {actual_value}"
            elif rule.condition == "less_than":
                success = actual_value < rule.expected_value
                message = f"Expected < {rule.expected_value}, got {actual_value}"
            elif rule.condition == "type":
                success = isinstance(actual_value, rule.expected_value)
                message = f"Expected type {rule.expected_value.__name__}"
            else:
                raise ValueError(f"Unknown condition: {rule.condition}")

            return ValidationResult(
                success=success,
                failures=[] if success else [message],
                warnings=[],
                validation_time=0,
                details={
                    'actual_value': actual_value,
                    'expected_value': rule.expected_value,
                    'condition': rule.condition
                }
            )

        except Exception as e:
            logger.error(f"Error checking rule: {e}")
            return ValidationResult(
                success=False,
                failures=[f"Rule check error: {str(e)}"],
                warnings=[],
                validation_time=0,
                details={'error': str(e)}
            )

    def _validate_expected_state(self, current: Dict[str, Any],
                                 expected: Dict[str, Any]) -> ValidationResult:
        """Validate current state against expected state."""
        failures = []
        warnings = []
        details = {}

        try:
            for key, expected_value in expected.items():
                if key not in current:
                    failures.append(f"Missing key: {key}")
                    continue

                current_value = current[key]

                if isinstance(expected_value, dict):
                    if not isinstance(current_value, dict):
                        failures.append(
                            f"Type mismatch for {key}: "
                            f"expected dict, got {type(current_value)}"
                        )
                    else:
                        result = self._validate_expected_state(
                            current_value,
                            expected_value
                        )
                        failures.extend(result.failures)
                        warnings.extend(result.warnings)
                        details[key] = result.details

                elif isinstance(expected_value, (list, tuple)):
                    if not isinstance(current_value, (list, tuple)):
                        failures.append(
                            f"Type mismatch for {key}: "
                            f"expected list/tuple, got {type(current_value)}"
                        )
                    else:
                        result = self._validate_lists(current_value, expected_value)
                        failures.extend(result.failures)
                        warnings.extend(result.warnings)
                        details[key] = result.details

                elif current_value != expected_value:
                    failures.append(
                        f"Value mismatch for {key}: "
                        f"expected {expected_value}, got {current_value}"
                    )

            return ValidationResult(
                success=len(failures) == 0,
                failures=failures,
                warnings=warnings,
                validation_time=0,
                details=details
            )

        except Exception as e:
            logger.error(f"Error validating expected state: {e}")
            return ValidationResult(
                success=False,
                failures=[f"Validation error: {str(e)}"],
                warnings=[],
                validation_time=0,
                details={'error': str(e)}
            )

    def _validate_lists(self, current: List[Any],
                        expected: List[Any]) -> ValidationResult:
        """Validate lists of values."""
        failures = []
        warnings = []
        details = {}

        try:
            if len(current) != len(expected):
                failures.append(
                    f"List length mismatch: "
                    f"expected {len(expected)}, got {len(current)}"
                )

            for i, (curr_item, exp_item) in enumerate(zip(current, expected)):
                if isinstance(exp_item, dict):
                    if not isinstance(curr_item, dict):
                        failures.append(
                            f"Type mismatch at index {i}: "
                            f"expected dict, got {type(curr_item)}"
                        )
                    else:
                        result = self._validate_expected_state(curr_item, exp_item)
                        failures.extend(result.failures)
                        warnings.extend(result.warnings)
                        details[f'item_{i}'] = result.details

                elif isinstance(exp_item, (list, tuple)):
                    if not isinstance(curr_item, (list, tuple)):
                        failures.append(
                            f"Type mismatch at index {i}: "
                            f"expected list/tuple, got {type(curr_item)}"
                        )
                    else:
                        result = self._validate_lists(curr_item, exp_item)
                        failures.extend(result.failures)
                        warnings.extend(result.warnings)
                        details[f'item_{i}'] = result.details

                elif curr_item != exp_item:
                    failures.append(
                        f"Value mismatch at index {i}: "
                        f"expected {exp_item}, got {curr_item}"
                    )

            return ValidationResult(
                success=len(failures) == 0,
                failures=failures,
                warnings=warnings,
                validation_time=0,
                details=details
            )

        except Exception as e:
            logger.error(f"Error validating lists: {e}")
            return ValidationResult(
                success=False,
                failures=[f"List validation error: {str(e)}"],
                warnings=[],
                validation_time=0,
                details={'error': str(e)}
            )

    def _get_nested_value(self, obj: Dict[str, Any], path: str) -> Any:
        """Get nested dictionary value using dot notation."""
        try:
            current = obj
            for part in path.split('.'):
                if isinstance(current, dict):
                    if part not in current:
                        return None
                    current = current[part]
                else:
                    return None
            return current
        except Exception as e:
            logger.error(f"Error getting nested value: {e}")
            return None
