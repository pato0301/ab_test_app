import random

import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats
import statsmodels.api as sm
from scipy.stats import beta, norm
from statsmodels.stats.power import TTestIndPower, tt_ind_solve_power
from statsmodels.stats.proportion import (
    confint_proportions_2indep,
    proportions_chisquare,
    proportions_ztest,
)
from statsmodels.stats.weightstats import ttest_ind

# Now lets simulate with monte carlos
N_TRIALS = 100000
# Set the significance level
ALPHA = 0.05

ALTERNATIVE_MAPPING = {
    "Two-tailed test": "two-sided",
    "One-tailed test (less)": "smaller",
    "One-tailed test (greater)": "larger",
}


def generate_array(n, x):
    """
    Generates an array of 0s and 1s of length n with x number of 1s inside.
    """
    # Ensure x is less than or equal to n.
    if x > n:
        raise ValueError("x cannot be greater than n")

    # Create an array of n 0s.
    arr = [0] * n

    # Choose x indices randomly and set their values to 1.
    indices = random.sample(range(n), x)
    for i in indices:
        arr[i] = 1

    return arr


def cohend(d1, d2, equal_sample=True):
    # calculate the size of samples
    n1, n2 = len(d1), len(d2)
    if equal_sample:
        # calculate the variance of the samples
        s1, s2 = np.var(d1), np.var(d2)
        # calculate the pooled standard deviation
        s = np.sqrt((s1 + s2) / 2)
    else:
        # calculate the variance of the samples
        s1, s2 = np.var(d1, ddof=1), np.var(d2, ddof=1)
        # calculate the pooled standard deviation
        s = np.sqrt(((n1 - 1) * s1 + (n2 - 1) * s2) / (n1 + n2 - 2))

    # calculate the means of the samples
    u1, u2 = np.mean(d1), np.mean(d2)
    # calculate the effect size
    return abs((u1 - u2) / s)


def cohen_d_interpretation(d):
    if d < 0.2:
        return "Very small effect."
    elif d < 0.5:
        return "Small effect."
    elif d < 0.8:
        return "Medium size effect."
    elif d < 1.2:
        return "Large effect."
    else:
        return "Very large effect."


def sample_ratio_mismatch(control_group_observations, variant_group_observations, percent_of_variant, srm_alpha):
    observed = np.array([control_group_observations, variant_group_observations])
    total_observed = control_group_observations + variant_group_observations
    expected_control = total_observed * (1 - percent_of_variant)
    expected_variant = total_observed * percent_of_variant
    expected = np.array([expected_control, expected_variant])

    print("expected: ", expected)
    print("observed: ", observed)
    # perform Chi-Square Goodness of Fit Test
    chi_stats, pvalue = stats.chisquare(f_obs=observed, f_exp=expected)

    if pvalue < srm_alpha:
        return "Reject Ho and conclude that there is statistical significance in the ratio of samples Therefore, there is SRM."
    else:
        return "Fail to reject Ho. Therefore, there is no SRM."


def chi_squared_test(control_group, control_successes, variant_group, variant_successes, alpha):
    # Execute chi-squared test
    AB_chistats, AB_pvalue, _ = proportions_chisquare(
        [control_successes, variant_successes], nobs=[control_group, variant_group]
    )

    if AB_pvalue < alpha:
        return "Reject Ho: There is a statistically significant difference between the control and variant groups."
    else:
        return "Fail to reject Ho: No statistical significance found."


def frequentist_analysis(
    control_group, control_successes, variant_group, variant_successes, test_type, alpha, statistical_test="t-test"
):
    # Calculate the proportions for control and variant groups
    control_rate = control_successes / control_group
    variant_rate = variant_successes / variant_group

    if statistical_test == "t-test":
        # Create arrays of 1s (successes) and 0s (failures) for each group
        control = np.concatenate([np.ones(control_successes), np.zeros(control_group - control_successes)])
        variant = np.concatenate([np.ones(variant_successes), np.zeros(variant_group - variant_successes)])

        # Perform a two-sample t-test (t-test for proportions)
        t_stat, p_value, degrees_freedom = ttest_ind(control, variant, alternative=ALTERNATIVE_MAPPING[test_type])
        test_used = "t-test"

    elif statistical_test == "z-test":
        # Prepare data for z-test
        count = np.array([variant_successes, control_successes])
        nobs = np.array([variant_group, control_group])

        # Perform z-test for proportions
        if test_type == "Two-tailed test":
            alternative = "two-sided"
        elif test_type == "One-tailed test (greater)":
            alternative = "larger"
        else:  # One-tailed test (variant < control)
            alternative = "smaller"

        z_stat, p_value = proportions_ztest(count, nobs, alternative=alternative)
        test_used = "z-test"

    # Adjust for one-tailed or two-tailed test
    if test_type == "Two-tailed test":
        # Two-tailed test
        reject_null_hypothesis = p_value < alpha
    else:
        if statistical_test == "t-test":
            p_value /= 2

        # Check if variant_rate > control_rate for one-tailed test direction
        if test_type == "One-tailed test (greater)":
            reject_null_hypothesis = (variant_rate > control_rate) and (p_value < alpha)
        else:  # One-tailed test (less)
            reject_null_hypothesis = (variant_rate < control_rate) and (p_value < alpha)

    # Compute the Confidence Interval of the Test using confint_proportions_2indep
    ci = confint_proportions_2indep(
        variant_successes,
        variant_group,
        control_successes,
        control_group,
        method=None,
        compare="diff",
        alpha=alpha,
        correction=True,
    )

    # Extract the lower and upper bounds of the confidence interval
    lower = ci[0]
    upper = ci[1]

    # Calculate the lift (relative change) in the variant group compared to the control group
    lower_lift = lower / control_rate
    upper_lift = upper / control_rate

    # Return the results
    return dict(
        reject_null_hypothesis=reject_null_hypothesis,
        p_value=round(p_value, 6),
        lower_bound=round(lower, 6),
        upper_bound=round(upper, 6),
        lower_lift=round(lower_lift, 6),
        upper_lift=round(upper_lift, 6),
        test_used=test_used,
    )


def calculate_sample_size(control_conversion_rate, minimum_detectable_effect, alpha, power):
    # Convert rates to proportions
    p1 = control_conversion_rate
    p2 = control_conversion_rate * (1 + minimum_detectable_effect)

    # Calculate the effect size using Cohen's D
    cohen_D = sm.stats.proportion_effectsize(p1, p2)

    # Estimate the sample size required per group
    n = tt_ind_solve_power(effect_size=cohen_D, power=power, alpha=alpha)
    n = int(round(n, -3))  # Round up to the nearest thousand

    sample_size = round(2 * n)
    start = round(sample_size * 0.01)
    step = round(sample_size * 0.01)

    # Generate the power analysis plot
    ttest_power = TTestIndPower()
    nobs = np.arange(start, sample_size, step)

    plt.figure(figsize=(10, 6))
    ttest_power.plot_power(dep_var="nobs", nobs=nobs, effect_size=[cohen_D], title="Power Analysis")

    # Set plot parameters
    plt.axhline(power, linestyle="--", label="Desired Power", alpha=0.5)
    plt.axvline(n, linestyle="--", color="orange", label="Sample Size", alpha=0.5)
    plt.ylabel("Statistical Power")
    plt.grid(alpha=0.08)
    plt.legend()

    return sample_size, plt


def normal_posterior(n, sample_mean, sample_std, prior_mean, prior_variance):
    sample_variance = (sample_std**2) / n
    posterior_variance = 1 / (1 / prior_variance + 1 / sample_variance)
    posterior_mean = posterior_variance * (prior_mean / prior_variance + sample_mean / sample_variance)

    return posterior_mean, posterior_variance


def bayes_analysis(
    is_conversion: bool,
    control_group: int,
    variant_group: int,
    num_simulations: int = 10000,
    # For conversion testing
    control_successes: int = None,
    variant_successes: int = None,
    alpha_prior: float = None,
    beta_prior: float = None,
    # For continuous metrics
    control_mean: float = None,
    control_std: float = None,
    variant_mean: float = None,
    variant_std: float = None,
    prior_mean: float = None,
    prior_variance: float = None,
):
    if is_conversion:
        # --- Validate inputs ---
        print("\n")
        print("in fucntion")
        print(control_successes, variant_successes, alpha_prior, beta_prior)
        if None in (control_successes, variant_successes, alpha_prior, beta_prior):
            raise ValueError("Missing required parameters for conversion rate testing.")

        # --- Posterior sampling ---
        alpha_post_A = control_successes + alpha_prior
        beta_post_A = control_group - control_successes + beta_prior
        alpha_post_B = variant_successes + alpha_prior
        beta_post_B = variant_group - variant_successes + beta_prior

        control_samples = np.random.beta(alpha_post_A, beta_post_A, size=num_simulations)
        variant_samples = np.random.beta(alpha_post_B, beta_post_B, size=num_simulations)

        # --- Plot ---
        x = np.linspace(0, 1, 1000)
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(x, beta.pdf(x, alpha_post_A, beta_post_A), label="Control (A)", color="blue")
        ax.plot(x, beta.pdf(x, alpha_post_B, beta_post_B), label="Variant (B)", color="green")
        ax.set_title("Posterior Distributions of Conversion Rates")
        ax.set_xlabel("Conversion Rate")
        ax.set_ylabel("Density")
        ax.legend()
        ax.grid(True)

        # --- Metrics ---
        prob_b_better = np.mean(variant_samples > control_samples)
        expected_lift = np.mean((variant_samples - control_samples) / control_samples)
        risk_b = np.mean((control_samples > variant_samples) & (variant_samples < control_samples * 0.99))
        control_ci = (np.percentile(control_samples, 2.5), np.percentile(control_samples, 97.5))
        variant_ci = (np.percentile(variant_samples, 2.5), np.percentile(variant_samples, 97.5))

        return {
            "prob_b_better": float(prob_b_better),
            "expected_lift": float(expected_lift),
            "risk_b": float(risk_b),
            "control_cr": float(np.mean(control_samples)),
            "variant_cr": float(np.mean(variant_samples)),
            "control_ci": tuple(control_ci),
            "variant_ci": tuple(variant_ci),
            "control_alpha_post": round(alpha_post_A, 3),
            "control_beta_post": round(beta_post_A, 3),
            "variant_alpha_post": round(alpha_post_B, 3),
            "variant_beta_post": round(beta_post_B, 3),
            "plot": fig,
        }

    else:
        # --- Validate inputs ---
        print("\n")
        print("in fucntion")
        print(control_mean, control_std, variant_mean, variant_std, prior_mean, prior_variance)
        if None in (control_mean, control_std, variant_mean, variant_std, prior_mean, prior_variance):
            raise ValueError("Missing required parameters for continuous metric testing.")

        # --- Posterior sampling ---
        post_mean_A, post_var_A = normal_posterior(control_group, control_mean, control_std, prior_mean, prior_variance)
        post_mean_B, post_var_B = normal_posterior(variant_group, variant_mean, variant_std, prior_mean, prior_variance)

        control_samples = np.random.normal(post_mean_A, np.sqrt(post_var_A), size=num_simulations)
        variant_samples = np.random.normal(post_mean_B, np.sqrt(post_var_B), size=num_simulations)

        # --- Plot ---
        x = np.linspace(
            min(control_samples.min(), variant_samples.min()), max(control_samples.max(), variant_samples.max()), 1000
        )
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(x, norm.pdf(x, post_mean_A, np.sqrt(post_var_A)), label="Control (A)", color="blue")
        ax.plot(x, norm.pdf(x, post_mean_B, np.sqrt(post_var_B)), label="Variant (B)", color="green")
        ax.set_title("Posterior Distributions of Metric Means")
        ax.set_xlabel("Mean Value")
        ax.set_ylabel("Density")
        ax.legend()
        ax.grid(True)

        # --- Metrics ---
        prob_b_better = np.mean(variant_samples > control_samples)
        expected_lift = np.mean((variant_samples - control_samples) / control_samples)
        risk_b = np.mean((control_samples > variant_samples) & (variant_samples < control_samples * 0.99))
        control_ci = (np.percentile(control_samples, 2.5), np.percentile(control_samples, 97.5))
        variant_ci = (np.percentile(variant_samples, 2.5), np.percentile(variant_samples, 97.5))

        return {
            "prob_b_better": float(prob_b_better),
            "expected_lift": float(expected_lift),
            "risk_b": float(risk_b),
            "control_cr": float(np.mean(control_samples)),
            "variant_cr": float(np.mean(variant_samples)),
            "control_ci": tuple(control_ci),
            "variant_ci": tuple(variant_ci),
            "control_alpha_post": round(post_mean_A, 3),
            "control_beta_post": round(post_var_A, 3),
            "variant_alpha_post": round(post_mean_B, 3),
            "variant_beta_post": round(post_var_B, 3),
            "plot": fig,
        }
