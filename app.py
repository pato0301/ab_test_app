import streamlit as st

from utils import (
    bayes_analysis,
    calculate_sample_size,
    chi_squared_test,
    frequentist_analysis,
    sample_ratio_mismatch,
)

ANALYSIS_OPTIONS = [
    "Choose a task",
    "Sample Size",
    "Sample Ratio Mismatch",
    "Chi-Square Test",
    "Frequentist Analysis",
    "Bayes Analysis",
]
FREQUENTIST_OPTIONS = ["Two-tailed test", "One-tailed test (less)", "One-tailed test (greater)"]


def main():
    st.title("A/B Test App")

    analysis_type = st.selectbox("Select analysis type", ANALYSIS_OPTIONS)

    if analysis_type == "Sample Size":
        sample_size_section()
    elif analysis_type == "Chi-Square Test":
        chi_square_test_section()
    elif analysis_type == "Sample Ratio Mismatch":
        sample_ratio_mismatch_section()
    elif analysis_type in ("Frequentist Analysis", "Bayes Analysis"):
        analysis_section(analysis_type)


def sample_size_section():
    st.header("Sample Size Calculation")
    control_conversion_rate = st.number_input(
        "Control Conversion Rate", min_value=0.0, max_value=1.0, step=0.01, value=0.1
    )
    minimum_detectable_effect = st.number_input(
        "Minimum Detectable Effect", min_value=0.0, max_value=1.0, step=0.01, value=0.05
    )
    alpha = st.number_input("Significance Level (alpha)", min_value=0.01, max_value=0.1, step=0.01, value=0.05)
    power = st.number_input("Power (1 - beta)", min_value=0.8, max_value=0.99, step=0.01, value=0.8)
    if st.button("Run Sample Size"):
        sample_size, power_plot = calculate_sample_size(
            control_conversion_rate, minimum_detectable_effect, alpha, power
        )
        st.header(f"Sample Size is: {sample_size}")

        # Display the plot in the Streamlit app
        st.pyplot(power_plot)


def chi_square_test_section():
    st.header("Chi Square Test Calculation")

    alpha = st.number_input("Alpha", min_value=0.00, max_value=1.00, step=0.01, value=0.05)

    col1, col2 = st.columns(2)
    with col1:
        control_group = st.number_input("Control Group Observations", min_value=1, step=1, value=1000)
        variant_group = st.number_input("Variant Group Observations", min_value=1, step=1, value=1000)

    with col2:
        control_successes = st.number_input("Control Group Successes", min_value=0, step=1, value=100)
        variant_successes = st.number_input("Variant Group Successes", min_value=0, step=1, value=120)

    if st.button("Run Chi Square Test"):
        result = chi_squared_test(control_group, control_successes, variant_group, variant_successes, alpha)
        st.header("Chi Square Result:")
        st.subheader("Recomendation:")
        # st.write(f"Cohen d is: {result['cohen_d']}")
        st.write(result)
        st.text("")
        st.divider()


def sample_ratio_mismatch_section():
    st.header("Sample Ratio Mismatch")

    alpha = st.number_input("Alpha", min_value=0.00, max_value=1.00, step=0.01, value=0.05)

    col1, col2 = st.columns(2)
    with col1:
        control_group = st.number_input("Control Group Observations", min_value=1, step=1, value=1000)
        variant_group = st.number_input("Variant Group Observations", min_value=1, step=1, value=1000)

    with col2:
        percent_of_variant = st.number_input("Percent Assigment to Variant", min_value=0.0, step=0.01, value=0.5)

    if st.button("Run Chi Square Test"):
        result = sample_ratio_mismatch(control_group, variant_group, percent_of_variant, alpha)
        st.header("Chi Square Result:")
        st.subheader("Recomendation:")
        # st.write(f"Cohen d is: {result['cohen_d']}")
        st.write(result)
        st.text("")
        st.divider()


def analysis_section(analysis_type):
    analisis_name = analysis_type.split(" ")[0].capitalize()
    st.title(f"{analisis_name} Analysis")

    if analysis_type == "Frequentist Analysis":
        test_type = st.selectbox("Select your test type", FREQUENTIST_OPTIONS)

    col1, col2 = st.columns(2)
    with col1:
        # if analysis_type == "Bayes Analysis":
        #     bayes_base_success_rate = st.number_input(
        #         "Base Success Rate", min_value=0.00, max_value=100.00, step=0.01, value=1.00
        #     )

        if analysis_type != "Bayes Analysis":
            control_group = st.number_input("Control Group Observations", min_value=1, step=1, value=1000)
            variant_group = st.number_input("Variant Group Observations", min_value=1, step=1, value=1000)

    with col2:
        # if analysis_type == "Bayes Analysis":
        #     bayes_mde = st.number_input(
        #         "What is the desired lift as a percent (MDE)?", min_value=0.00, max_value=100.00, step=0.01, value=1.00
        #     )

        if analysis_type != "Bayes Analysis":
            control_successes = st.number_input("Control Group Successes", min_value=0, step=1, value=100)
            variant_successes = st.number_input("Variant Group Successes", min_value=0, step=1, value=120)

    # button_key = "bayes" if analysis_type == "Bayes Analysis" else "frequentist"
    # st.button(f"Run {analisis_name} Analysis", key=button_key)

    # Trigger different functions based on the analysis type when the button is clicked
    if analysis_type == "Bayes Analysis":
        st.header("Bayesian A/B Test Configuration")

        # Test Type Selection
        test_type = st.radio(
            "Test Type", options=["Conversion Rate Testing", "Continuous Metric Testing (Mean)"], index=0
        )
        st.caption("Choose what type of metric you want to test.")

        # Variant A and B inputs side by side
        col1, col2 = st.columns(2)

        if test_type == "Conversion Rate Testing":
            with col1:
                st.subheader("Variant A (Control)")
                control_group = st.number_input("Visitors", min_value=1, step=1, value=1000, key="control_visitors")
                control_successes = st.number_input(
                    "Conversions", min_value=0, step=1, value=50, key="control_conversions"
                )
                conversion_rate_control = control_successes / control_group if control_group else 0
                st.info(f"Conversion Rate: {conversion_rate_control:.2%}")

            with col2:
                st.subheader("Variant B (Treatment)")
                variant_group = st.number_input("Visitors ", min_value=1, step=1, value=1000, key="variant_visitors")
                variant_successes = st.number_input(
                    "Conversions ", min_value=0, step=1, value=65, key="variant_conversions"
                )
                conversion_rate_variant = variant_successes / variant_group if variant_group else 0
                st.info(f"Conversion Rate: {conversion_rate_variant:.2%}")

            st.divider()

            # Prior Distribution
            st.subheader("Bayesian Prior Distribution")
            prior_options = {
                "Uniform (Beta(1,1))": (1, 1),
                "Jeffreys (Beta(0.5, 0.5))": (0.5, 0.5),
                "Informative (Beta(2, 5))": (2, 5),
            }
            selected_prior_label = st.selectbox("Prior Distribution Type", list(prior_options.keys()))
            alpha_prior, beta_prior = prior_options[selected_prior_label]
            st.caption("Choose your prior beliefs about the conversion rate distribution.")
            st.info(f"Selected: {selected_prior_label} \n\nParameters: α = {alpha_prior}, β = {beta_prior}")

        elif test_type == "Continuous Metric Testing (Mean)":
            with col1:
                st.subheader("Variant A (Control)")
                control_group = st.number_input("Sample Size", min_value=1, step=1, value=1000, key="mean_control_n")
                control_mean = st.number_input("Sample Mean", value=0.0, key="mean_control_mean")
                control_std = st.number_input(
                    "Sample Standard Deviation", min_value=0.01, value=1.0, key="mean_control_std"
                )
                st.info(f"Mean: {control_mean:.2f}")

            with col2:
                st.subheader("Variant B (Treatment)")
                variant_group = st.number_input("Sample Size ", min_value=1, step=1, value=1000, key="mean_variant_n")
                variant_mean = st.number_input("Sample Mean ", value=0.0, key="mean_variant_mean")
                variant_std = st.number_input(
                    "Sample Standard Deviation ", min_value=0.01, value=1.0, key="mean_variant_std"
                )
                st.info(f"Mean: {variant_mean:.2f}")

            st.divider()
            # Normal Prior
            st.subheader("Bayesian Prior Distribution")
            st.caption("Choose your prior beliefs about the mean distribution.")
            st.selectbox("Prior Distribution Type", ["Normal Prior"])
            prior_mean = st.number_input("Prior Mean", value=0.0)
            prior_variance = st.number_input("Prior Variance", min_value=0.01, value=1.0)

        st.divider()

        # Monte Carlo Simulations
        st.subheader("🔀 Monte Carlo Simulation")
        num_simulations = st.number_input(
            "Number of Simulations", min_value=1000, max_value=100000, step=1000, value=10000
        )
        st.caption("Higher values provide more accurate results but take longer to calculate (1,000 - 100,000).")
        accuracy_level = "High" if num_simulations >= 50000 else "Medium" if num_simulations >= 10000 else "Low"
        st.info(f"Current Setting: {num_simulations:,} simulations\nAccuracy: {accuracy_level}")

        if st.button("Run Bayesian Analysis", key="bayes_analysis_run"):
            if is_conversion := test_type == "Continuous Metric Testing (Mean)":
                print("false\n")
                result = bayes_analysis(
                    is_conversion=is_conversion,
                    control_group=control_group,
                    variant_group=variant_group,
                    num_simulations=num_simulations,
                    control_mean=control_mean,
                    variant_mean=variant_mean,
                    control_std=control_std,
                    variant_std=variant_std,
                    prior_mean=prior_mean,
                    prior_variance=prior_variance,
                )
            else:
                print("\n")
                print("is conversion")
                print(control_successes, variant_successes, alpha_prior, beta_prior)
                print("\n")
                result = bayes_analysis(
                    is_conversion=is_conversion,
                    control_group=control_group,
                    variant_group=variant_group,
                    num_simulations=num_simulations,
                    control_successes=control_successes,
                    variant_successes=variant_successes,
                    alpha_prior=alpha_prior,
                    beta_prior=beta_prior,
                )

            col1, col2, col3 = st.columns(3)
            col1.metric("Probability B is Better", f"{result['prob_b_better']*100:.1f}%")
            col2.metric("Expected Lift", f"{result['expected_lift']*100:.2f}%")
            col3.metric("Risk of Choosing B", f"{result['risk_b']*100:.2f}%")

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Variant A (Control)")
                st.metric("Conversion Rate", f"{result['control_cr']*100:.2f}%")
                st.metric(
                    "95% Credible Interval", f"{result['control_ci'][0]*100:.2f}% - {result['control_ci'][1]*100:.2f}%"
                )
                st.metric("Posterior α", result["control_alpha_post"])
                st.metric("Posterior β", result["control_beta_post"])

            with col2:
                st.subheader("Variant B (Treatment)")
                st.metric("Conversion Rate", f"{result['variant_cr']*100:.2f}%")
                st.metric(
                    "95% Credible Interval", f"{result['variant_ci'][0]*100:.2f}% - {result['variant_ci'][1]*100:.2f}%"
                )
                st.metric("Posterior α", result["variant_alpha_post"])
                st.metric("Posterior β", result["variant_beta_post"])

            st.subheader("Posterior Probability Distributions")
            st.caption("These curves show the probability distribution of conversion rates for each variant")
            if result["plot"]:
                st.pyplot(result["plot"])
            else:
                st.write("[Insert Matplotlib/Plotly plot here]")

    elif analysis_type == "Frequentist Analysis":
        print(f"enter frequentist with {analisis_name}")
        if st.button(f"Run {analisis_name} Analysis", key="frequentist"):
            result = frequentist_analysis(control_group, control_successes, variant_group, variant_successes, test_type)
            st.header("Frequentist Analysis Result:")
            st.subheader("Recomendation:")
            if result["reject_null_hypothesis"]:
                st.write("Reject Ho and conclude that there is statistical significance")
                st.write(f"P value is: {result['p_value']:.4f}")
            else:
                st.write("We can not reject Ho and conclude that there is statistical significance")
                st.write(f"P value is: {result['p_value']}")
            # st.write(f"{result['reject_null_hypothesis']}")
            st.text("")
            st.divider()
            st.subheader("Deeper Analysis Results:")
            col1, col2 = st.columns(2)
            # print(result['ci_control'])
            lower_bound = result["lower_bound"]
            upper_bound = result["upper_bound"]
            lower_lift = result["lower_lift"]
            upper_lift = result["upper_lift"]
            col1.metric("Absolute Difference CI", f"({lower_bound:.3f}, {upper_bound:.3f})", "")
            col2.metric("Relative Difference (lift) CI", f"({lower_lift*100:.1f}%, {upper_lift*100:.1f}%)", "")
            # col3.metric(
            #     "Confidence interval for the one-tailed test is",
            #     f"[{result['lower_bound']:.2f}, {result['upper_bound']:.2f}]",
            # )


if __name__ == "__main__":
    main()
