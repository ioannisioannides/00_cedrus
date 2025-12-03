"""
IAF MD1 Multi-Site Sampling Algorithm

Implements the minimum sampling requirements for multi-site organizations
as defined in IAF Mandatory Document 1 (IAF MD1) Annex A.

Reference: IAF MD1:2018 - Audit and Certification of a Management System
Operated by an Organization with Multiple Sites
"""

import math
from typing import Any, Dict, List, Tuple


def calculate_sample_size(
    total_sites: int,
    high_risk_sites: int = 0,
    previous_findings_count: int = 0,
    is_initial_certification: bool = True,
    scope_variation: str = "uniform",  # "uniform", "moderate", "high"
) -> Dict[str, Any]:
    """
    Calculate minimum sample size for multi-site audit per IAF MD1 Annex A.

    IAF MD1 Formula:
    - For initial certification: y = √x (where x = total sites)
    - For surveillance: y = √x - 0.5 (minimum 1 site)
    - Always round up to next integer
    - Additional sites added based on risk factors

    Args:
        total_sites: Total number of sites in the organization
        high_risk_sites: Number of sites identified as high risk
        previous_findings_count: Number of major NCs from previous audit cycle
        is_initial_certification: True for Stage 1/2, False for surveillance
        scope_variation: Degree of scope variation across sites

    Returns:
        Dictionary containing:
        - minimum_sites: Minimum number of sites to audit
        - base_calculation: Base sample from IAF MD1 formula
        - risk_adjustment: Additional sites due to risk factors
        - justification: Detailed explanation of the calculation
        - risk_factors: List of identified risk factors
        - recommended_sites: List of site selection recommendations

    Raises:
        ValueError: If total_sites < 1
    """
    if total_sites < 1:
        raise ValueError("Total sites must be at least 1")

    # IAF MD1 base calculation
    if is_initial_certification:
        # Stage 1 and Stage 2: y = √x
        base_sample = math.ceil(math.sqrt(total_sites))
    else:
        # Surveillance audits: y = √x - 0.5 (minimum 1)
        base_sample = max(1, math.ceil(math.sqrt(total_sites) - 0.5))

    # Risk-based adjustments
    risk_adjustment, risk_factors = _calculate_risk_adjustments(
        base_sample, high_risk_sites, previous_findings_count, scope_variation
    )

    # Calculate final minimum
    minimum_sites = min(base_sample + risk_adjustment, total_sites)

    # Build justification text
    audit_type = "initial certification" if is_initial_certification else "surveillance"
    justification_parts = [
        f"IAF MD1 calculation for {audit_type} audit:",
        f"- Total sites in organization: {total_sites}",
        f"- Base sample (IAF MD1 formula): {base_sample}",
    ]

    if risk_adjustment > 0:
        justification_parts.append(f"- Risk-based adjustment: +{risk_adjustment} sites")
        for factor in risk_factors:
            justification_parts.append(f"  • {factor}")
    else:
        justification_parts.append("- No risk-based adjustments required")

    justification_parts.append(f"\nMinimum sites to audit: {minimum_sites} of {total_sites}")

    # Sampling recommendations
    recommendations = [
        "Always include the central office/head office",
        "Select sites representing all significant scope variations",
        "Prioritize sites with high-risk activities",
        "Include sites with previous nonconformities",
    ]

    if total_sites > minimum_sites:
        coverage_percent = (minimum_sites / total_sites) * 100
        recommendations.append(f"This sample covers {coverage_percent:.1f}% of total sites")

    if is_initial_certification:
        recommendations.append("Stage 1 and Stage 2 must audit the SAME selected sites (IAF MD1 requirement)")

    return {
        "minimum_sites": minimum_sites,
        "base_calculation": base_sample,
        "risk_adjustment": risk_adjustment,
        "justification": "\n".join(justification_parts),
        "risk_factors": risk_factors,
        "recommended_sites": recommendations,
        "coverage_percentage": (minimum_sites / total_sites) * 100,
        "audit_type": audit_type,
    }


def _calculate_risk_adjustments(
    base_sample: int, high_risk_sites: int, previous_findings_count: int, scope_variation: str
) -> Tuple[int, List[str]]:
    """
    Compute additional site-count adjustments and explanatory messages based on identified risks.
    
    Parameters:
        base_sample (int): Base MD1 sample count used as the reference for percentage-based adjustments.
        high_risk_sites (int): Number of sites classified as high risk.
        previous_findings_count (int): Number of previous major nonconformities.
        scope_variation (str): Scope variation level across sites; expected values include "uniform", "moderate", or "high".
    
    Returns:
        risk_adjustment (int): Total number of additional sites to add to the base sample.
        risk_factors (List[str]): Human-readable descriptions explaining each applied adjustment.
    """
    risk_adjustment = 0
    risk_factors = []

    # Factor 1: High-risk sites (add 1 site per 5 high-risk sites)
    if high_risk_sites > 0:
        high_risk_addition = math.ceil(high_risk_sites / 5)
        risk_adjustment += high_risk_addition
        risk_factors.append(
            f"High-risk sites: {high_risk_sites} sites identified, adding {high_risk_addition} to sample"
        )

    # Factor 2: Previous major nonconformities (add 20% if >3 major NCs)
    if previous_findings_count > 3:
        nc_addition = math.ceil(base_sample * 0.2)
        risk_adjustment += nc_addition
        risk_factors.append(
            f"Previous major NCs: {previous_findings_count} found, adding {nc_addition} sites (20% increase)"
        )

    # Factor 3: High scope variation (add 1-2 sites)
    if scope_variation == "high":
        variation_addition = 2
        risk_adjustment += variation_addition
        risk_factors.append(
            f"High scope variation across sites, adding {variation_addition} sites for representative coverage"
        )
    elif scope_variation == "moderate":
        variation_addition = 1
        risk_adjustment += variation_addition
        risk_factors.append(f"Moderate scope variation, adding {variation_addition} site")

    return risk_adjustment, risk_factors


def validate_site_selection(selected_sites: int, required_minimum: int, total_sites: int) -> Dict[str, Any]:
    """
    Validate that site selection meets IAF MD1 requirements.

    Args:
        selected_sites: Number of sites selected for audit
        required_minimum: Minimum required by IAF MD1 calculation
        total_sites: Total number of sites

    Returns:
        Dictionary with validation results:
        - is_valid: True if selection meets requirements
        - message: Explanation of validation result
        - shortfall: Number of additional sites needed (if invalid)
    """
    if selected_sites < required_minimum:
        shortfall = required_minimum - selected_sites
        return {
            "is_valid": False,
            "message": (
                f"Site selection does not meet IAF MD1 minimum requirements. "
                f"Selected {selected_sites} sites, but minimum is {required_minimum}. "
                f"Need {shortfall} more site(s)."
            ),
            "shortfall": shortfall,
        }

    if selected_sites > total_sites:
        return {
            "is_valid": False,
            "message": (
                f"Invalid selection: Cannot audit {selected_sites} sites "
                f"when organization only has {total_sites} sites."
            ),
            "shortfall": 0,
        }

    return {
        "is_valid": True,
        "message": f"Site selection is valid: {selected_sites} sites meets minimum of {required_minimum}.",
        "shortfall": 0,
    }


# Example usage and reference data
SAMPLING_EXAMPLES = {
    "small_org": {
        "description": "Small organization with 5 sites, initial certification",
        "parameters": {
            "total_sites": 5,
            "is_initial_certification": True,
        },
        "expected_result": {
            "minimum_sites": 3,  # √5 = 2.24, round up to 3
            "note": "Must audit 3 out of 5 sites for Stage 1 and Stage 2",
        },
    },
    "medium_org": {
        "description": "Medium organization with 25 sites, surveillance",
        "parameters": {
            "total_sites": 25,
            "is_initial_certification": False,
        },
        "expected_result": {
            "minimum_sites": 5,  # √25 - 0.5 = 4.5, round up to 5
            "note": "Surveillance audit requires 5 out of 25 sites",
        },
    },
    "large_org_high_risk": {
        "description": "Large organization with 100 sites, 10 high-risk sites, surveillance",
        "parameters": {
            "total_sites": 100,
            "high_risk_sites": 10,
            "is_initial_certification": False,
        },
        "expected_result": {
            "minimum_sites": 12,  # √100 - 0.5 = 9.5 → 10, + 2 for high-risk
            "note": "Base 10 sites + 2 additional for high-risk sites",
        },
    },
}