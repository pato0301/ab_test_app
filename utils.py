import random

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# import scipy.stats as st
# import scipy.stats as stats
import statsmodels.api as sm
from scipy.special import betaincinv
from scipy.stats import beta
from statsmodels.stats.power import TTestIndPower, tt_ind_solve_power
from statsmodels.stats.proportion import (  # proportions_chisquare,
    confint_proportions_2indep,
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


def bayes_analysis(
    base_suc_rate, control_group, variant_group, control_successes, variant_successes, lift_percent_desired
):
    print(f"lift_percent_desired: {lift_percent_desired}")
    print(f"base_suc_rate: {base_suc_rate}")
    base_fail_rate = 100 - base_suc_rate
    suc_control_group, fail_control_group = control_successes, control_group - control_successes
    suc_variant_group, fail_variant_group = variant_successes, variant_group - variant_successes

    # Update our prior
    alfa_control, beta_control = base_suc_rate + suc_control_group, base_fail_rate + fail_control_group
    alfa_test, beta_test = base_suc_rate + suc_variant_group, base_fail_rate + fail_variant_group

    A_posterior = beta(alfa_control, beta_control)  # Posterior = Prios + A's data
    B_posterior = beta(alfa_test, beta_test)  # Posterior = Prios + B's data

    A_sample = pd.Series(A_posterior.rvs(100000))
    B_sample = pd.Series(B_posterior.rvs(100000))

    # how many times did B outperform A?
    variant_wins = sum(B_sample > A_sample)
    result_variant_wins = variant_wins / N_TRIALS

    # What is the probability of X% improvement
    lift_percentage = (B_sample - A_sample) / A_sample
    lift_percent_result = np.mean((100 * lift_percentage) > lift_percent_desired) * 100

    # Get confidence level
    variant_up_test = betaincinv(alfa_test, beta_test, 0.975)
    variant_low_test = betaincinv(alfa_test, beta_test, 0.25)

    control_up_control = betaincinv(alfa_control, beta_control, 0.975)
    control_low_control = betaincinv(alfa_control, beta_control, 0.25)

    # Get cohen d
    d = cohend(A_sample, B_sample)

    return dict(
        cohen_d=d,
        cohen_d_humanize=cohen_d_interpretation(d),
        conf_interval=(
            (round(control_low_control * 100, 2), (round(control_up_control * 100, 2))),
            (round(variant_low_test * 100, 2), round(variant_up_test * 100, 2)),
        ),
        perc_improvement=lift_percent_result,
        result_variant_wins_times=round(result_variant_wins * 100, 6),
        pValueEquivalent=round(1 - result_variant_wins, 6),
    )


# def frequentist_analysis(control_group, control_successes, variant_group, variant_successes, test_type):
#     # Split the data into two groups (control and variant)
#     # print(variant_group,variant_successes)
#     control = np.array(generate_array(control_group, control_successes))
#     variant = np.array(generate_array(variant_group, variant_successes))

#     # Calculate the conversion rates for each group
#     control_rate = np.mean(control)
#     variant_rate = np.mean(variant)

#     # Calculate the pooled standard error
#     pooled_se = np.sqrt(
#         (control_rate * (1 - control_rate) / control_group) + (variant_rate * (1 - variant_rate) / variant_group)
#     )

#     # Calculate the z-score and p-value
#     z_score = (variant_rate - control_rate) / pooled_se
#     ci_control = st.t.interval(0.95, control_group - 1, loc=control_rate, scale=st.sem(control))
#     # Round the values in ci_control to three decimal points
#     ci_control_rounded = tuple(round(value, 3) for value in ci_control)

#     # ci_variant = st.t.interval(0.95, variant_group - 1, loc=variant_rate, scale=st.sem(variant))
#     # Round the values in ci_control to three decimal points
#     ci_variant_rounded = tuple(round(value, 3) for value in ci_control)

#     if test_type == "One-tailed test":
#         # Calculate the p-value
#         p_value = st.norm.sf(z_score)  # one-tailed test
#         # Calculate the confidence interval
#         margin_of_error_one = st.norm.ppf(1 - ALPHA) * pooled_se
#         lower_bound = (variant_rate - control_rate) - margin_of_error_one
#         upper_bound = (variant_rate - control_rate) + margin_of_error_one
#         reject_null_hypothesis = p_value < ALPHA
#     elif test_type == "Two-tailed test":
#         # Calculate the p-value
#         p_value = st.norm.sf(abs(z_score)) * 2  # two-tailed test
#         # Calculate the confidence interval
#         margin_of_error_two = st.norm.ppf(1 - ALPHA / 2) * pooled_se
#         lower_bound = (variant_rate - control_rate) - margin_of_error_two
#         upper_bound = (variant_rate - control_rate) + margin_of_error_two
#         reject_null_hypothesis = p_value < ALPHA

#     return dict(
#         reject_null_hypothesis=reject_null_hypothesis,
#         p_value=round(p_value, 4),
#         ci_control=ci_control_rounded,
#         ci_variant=ci_variant_rounded,
#         lower_bound=lower_bound,
#         upper_bound=upper_bound,
#     )


def frequentist_analysis(control_group, control_successes, variant_group, variant_successes, test_type):
    # Calculate the proportions for control and variant groups
    control_rate = control_successes / control_group
    variant_rate = variant_successes / variant_group

    # Create arrays of 1s (successes) and 0s (failures) for each group
    control = np.concatenate([np.ones(control_successes), np.zeros(control_group - control_successes)])
    variant = np.concatenate([np.ones(variant_successes), np.zeros(variant_group - variant_successes)])

    # Perform a two-sample t-test (t-test for proportions)
    t_stat, p_value, degrees_freedom = ttest_ind(control, variant, alternative=ALTERNATIVE_MAPPING[test_type])

    # Adjust for one-tailed or two-tailed test
    if test_type == "Two-tailed test":
        # Two-tailed test
        reject_null_hypothesis = p_value < 0.05
    else:
        p_value /= 2  # One-tailed test halves the p-value
        # Check if variant_rate > control_rate for one-tailed test direction
        if variant_rate > control_rate:
            reject_null_hypothesis = p_value < 0.05
        else:
            reject_null_hypothesis = False

    # Compute the Confidence Interval of the Test using confint_proportions_2indep
    ci = confint_proportions_2indep(
        variant_successes,
        variant_group,
        control_successes,
        control_group,
        method=None,
        compare="diff",
        alpha=0.05,
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
    )


# def calculate_sample_size(control_conversion_rate, minimum_detectable_effect, alpha, beta):
#     # Convert rates to proportions
#     p1 = control_conversion_rate
#     p2 = control_conversion_rate + minimum_detectable_effects

#     # Z-scores
#     Z_alpha_2 = st.norm.ppf(1 - alpha / 2)
#     Z_beta = st.norm.ppf(1 - beta)

#     # Calculate sample size
#     numerator = (Z_alpha_2 + Z_beta) ** 2 * (p1 * (1 - p1) + p2 * (1 - p2))
#     denominator = (p1 - p2) ** 2

#     sample_size = numerator / denominator

#     return round(sample_size)


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
