import pytest

from trunk.services.duration_validator import (
    calculate_complexity_factor,
    format_duration_report,
    get_base_duration,
    validate_audit_duration,
)


class TestDurationValidator:
    def test_get_base_duration_valid(self):
        assert get_base_duration(3) == 3.5
        assert get_base_duration(8) == 6.0
        assert get_base_duration(100) == 21.0
        assert get_base_duration(10000) == 133.0

    def test_get_base_duration_large_org(self):
        # 10500 base is 133.0
        # 12500 is 2000 more -> +14 hours -> 147.0
        assert get_base_duration(12500) == 147.0
        # 12501 is 2001 more -> +28 hours (2 increments) -> 161.0
        assert get_base_duration(12501) == 161.0

    def test_get_base_duration_invalid(self):
        with pytest.raises(ValueError, match="Employee count must be at least 1"):
            get_base_duration(0)

    def test_calculate_complexity_factor_defaults(self):
        factor, reasons = calculate_complexity_factor()
        assert factor == 1.0
        assert "No complexity adjustments applied" in reasons

    def test_calculate_complexity_factor_high_complexity(self):
        factor, reasons = calculate_complexity_factor(
            number_of_sites=5,  # +0.20 (capped at 0.15)
            scope_variation="high",  # +0.10
            process_complexity="complex",  # +0.15
            regulatory_environment="high",  # +0.10
            has_outsourced_processes=True,  # +0.08
            previous_major_ncs=3,  # +0.10
        )
        # Total raw: 1.0 + 0.15 + 0.10 + 0.15 + 0.10 + 0.08 + 0.10 = 1.68
        # Capped at 1.3
        assert factor == 1.3
        assert len(reasons) == 6

    def test_calculate_complexity_factor_low_complexity(self):
        factor, reasons = calculate_complexity_factor(
            process_complexity="simple",  # -0.10
            regulatory_environment="low",  # -0.05
        )
        # Total raw: 1.0 - 0.10 - 0.05 = 0.85
        assert factor == 0.85
        assert len(reasons) == 2

    def test_validate_audit_duration_compliant(self):
        # Base for 100 employees is 21.0
        # No complexity -> 21.0
        result = validate_audit_duration(planned_hours=21.0, employee_count=100)
        assert result["is_valid"] is True
        assert result["severity"] == "compliant"
        assert result["shortfall_hours"] == 0

    def test_validate_audit_duration_warning(self):
        # Base for 100 employees is 21.0
        # Planned 20.0 -> Shortfall 1.0
        result = validate_audit_duration(planned_hours=20.0, employee_count=100)
        assert result["is_valid"] is False
        assert result["severity"] == "warning"
        assert result["shortfall_hours"] == 1.0

    def test_validate_audit_duration_critical(self):
        # Base for 100 employees is 21.0
        # Planned 10.0 -> Shortfall 11.0
        result = validate_audit_duration(planned_hours=10.0, employee_count=100)
        assert result["is_valid"] is False
        assert result["severity"] == "critical"
        assert result["shortfall_hours"] == 11.0

    def test_validate_audit_duration_surveillance(self):
        # Base for 100 employees is 21.0
        # Surveillance factor 0.67 -> 14.07 -> rounded to 14.0
        result = validate_audit_duration(planned_hours=14.0, employee_count=100, is_initial_certification=False)
        assert result["is_valid"] is True
        assert result["required_minimum"] == 14.0

    def test_format_duration_report(self):
        result = validate_audit_duration(planned_hours=21.0, employee_count=100)
        report = format_duration_report(result)
        assert "IAF MD5 AUDIT DURATION VALIDATION REPORT" in report
        assert "COMPLIANT" in report
        assert "Required Minimum: 21.0 hours" in report
