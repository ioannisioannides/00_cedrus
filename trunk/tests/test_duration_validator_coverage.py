from unittest.mock import patch

import pytest

from trunk.services.duration_validator import (
    IAF_MD5_QMS_BASE_DURATIONS,
    calculate_complexity_factor,
    format_duration_report,
    get_base_duration,
    validate_audit_duration,
)


class TestDurationValidatorCoverage:
    def test_get_base_duration_not_found(self):
        """Test get_base_duration raises ValueError when employee count not in table."""
        # Mock the table to have a gap
        with patch.dict(IAF_MD5_QMS_BASE_DURATIONS, {}, clear=True):
            # Add only one entry
            IAF_MD5_QMS_BASE_DURATIONS[(1, 5)] = 3.5

            # Test with employee count not in table
            with pytest.raises(ValueError, match="No base duration found"):
                get_base_duration(10)

    def test_calculate_complexity_factor_moderate_scope(self):
        """Test complexity factor with moderate scope variation."""
        factor, reasons = calculate_complexity_factor(scope_variation="moderate")
        assert factor == 1.05
        assert "Moderate scope variation: +5%" in reasons

    @patch("trunk.services.duration_validator.get_base_duration")
    def test_validate_audit_duration_zero_minimum(self, mock_get_base):
        """Test validation when required minimum is 0 (should handle division by zero)."""
        mock_get_base.return_value = 0.0

        # This should result in required_minimum = 0
        result = validate_audit_duration(employee_count=10, planned_hours=8.0, is_initial_certification=True)

        assert result["required_minimum"] == 0
        assert result["percentage_difference"] == 0

    def test_validate_audit_duration_exceeds_minimum(self):
        """Test validation when planned duration significantly exceeds minimum."""
        # Base for 10 employees is 6.0 hours
        # Initial certification adds 0% (factor 1.0)
        # Planned 10 hours > 6.0 * 1.1 (6.6)

        result = validate_audit_duration(employee_count=10, planned_hours=10.0, is_initial_certification=True)

        assert result["is_valid"] is True
        assert "exceeds IAF MD5 minimum" in result["recommendation"]

    def test_format_duration_report_invalid(self):
        """Test formatting report for invalid result."""
        result = {
            "audit_type": "Initial Certification",
            "standard": "ISO 9001",
            "employee_count": 10,
            "base_duration": 6.0,
            "complexity_factor": 1.0,
            "adjustment_reasons": [],
            "required_minimum": 6.0,
            "planned_hours": 4.0,
            "is_valid": False,
            "recommendation": "Increase duration",
        }

        report = format_duration_report(result)
        assert "✗ NON-COMPLIANT" in report
