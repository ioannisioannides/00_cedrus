import pytest

from trunk.services.sampling import calculate_sample_size, validate_site_selection


class TestSampling:
    def test_calculate_sample_size_initial_basic(self):
        # sqrt(5) = 2.23 -> 3
        result = calculate_sample_size(total_sites=5, is_initial_certification=True)
        assert result["minimum_sites"] == 3
        assert result["base_calculation"] == 3
        assert result["risk_adjustment"] == 0
        assert "initial certification" in result["justification"]

    def test_calculate_sample_size_surveillance_basic(self):
        # sqrt(25) = 5. 5 - 0.5 = 4.5 -> 5
        result = calculate_sample_size(total_sites=25, is_initial_certification=False)
        assert result["minimum_sites"] == 5
        assert result["base_calculation"] == 5

        # sqrt(5) = 2.23. 2.23 - 0.5 = 1.73 -> 2
        result = calculate_sample_size(total_sites=5, is_initial_certification=False)
        assert result["minimum_sites"] == 2

    def test_calculate_sample_size_surveillance_min_one(self):
        # sqrt(1) = 1. 1 - 0.5 = 0.5 -> 1
        result = calculate_sample_size(total_sites=1, is_initial_certification=False)
        assert result["minimum_sites"] == 1

    def test_calculate_sample_size_invalid(self):
        with pytest.raises(ValueError, match="Total sites must be at least 1"):
            calculate_sample_size(total_sites=0)

    def test_calculate_sample_size_risk_adjustments(self):
        # Base: sqrt(100) = 10 (initial)
        # High risk: 10 sites -> +ceil(10/5) = +2
        # Previous findings: 4 (>3) -> +ceil(10*0.2) = +2
        # Scope variation: high -> +2
        # Total: 10 + 2 + 2 + 2 = 16
        result = calculate_sample_size(
            total_sites=100,
            high_risk_sites=10,
            previous_findings_count=4,
            scope_variation="high",
            is_initial_certification=True,
        )
        assert result["base_calculation"] == 10
        assert result["risk_adjustment"] == 6
        assert result["minimum_sites"] == 16
        assert len(result["risk_factors"]) == 3

    def test_calculate_sample_size_moderate_scope(self):
        # Base: sqrt(100) = 10
        # Moderate scope -> +1
        result = calculate_sample_size(
            total_sites=100,
            scope_variation="moderate",
            is_initial_certification=True,
        )
        assert result["minimum_sites"] == 11
        assert result["risk_adjustment"] == 1

    def test_calculate_sample_size_capped_at_total(self):
        # Base: sqrt(5) = 3
        # High risk: 20 sites (impossible but for math) -> +4
        # Total calc: 7. But total sites is 5.
        result = calculate_sample_size(
            total_sites=5,
            high_risk_sites=20,
            is_initial_certification=True,
        )
        assert result["minimum_sites"] == 5

    def test_validate_site_selection_valid(self):
        result = validate_site_selection(selected_sites=5, required_minimum=5, total_sites=10)
        assert result["is_valid"] is True
        assert result["shortfall"] == 0

    def test_validate_site_selection_shortfall(self):
        result = validate_site_selection(selected_sites=4, required_minimum=5, total_sites=10)
        assert result["is_valid"] is False
        assert result["shortfall"] == 1
        assert "Need 1 more site" in result["message"]

    def test_validate_site_selection_too_many(self):
        result = validate_site_selection(selected_sites=11, required_minimum=5, total_sites=10)
        assert result["is_valid"] is False
        assert "Cannot audit 11 sites" in result["message"]
