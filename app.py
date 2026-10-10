
import pandas as pd
import streamlit as st

from src.optimizer import (
    BATCHES,
    prepare_items,
    classical_baseline,
    qaoa_solution,
)

st.set_page_config(
    page_title="Quantum E-Waste Triage",
    page_icon="♻️",
    layout="wide",
)

st.title("♻️ Quantum E-Waste Triage")
st.write(
    "Prioritize e-waste collection under limited capacity "
    "using QAOA and a classical baseline."
)

st.info(
    "Prototype using illustrative data. QAOA runs on a classical "
    "statevector simulator; this is not a quantum-hardware run."
)

items = prepare_items(BATCHES)

capacity = st.slider(
    "Collection capacity (kg)",
    min_value=5,
    max_value=20,
    value=10,
)

table = pd.DataFrame(items).rename(
    columns={
        "name": "E-waste batch",
        "weight": "Weight (kg)",
        "recovery": "Recovery value",
        "urgency": "Urgency",
        "environment": "Environmental priority",
        "score": "Priority score",
    }
)

st.subheader("Available e-waste batches")
st.dataframe(
    table[
        [
            "E-waste batch",
            "Weight (kg)",
            "Recovery value",
            "Urgency",
            "Environmental priority",
            "Priority score",
        ]
    ],
    width="stretch",
    hide_index=True,
)

st.caption(
    "Priority score = recovery value + 2 × urgency + "
    "2 × environmental priority."
)

if st.button("Run QAOA and compare", type="primary"):
    with st.spinner("Running the quantum-circuit simulation..."):
        baseline = classical_baseline(items, capacity)
        quantum_result, details = qaoa_solution(items, capacity)

    st.subheader("Results")
    left, right = st.columns(2)

    with left:
        st.markdown("### QAOA (simulated)")
        st.metric("Priority score", quantum_result["score"])
        st.metric("Collected weight", f'{quantum_result["weight"]} kg')
        st.write("Selected batches:")
        for name in quantum_result["selected"]:
            st.write(f"• {name}")

    with right:
        st.markdown("### Exact classical baseline")
        st.metric("Priority score", baseline["score"])
        st.metric("Collected weight", f'{baseline["weight"]} kg')
        st.write("Selected batches:")
        for name in baseline["selected"]:
            st.write(f"• {name}")

    st.write(
        "**Score difference (QAOA − classical):**",
        quantum_result["score"] - baseline["score"],
    )

    comparison = pd.DataFrame(
        [
            {
                "Method": "QAOA (simulated)",
                "Score": quantum_result["score"],
                "Weight (kg)": quantum_result["weight"],
                "Feasible": quantum_result["feasible"],
            },
            {
                "Method": "Exact classical",
                "Score": baseline["score"],
                "Weight (kg)": baseline["weight"],
                "Feasible": baseline["feasible"],
            },
        ]
    )

    st.subheader("Comparison table")
    st.dataframe(comparison, width="stretch", hide_index=True)

    with st.expander("QAOA experiment details"):
        st.write("Parameter search:", details["parameter_search"])
        st.write("Measurement samples:", details["shots"])
        st.write("Circuit repetitions:", details["reps"])
        st.write(
            "Expected penalized cost:",
            round(details["expected_penalized_cost"], 3),
        )

    st.caption(
        "This small simulated experiment does not establish quantum "
        "advantage. The exhaustive classical baseline is practical "
        "because the demo contains only six batches."
    )
else:
    st.write("Choose a capacity and click **Run QAOA and compare**.")
