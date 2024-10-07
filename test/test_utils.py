import numpy as np
import pytest

from ..utils import (
    bayes_analysis,
    calculate_sample_size,
    cohen_d_interpretation,
    cohend,
    frequentist_analysis,
    generate_array,
)


# Test generate_array function
def test_generate_array():
    arr = generate_array(10, 5)
    assert len(arr) == 10, "Array length should be 10"
    assert sum(arr) == 5, "The sum of 1s should be 5"

    with pytest.raises(ValueError):
        generate_array(5, 6)  # x > n, should raise ValueError


# Test cohend function
def test_cohend():
    d1 = np.array([1, 2, 3])
    d2 = np.array([2, 3, 4])
    d = cohend(d1, d2)
    assert round(d, 2) == 1.22, "Cohen's d should be around 1.22"


# Test cohen_d_interpretation function
def test_cohen_d_interpretation():
    assert cohen_d_interpretation(0.1) == "Very small effect."
    assert cohen_d_interpretation(0.3) == "Small effect."
    assert cohen_d_interpretation(0.7) == "Medium size effect."
    assert cohen_d_interpretation(1.0) == "Large effect."
    assert cohen_d_interpretation(1.3) == "Very large effect."


# Test bayes_analysis function
def test_bayes_analysis():
    result = bayes_analysis(
        base_suc_rate=10,
        control_group=1000,
        variant_group=1000,
        control_successes=100,
        variant_successes=120,
        lift_percent_desired=5,
    )

    assert "cohen_d" in result
    assert "conf_interval" in result
    assert "perc_improvement" in result
    assert "result_variant_wins_times" in result
    assert "pValueEquivalent" in result


# Test frequentist_analysis function
def test_frequentist_analysis():
    result = frequentist_analysis(
        control_group=1000,
        control_successes=100,
        variant_group=1000,
        variant_successes=120,
        test_type="Two-tailed test",
    )

    assert "reject_null_hypothesis" in result
    assert "p_value" in result
    assert "ci_control" in result
    assert "ci_variant" in result
    assert "lower_bound" in result
    assert "upper_bound" in result


# Test calculate_sample_size function
def test_calculate_sample_size():
    sample_size = calculate_sample_size(
        control_conversion_rate=0.1, minimum_detectable_effect=0.02, alpha=0.05, beta=0.2
    )
    assert isinstance(sample_size, int), "Sample size should be an integer"
    assert sample_size > 0, "Sample size should be greater than 0"


# Run all tests
if __name__ == "__main__":
    pytest.main()
