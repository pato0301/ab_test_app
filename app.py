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

    if analysis_type == "sample size":
        sample_size_section()
    elif analysis_type == "Chi-Square Test":
        chi_square_test_section()
    elif analysis_type == "Sample Ratio Mismatch":
        sample_ratio_mismatch_section()
    elif analysis_type in ("frequentist analysis", "bayes analysis"):
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

    if analysis_type == "frequentist analysis":
        test_type = st.selectbox("Select your test type", FREQUENTIST_OPTIONS)

    col1, col2 = st.columns(2)
    with col1:
        if analysis_type == "bayes analysis":
            bayes_base_success_rate = st.number_input(
                "Base Success Rate", min_value=0.00, max_value=100.00, step=0.01, value=1.00
            )

        control_group = st.number_input("Control Group Observations", min_value=1, step=1, value=1000)
        variant_group = st.number_input("Variant Group Observations", min_value=1, step=1, value=1000)

    with col2:
        if analysis_type == "bayes analysis":
            bayes_mde = st.number_input(
                "What is the desired lift as a percent (MDE)?", min_value=0.00, max_value=100.00, step=0.01, value=1.00
            )

        control_successes = st.number_input("Control Group Successes", min_value=0, step=1, value=100)
        variant_successes = st.number_input("Variant Group Successes", min_value=0, step=1, value=120)

    # st.button(f"Run {analisis_name} Analysis")
    # Trigger different functions based on the analysis type when the button is clicked
    if analysis_type == "bayes analysis":
        if st.button(f"Run {analisis_name} Analysis"):
            result = bayes_analysis(
                bayes_base_success_rate, control_group, variant_group, control_successes, variant_successes, bayes_mde
            )
            st.header("Bayesian Analysis Result:")
            st.subheader("Recomendation:")
            # st.write(f"Cohen d is: {result['cohen_d']}")
            st.write(f"{result['cohen_d_humanize']}")
            st.text("")
            st.divider()
            st.subheader("Deeper Analysis Results:")
            col1, col2, col3 = st.columns(3)
            col1.metric("Bayesian Effect Size", f"{result['cohen_d']:.4f}")
            col2.metric(f"Probability lift of {bayes_mde}%", f"{result['perc_improvement']:.2f}%")
            col3.metric("times Variant is better than Control", f"{result['result_variant_wins_times']:.2f}%")
            col1, col2, col3 = st.columns(3)
            col1.metric("95% credible interval control:", f"{result['conf_interval'][0]}")
            col2.metric("95% credible interval test:", f"{result['conf_interval'][1]}")
            # col2.metric(f"Probability lift of {bayes_mde*100}%", f"{result['perc_improvement']:.2f}%")
            # col3.metric(f"times Variant is better than Control", f"{result['result_variant_wins_times']:.2f}%")
            # st.write(f"Bayesian Effect Size: {result['cohen_d']:.4f}")
            # st.write(f"Probability that we are seeing a {bayes_mde}% lift: {result['perc_improvement']:.4f}")
            # st.write(f"{result['result_variant_wins_times']}% of the times B is better than A.
            # This can be linked to a one-sided p-value of {result['pValueEquivalent']}")
            # st.write(f"95% credible interval control: {result['conf_interval'][0]}")
            # st.write(f"95% credible interval test: {result['conf_interval'][1]}")
    elif analysis_type == "frequentist analysis":
        if st.button(f"Run {analisis_name} Analysis"):
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
