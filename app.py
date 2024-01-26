import streamlit as st
from utils import bayes_analysis, calculate_sample_size, frequentist_analysis

ANALYSIS_OPTIONS = ["Choose a task","sample size", "frequentist analysis", "bayes analysis"]
FREQUENTIST_OPTIONS = ["One-tailed test", "Two-tailed test"]

def main():
    st.title("Landbot's A/B Test App")

    analysis_type = st.selectbox("Select analysis type", ANALYSIS_OPTIONS)

    if analysis_type == "sample size":
        sample_size_section()
    elif analysis_type in ("frequentist analysis", "bayes analysis"):
        analysis_section(analysis_type)

def sample_size_section():
    st.header("Sample Size Calculation")
    control_conversion_rate = st.number_input("Control Conversion Rate", min_value=0.0, max_value=1.0, step=0.01, value=0.1)
    minimum_detectable_effect = st.number_input("Minimum Detectable Effect", min_value=0.0, max_value=1.0, step=0.01, value=0.05)
    alpha = st.number_input("Significance Level (alpha)", min_value=0.01, max_value=0.1, step=0.01, value=0.05)
    beta = st.number_input("Power (1 - beta)", min_value=0.8, max_value=0.99, step=0.01, value=0.9)
    if st.button("Run Sample Size"):
        sample_size = calculate_sample_size(control_conversion_rate, minimum_detectable_effect, alpha, beta)
        st.header(f"Sample Size is: {sample_size}")


def analysis_section(analysis_type):
    analisis_name = analysis_type.split(" ")[0].capitalize()
    st.title(f"{analisis_name} Analysis")

    if analysis_type == "frequentist analysis":
        test_type = st.selectbox("Select your test type", FREQUENTIST_OPTIONS)

    col1, col2 = st.columns(2)
    with col1:
        if analysis_type == "bayes analysis":
            bayes_base_success_rate = st.number_input("Base Success Rate", min_value=0.00, max_value=100.00, step=0.01, value=1.00)

        control_group = st.number_input("Control Group Observations", min_value=1, step=1, value=1000)
        variant_group = st.number_input("Variant Group Observations", min_value=1, step=1, value=1000)


    with col2:
        if analysis_type == "bayes analysis":
            bayes_mde = st.number_input("What is the desired lift as a percent (MDE)?", min_value=0.00, max_value=100.00, step=0.01, value=1.00)

        control_successes = st.number_input("Control Group Successes", min_value=0, step=1, value=100)
        variant_successes = st.number_input("Variant Group Successes", min_value=0, step=1, value=120)


    #st.button(f"Run {analisis_name} Analysis")
    # Trigger different functions based on the analysis type when the button is clicked
    if analysis_type == "bayes analysis":
        if st.button(f"Run {analisis_name} Analysis"):
            result = bayes_analysis(bayes_base_success_rate, control_group, variant_group, control_successes, variant_successes, bayes_mde)
            st.header("Bayesian Analysis Result:")
            st.subheader(f"Recomendation:")
            #st.write(f"Cohen d is: {result['cohen_d']}")
            st.write(f"{result['cohen_d_humanize']}")
            st.text("")
            st.divider()
            st.subheader(f"Deeper Analysis Results:")
            col1, col2, col3 = st.columns(3)
            col1.metric(f"Bayesian Effect Size", f"{result['cohen_d']:.4f}")
            col2.metric(f"Probability lift of {bayes_mde}%", f"{result['perc_improvement']:.2f}%")
            col3.metric(f"times Variant is better than Control", f"{result['result_variant_wins_times']:.2f}%")
            col1, col2, col3 = st.columns(3)
            col1.metric(f"95% credible interval control:", f"{result['conf_interval'][0]}")
            col2.metric(f"95% credible interval test:", f"{result['conf_interval'][1]}")
            #col2.metric(f"Probability lift of {bayes_mde*100}%", f"{result['perc_improvement']:.2f}%")
            #col3.metric(f"times Variant is better than Control", f"{result['result_variant_wins_times']:.2f}%")
            #st.write(f"Bayesian Effect Size: {result['cohen_d']:.4f}")
            #st.write(f"Probability that we are seeing a {bayes_mde}% lift: {result['perc_improvement']:.4f}")
            #st.write(f"{result['result_variant_wins_times']}% of the times B is better than A. This can be linked to a one-sided p-value of {result['pValueEquivalent']}")
            #st.write(f"95% credible interval control: {result['conf_interval'][0]}")
            #st.write(f"95% credible interval test: {result['conf_interval'][1]}")
    elif analysis_type == "frequentist analysis":
        if st.button(f"Run {analisis_name} Analysis"):
            result = frequentist_analysis(control_group, control_successes, variant_group, variant_successes, test_type)
            st.header("Frequentist Analysis Result:")
            st.subheader(f"Recomendation:")
            if result['reject_null_hypothesis']:
                st.write(f"You should implement the variant group")
                st.write(f"P value is: {result['p_value']:.4f}")
            else:
                st.write(f"You should not implement the control group")
                st.write(f"P value is: {result['p_value']}")
            #st.write(f"{result['reject_null_hypothesis']}")
            st.text("")
            st.divider()
            st.subheader(f"Deeper Analysis Results:")
            col1, col2, col3 = st.columns(3)
            #print(result['ci_control'])
            col1.metric("Confidence interval for control group", f"{result['ci_control']}")
            col2.metric(f"Confidence interval for test group", f"{result['ci_variant']}")
            col3.metric(f"Confidence interval for the one-tailed test is", f"[{result['lower_bound']:.2f}, {result['upper_bound']:.2f}]")



if __name__ == "__main__":
    main()
