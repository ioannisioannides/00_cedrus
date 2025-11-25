"""
IAF MD5 Audit Duration Validation

Implements the minimum audit duration requirements as defined in
IAF Mandatory Document 5 (IAF MD5) - Duration of QMS and EMS Audits.

Reference: IAF MD5:2019 - Duration of Quality and Environmental
Management Systems Audits
"""

from typing import Any, Dict, List, Tuple

# IAF MD5 base duration tables (in hours)
# These are starting points that must be adjusted based on various factors

IAF_MD5_QMS_BASE_DURATIONS = {
    # Employee count ranges and base audit hours for ISO 9001
    # Format: (min_employees, max_employees): base_hours
    (1, 5): 3.5,
    (6, 10): 6.0,
    (11, 15): 8.0,
    (16, 25): 10.0,
    (26, 45): 12.5,
    (46, 65): 16.0,
    (66, 85): 18.0,
    (86, 125): 21.0,
    (126, 175): 24.0,
    (176, 275): 29.0,
    (276, 425): 35.0,
    (426, 625): 42.0,
    (626, 875): 49.0,
    (876, 1175): 56.0,
    (1176, 1550): 63.0,
    (1551, 2025): 70.0,
    (2026, 2675): 77.0,
    (2676, 3450): 84.0,
    (3451, 4350): 91.0,
    (4351, 5450): 98.0,
    (5451, 6800): 105.0,
    (6801, 8500): 119.0,
    (8501, 10500): 133.0,
    # For >10500 employees, add 14 hours per additional 2000 employees
}


def get_base_duration(employee_count: int, standard_code: str = "ISO 9001") -> float:
    """
    Get base audit duration from IAF MD5 tables.

    Args:
        employee_count: Number of employees in scope
        standard_code: Standard being audited (currently only ISO 9001 implemented)

    Returns:
        Base audit hours from IAF MD5 table

    Raises:
        ValueError: If employee_count < 1
    """
    if employee_count < 1:
        raise ValueError("Employee count must be at least 1")

    # Handle very large organizations (>10,500 employees)
    if employee_count > 10500:
        base_for_10500 = 133.0
        additional_employees = employee_count - 10500
        additional_increments = (additional_employees + 1999) // 2000  # Round up
        return base_for_10500 + (additional_increments * 14.0)

    # Find applicable range in table
    for (min_emp, max_emp), base_hours in IAF_MD5_QMS_BASE_DURATIONS.items():
        if min_emp <= employee_count <= max_emp:
            return base_hours

    # Should not reach here if table is complete
    raise ValueError(f"No base duration found for {employee_count} employees")


def calculate_complexity_factor(
    number_of_sites: int = 1,
    scope_variation: str = "uniform",  # uniform, moderate, high
    process_complexity: str = "standard",  # simple, standard, complex
    regulatory_environment: str = "standard",  # low, standard, high
    has_outsourced_processes: bool = False,
    previous_major_ncs: int = 0,
) -> Tuple[float, List[str]]:
    """
    Calculate complexity adjustment factor per IAF MD5 Section 4.

    IAF MD5 requires consideration of:
    - Complexity of the organization
    - Number and significance of processes
    - Sites and multi-site considerations
    - Level of regulatory requirements
    - Outsourced processes
    - Results of previous audits

    Args:
        number_of_sites: Number of sites to audit
        scope_variation: Degree of scope variation
        process_complexity: Complexity of processes
        regulatory_environment: Level of regulatory requirements
        has_outsourced_processes: Whether organization outsources key processes
        previous_major_ncs: Count of major NCs from previous audit

    Returns:
        Tuple of (adjustment_factor, list_of_reasons)
        adjustment_factor: Multiplier to apply to base duration (0.8 - 1.3)
        list_of_reasons: Explanations for adjustments
    """
    adjustment = 1.0
    reasons = []

    # Multi-site adjustment
    if number_of_sites > 1:
        site_factor = 0.05 * (number_of_sites - 1)  # 5% per additional site
        site_factor = min(site_factor, 0.15)  # Cap at 15% increase
        adjustment += site_factor
        reasons.append(f"Multi-site organization: +{site_factor*100:.1f}% " f"({number_of_sites} sites being audited)")

    # Scope variation adjustment
    if scope_variation == "high":
        adjustment += 0.10
        reasons.append("High scope variation: +10%")
    elif scope_variation == "moderate":
        adjustment += 0.05
        reasons.append("Moderate scope variation: +5%")

    # Process complexity adjustment
    if process_complexity == "complex":
        adjustment += 0.15
        reasons.append("Complex processes: +15%")
    elif process_complexity == "simple":
        adjustment -= 0.10
        reasons.append("Simple processes: -10%")

    # Regulatory environment adjustment
    if regulatory_environment == "high":
        adjustment += 0.10
        reasons.append("High regulatory requirements: +10%")
    elif regulatory_environment == "low":
        adjustment -= 0.05
        reasons.append("Low regulatory requirements: -5%")

    # Outsourced processes
    if has_outsourced_processes:
        adjustment += 0.08
        reasons.append("Outsourced processes require additional verification: +8%")

    # Previous audit results
    if previous_major_ncs >= 3:
        nc_factor = 0.10
        adjustment += nc_factor
        reasons.append(f"Previous major NCs ({previous_major_ncs}): +{nc_factor*100:.1f}% " "for enhanced verification")

    # Apply limits: IAF MD5 allows ±20% adjustment typically
    adjustment = max(0.8, min(1.3, adjustment))

    if adjustment == 1.0:
        reasons.append("No complexity adjustments applied")

    return adjustment, reasons


def validate_audit_duration(
    planned_hours: float,
    employee_count: int,
    standard_code: str = "ISO 9001",
    is_initial_certification: bool = True,
    number_of_sites: int = 1,
    scope_variation: str = "uniform",
    process_complexity: str = "standard",
    regulatory_environment: str = "standard",
    has_outsourced_processes: bool = False,
    previous_major_ncs: int = 0,
) -> Dict[str, Any]:
    """
    Validate whether planned audit duration meets IAF MD5 minimum requirements.

    Args:
        planned_hours: Planned audit duration in hours
        employee_count: Number of employees in scope
        standard_code: Standard being audited
        is_initial_certification: True for Stage 1/2, False for surveillance
        number_of_sites: Number of sites being audited
        scope_variation: Degree of scope variation across sites
        process_complexity: Complexity level of organization's processes
        regulatory_environment: Level of regulatory requirements
        has_outsourced_processes: Whether key processes are outsourced
        previous_major_ncs: Count of major NCs from previous audit

    Returns:
        Dictionary containing:
        - is_valid: True if planned duration meets minimum
        - required_minimum: Minimum hours required by IAF MD5
        - planned_hours: Hours currently planned
        - shortfall_hours: Hours below minimum (0 if valid)
        - base_duration: Base hours from IAF MD5 table
        - complexity_factor: Adjustment factor applied
        - adjustment_reasons: List of reasons for adjustments
        - recommendation: Text recommendation for auditor
        - severity: "compliant", "warning", or "critical"
    """
    # Get base duration from IAF MD5 tables
    base_duration = get_base_duration(employee_count, standard_code)

    # Calculate complexity adjustments
    complexity_factor, adjustment_reasons = calculate_complexity_factor(
        number_of_sites=number_of_sites,
        scope_variation=scope_variation,
        process_complexity=process_complexity,
        regulatory_environment=regulatory_environment,
        has_outsourced_processes=has_outsourced_processes,
        previous_major_ncs=previous_major_ncs,
    )

    # Calculate adjusted minimum
    adjusted_minimum = base_duration * complexity_factor

    # For surveillance audits, IAF MD5 allows reduction (typically 2/3 of initial)
    if not is_initial_certification:
        surveillance_factor = 0.67
        adjusted_minimum = adjusted_minimum * surveillance_factor
        adjustment_reasons.append(
            f"Surveillance audit: Apply {surveillance_factor*100:.0f}% factor " f"(IAF MD5 Section 5.2)"
        )

    # Round to 0.5 hour increments
    required_minimum = round(adjusted_minimum * 2) / 2

    # Determine validation result
    shortfall = max(0, required_minimum - planned_hours)
    is_valid = shortfall == 0

    # Calculate percentage difference
    if required_minimum > 0:
        percentage_diff = ((planned_hours - required_minimum) / required_minimum) * 100
    else:
        percentage_diff = 0

    # Determine severity
    if is_valid:
        if percentage_diff >= 10:
            severity = "compliant"
            recommendation = (
                f"Planned duration ({planned_hours} hours) exceeds IAF MD5 minimum "
                f"by {percentage_diff:.1f}%. This provides good audit coverage."
            )
        else:
            severity = "compliant"
            recommendation = (
                f"Planned duration ({planned_hours} hours) meets IAF MD5 minimum "
                f"requirements. Consider if additional time is needed for thorough coverage."
            )
    else:
        if shortfall <= 2:
            severity = "warning"
            recommendation = (
                f"⚠️ WARNING: Planned duration is {shortfall} hours below IAF MD5 minimum. "
                f"Additional justification required. Consider extending audit duration."
            )
        else:
            severity = "critical"
            recommendation = (
                f"❌ CRITICAL: Planned duration is {shortfall} hours below IAF MD5 minimum. "
                f"This audit plan does NOT meet accreditation requirements. "
                f"Duration must be increased to at least {required_minimum} hours."
            )

    audit_type = "Initial Certification" if is_initial_certification else "Surveillance"

    return {
        "is_valid": is_valid,
        "required_minimum": required_minimum,
        "planned_hours": planned_hours,
        "shortfall_hours": shortfall,
        "base_duration": base_duration,
        "complexity_factor": complexity_factor,
        "adjustment_reasons": adjustment_reasons,
        "recommendation": recommendation,
        "severity": severity,
        "audit_type": audit_type,
        "percentage_difference": percentage_diff,
        "employee_count": employee_count,
        "standard": standard_code,
    }


def format_duration_report(validation_result: Dict[str, Any]) -> str:
    """
    Format validation result as human-readable report.

    Args:
        validation_result: Result from validate_audit_duration()

    Returns:
        Formatted text report
    """
    result = validation_result

    report_lines = [
        "=" * 70,
        "IAF MD5 AUDIT DURATION VALIDATION REPORT",
        "=" * 70,
        "",
        f"Audit Type: {result['audit_type']}",
        f"Standard: {result['standard']}",
        f"Employees in Scope: {result['employee_count']}",
        "",
        "DURATION CALCULATION:",
        "-" * 70,
        f"IAF MD5 Base Duration: {result['base_duration']} hours",
        f"Complexity Factor: {result['complexity_factor']:.2f}x",
        "",
        "Adjustment Factors:",
    ]

    for reason in result["adjustment_reasons"]:
        report_lines.append(f"  • {reason}")

    report_lines.extend(
        [
            "",
            f"Required Minimum: {result['required_minimum']} hours",
            f"Planned Duration: {result['planned_hours']} hours",
            "",
            "VALIDATION RESULT:",
            "-" * 70,
        ]
    )

    if result["is_valid"]:
        report_lines.append(f"✓ COMPLIANT - {result['recommendation']}")
    else:
        report_lines.append(f"✗ NON-COMPLIANT - {result['recommendation']}")

    report_lines.append("=" * 70)

    return "\n".join(report_lines)


# Example validation scenarios for reference
VALIDATION_EXAMPLES = {
    "small_company_valid": {
        "description": "Small company (15 employees), adequate duration",
        "parameters": {
            "planned_hours": 8.0,
            "employee_count": 15,
            "is_initial_certification": True,
        },
        "expected": "Compliant - meets IAF MD5 minimum of 8.0 hours",
    },
    "medium_company_insufficient": {
        "description": "Medium company (100 employees), insufficient duration",
        "parameters": {
            "planned_hours": 16.0,
            "employee_count": 100,
            "is_initial_certification": True,
        },
        "expected": "Non-compliant - requires ~20.0 hours minimum",
    },
    "complex_multisite": {
        "description": "Complex multi-site organization with high regulatory requirements",
        "parameters": {
            "planned_hours": 35.0,
            "employee_count": 200,
            "number_of_sites": 3,
            "process_complexity": "complex",
            "regulatory_environment": "high",
            "is_initial_certification": True,
        },
        "expected": "May be insufficient due to complexity factors",
    },
}
