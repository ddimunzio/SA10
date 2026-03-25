"""
Rules Validator - Validate contest rules configuration.

This module validates that contest rules are complete, consistent,
and ready to be used by the rules engine.
"""

from typing import List, Dict, Any, Optional, Tuple
from .rules_loader import ContestRules, ScoringCondition
import re


class RulesValidator:
    """Validate contest rules configuration."""

    def __init__(self, rules: ContestRules):
        """
        Initialize the validator with contest rules.

        Args:
            rules: The contest rules to validate
        """
        self.rules = rules
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """
        Perform complete validation of contest rules.

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        # Run all validation checks
        self._validate_contest_definition()
        self._validate_exchange_format()
        self._validate_scoring_rules()
        self._validate_multipliers()
        self._validate_validation_rules()
        self._validate_reference_data()

        is_valid = len(self.errors) == 0
        return (is_valid, self.errors, self.warnings)

    def _validate_contest_definition(self):
        """Validate basic contest definition."""
        contest = self.rules.contest

        # Check required fields
        if not contest.name:
            self.errors.append("Contest name is required")

        if not contest.slug:
            self.errors.append("Contest slug is required")
        elif not re.match(r'^[a-z0-9_-]+$', contest.slug):
            self.errors.append(
                f"Contest slug '{contest.slug}' contains invalid characters. "
                "Use only lowercase letters, numbers, hyphens, and underscores."
            )

        # Validate bands
        valid_bands = ['160m', '80m', '40m', '20m', '15m', '10m', '6m', '2m', '70cm']
        for band in contest.bands:
            if band not in valid_bands:
                self.warnings.append(
                    f"Band '{band}' is not in standard list: {valid_bands}"
                )

        # Validate modes
        valid_modes = ['CW', 'SSB', 'FM', 'RTTY', 'PSK', 'FT8', 'FT4', 'DIGITAL']
        for mode in contest.modes:
            if mode not in valid_modes:
                self.warnings.append(
                    f"Mode '{mode}' is not in standard list: {valid_modes}"
                )

        # Check duration
        if contest.duration_hours <= 0:
            self.errors.append("Contest duration must be positive")
        elif contest.duration_hours > 48:
            self.warnings.append(
                f"Contest duration of {contest.duration_hours} hours is unusually long"
            )

    def _validate_exchange_format(self):
        """Validate exchange field definitions."""
        # Check sent exchange
        if not self.rules.exchange.sent:
            self.errors.append("Sent exchange must have at least one field")

        # Check received exchange
        if not self.rules.exchange.received:
            self.errors.append("Received exchange must have at least one field")

        # Validate field types
        valid_types = [
            'signal_report', 'zone', 'province', 'state', 'serial',
            'name', 'code', 'grid', 'power', 'custom'
        ]

        for field in self.rules.exchange.sent + self.rules.exchange.received:
            if field.type not in valid_types:
                self.warnings.append(
                    f"Exchange field type '{field.type}' is not standard. "
                    f"Standard types: {valid_types}"
                )

            # Validate pattern if present
            if field.pattern:
                try:
                    re.compile(field.pattern)
                except re.error as e:
                    self.errors.append(
                        f"Invalid regex pattern for field '{field.field}': {e}"
                    )

    def _validate_scoring_rules(self):
        """Validate scoring point rules."""
        if not self.rules.scoring.points:
            self.errors.append("Scoring rules must have at least one point rule")

        # Check for condition types
        valid_condition_types = [
            'same_dxcc', 'different_dxcc', 'same_continent', 'different_continent',
            'operator_continent', 'contact_continent', 'operator_zone', 'contact_zone',
            'callsign_suffix', 'contact_callsign_suffix', 'same_province',
            'different_province', 'same_state', 'different_state'
        ]

        for i, rule in enumerate(self.rules.scoring.points):
            if not rule.conditions:
                self.warnings.append(
                    f"Point rule {i+1} ('{rule.description}') has no conditions"
                )

            for condition in rule.conditions:
                if condition.type not in valid_condition_types:
                    self.warnings.append(
                        f"Condition type '{condition.type}' in rule '{rule.description}' "
                        f"is not standard. Valid types: {valid_condition_types}"
                    )

            # Check point values
            if rule.value < 0:
                self.warnings.append(
                    f"Negative point value in rule '{rule.description}': {rule.value}"
                )

    def _validate_multipliers(self):
        """Validate multiplier definitions."""
        if not self.rules.scoring.multipliers:
            self.warnings.append("No multipliers defined (contest will have only point scoring)")

        valid_mult_types = [
            'wpx_prefix', 'cq_zone', 'itu_zone', 'dxcc', 'province', 'state',
            'grid', 'custom'
        ]

        valid_scopes = ['contest', 'per_band', 'per_mode', 'per_band_mode']

        for mult in self.rules.scoring.multipliers:
            if mult.type not in valid_mult_types:
                self.warnings.append(
                    f"Multiplier type '{mult.type}' is not standard. "
                    f"Valid types: {valid_mult_types}"
                )

            if mult.scope not in valid_scopes:
                self.errors.append(
                    f"Invalid multiplier scope '{mult.scope}'. "
                    f"Valid scopes: {valid_scopes}"
                )

    def _validate_validation_rules(self):
        """Validate validation configuration."""
        # Check duplicate window
        valid_dup_types = ['band_mode', 'band', 'mode', 'contest', 'none']
        dup_type = self.rules.validation.duplicate_window.type

        if dup_type not in valid_dup_types:
            self.errors.append(
                f"Invalid duplicate window type '{dup_type}'. "
                f"Valid types: {valid_dup_types}"
            )

        # Validate exchange format patterns
        if self.rules.validation.exchange_format:
            for field_name, format_def in self.rules.validation.exchange_format.items():
                # Check SSB pattern
                if format_def.ssb_pattern:
                    try:
                        re.compile(format_def.ssb_pattern)
                    except re.error as e:
                        self.errors.append(
                            f"Invalid SSB pattern for '{field_name}': {e}"
                        )

                # Check CW pattern
                if format_def.cw_pattern:
                    try:
                        re.compile(format_def.cw_pattern)
                    except re.error as e:
                        self.errors.append(
                            f"Invalid CW pattern for '{field_name}': {e}"
                        )

                # Check general pattern
                if format_def.pattern:
                    try:
                        re.compile(format_def.pattern)
                    except re.error as e:
                        self.errors.append(
                            f"Invalid pattern for '{field_name}': {e}"
                        )

                # Validate min/max
                if format_def.min is not None and format_def.max is not None:
                    if format_def.min > format_def.max:
                        self.errors.append(
                            f"Invalid range for '{field_name}': min ({format_def.min}) "
                            f"is greater than max ({format_def.max})"
                        )

    def _validate_reference_data(self):
        """Validate reference data if present."""
        if not self.rules.reference_data:
            return

        # Check CQ zones if used
        if 'cq_zones' in self.rules.reference_data:
            zones = self.rules.reference_data['cq_zones']
            if not isinstance(zones, dict):
                self.errors.append("Reference data 'cq_zones' must be a dictionary")
            else:
                for zone_num, zone_name in zones.items():
                    try:
                        z = int(zone_num)
                        if z < 1 or z > 40:
                            self.warnings.append(
                                f"CQ zone {zone_num} is outside valid range (1-40)"
                            )
                    except ValueError:
                        self.errors.append(
                            f"CQ zone key '{zone_num}' must be a valid integer"
                        )

    def validate_exchange_value(
        self,
        field_name: str,
        value: str,
        mode: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a specific exchange value against rules.

        Args:
            field_name: Name of the exchange field
            value: The value to validate
            mode: Contest mode (SSB, CW, etc.)

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.rules.validation.exchange_format:
            return (True, None)

        if field_name not in self.rules.validation.exchange_format:
            return (True, None)

        format_def = self.rules.validation.exchange_format[field_name]

        # Check mode-specific pattern
        pattern = None
        if mode == 'SSB' and format_def.ssb_pattern:
            pattern = format_def.ssb_pattern
        elif mode == 'CW' and format_def.cw_pattern:
            pattern = format_def.cw_pattern
        elif format_def.pattern:
            pattern = format_def.pattern

        if pattern:
            if not re.match(pattern, value):
                return (False, f"Value '{value}' doesn't match pattern for {field_name}")

        # Check numeric range
        if format_def.min is not None or format_def.max is not None:
            try:
                num_value = int(value)
                if format_def.min is not None and num_value < format_def.min:
                    return (False, f"Value {num_value} is below minimum {format_def.min}")
                if format_def.max is not None and num_value > format_def.max:
                    return (False, f"Value {num_value} is above maximum {format_def.max}")
            except ValueError:
                return (False, f"Value '{value}' must be numeric for {field_name}")

        return (True, None)


def validate_contest_rules(rules: ContestRules) -> Dict[str, Any]:
    """
    Convenience function to validate contest rules.

    Args:
        rules: The contest rules to validate

    Returns:
        Dictionary with validation results
    """
    validator = RulesValidator(rules)
    is_valid, errors, warnings = validator.validate()

    return {
        'valid': is_valid,
        'errors': errors,
        'warnings': warnings,
        'error_count': len(errors),
        'warning_count': len(warnings)
    }


if __name__ == '__main__':
    # Test validation with SA10M rules
    from .rules_loader import load_sa10m_rules

    print("Loading SA10M rules...")
    rules = load_sa10m_rules()

    print("Validating rules...")
    validator = RulesValidator(rules)
    is_valid, errors, warnings = validator.validate()

    print(f"\nValidation result: {'✓ VALID' if is_valid else '✗ INVALID'}")

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for error in errors:
            print(f"  ✗ {error}")

    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for warning in warnings:
            print(f"  ⚠ {warning}")

    if is_valid and not warnings:
        print("\n✓ All validations passed!")

    # Test exchange validation
    print("\n--- Testing Exchange Validation ---")
    test_cases = [
        ('cq_zone', '13', 'SSB'),
        ('cq_zone', '99', 'SSB'),
        ('cq_zone', 'ABC', 'SSB'),
        ('rs_rst', '59', 'SSB'),
        ('rs_rst', '599', 'CW'),
        ('rs_rst', '5NN', 'CW'),
    ]

    for field, value, mode in test_cases:
        is_valid, error = validator.validate_exchange_value(field, value, mode)
        status = '✓' if is_valid else '✗'
        result = error if error else 'OK'
        print(f"  {status} {field}='{value}' ({mode}): {result}")

