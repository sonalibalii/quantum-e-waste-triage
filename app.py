
import pandas as pd
import streamlit as st

from src.optimizer import (
    BATCHES,
    prepare_items,
    classical_baseline,
    qaoa_solution,
)

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Quantum E-Waste Triage",
    page_icon="♻️",
    layout="wide",
)

# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("♻️ Quantum E-Waste Triage")

st.markdown(
    """
    **Smarter e-waste collection under limited capacity.**

    Prioritize electronic waste using recovery value, urgency,
    and environmental priority, then compare a QAOA-style
    quantum-circuit simulation with an exact classical baseline.
    """
)

st.info(
    "Research prototype • Illustrative data • Classical statevector "
    "simulation, not quantum hardware. No quantum advantage is claimed."
)

# --------------------------------------------------
# DATA AND CAPACITY
# --------------------------------------------------

items = prepare_items(BATCHES)

st.sidebar.header("Collection settings")

capacity = st.sidebar.slider(
    "Collection capacity (kg)",
    min_value=5,
    max_value=20,
    value=10,
    step=1,
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Priority scoring")
st.sidebar.write("Recovery value: 1×")
st.sidebar.write("Urgency: 2×")
st.sidebar.write("Environmental priority: 2×")

st.sidebar.caption(
    "These weights are illustrative assumptions for this prototype."
)

st.subheader("Available e-waste batches")

inventory = pd.DataFrame(items).rename(
    columns={
        "name": "E-waste batch",
        "weight": "Weight (kg)",
        "recovery": "Recovery value",
        "urgency": "Urgency",
        "environment": "Environmental priority",
        "score": "Priority score",
    }
)

st.dataframe(
    inventory[
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
    "Priority score = recovery value + 2 × urgency "
    "+ 2 × environmental priority."
)

# --------------------------------------------------
# RUN OPTIMIZERS
# --------------------------------------------------

if st.button("Run optimization and compare", type="primary", width="stretch"):
    with st.spinner("Evaluating candidate selections and running simulation..."):
        classical = classical_baseline(items, capacity)
        qaoa, details = qaoa_solution(items, capacity)

    # Defensive checks
    if not classical["feasible"] or not qaoa["feasible"]:
        st.error(
            "At least one optimizer returned an infeasible result. "
            "Please review the optimizer before relying on these results."
        )
        st.stop()

    if qaoa["score"] > classical["score"]:
        st.error(
            "The QAOA score exceeds the exact classical baseline. "
            "Please investigate the scoring or evaluation logic."
        )
        st.stop()

    # --------------------------------------------------
    # KEY METRICS
    # --------------------------------------------------

    st.divider()
    st.header("Optimization results")

    score_gap = classical["score"] - qaoa["score"]

    if classical["score"] > 0:
        gap_percent = 100 * score_gap / classical["score"]
    else:
        gap_percent = 0.0

    qaoa_utilization = 100 * qaoa["weight"] / capacity
    classical_utilization = 100 * classical["weight"] / capacity

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "QAOA score",
        qaoa["score"],
        help="Score from the best feasible QAOA measurement sample found.",
    )

    col2.metric(
        "Classical optimum",
        classical["score"],
        help="Exact optimum found by evaluating every possible selection.",
    )

    col3.metric(
        "Score gap",
        score_gap,
        help="Classical optimum score minus the QAOA score.",
    )

    col4.metric(
        "Optimality gap",
        f"{gap_percent:.1f}%",
        help="Percentage by which the QAOA score falls below the classical optimum.",
    )

    # --------------------------------------------------
    # CAPACITY UTILIZATION
    # --------------------------------------------------

    st.subheader("Collection capacity")

    util1, util2 = st.columns(2)

    with util1:
        st.markdown("#### QAOA (simulated)")
        st.metric(
            "Capacity used",
            f"{qaoa['weight']} / {capacity} kg",
            f"{qaoa_utilization:.1f}% utilized",
        )
        st.progress(min(qaoa_utilization / 100, 1.0))

    with util2:
        st.markdown("#### Exact classical")
        st.metric(
            "Capacity used",
            f"{classical['weight']} / {capacity} kg",
            f"{classical_utilization:.1f}% utilized",
        )
        st.progress(min(classical_utilization / 100, 1.0))

    # --------------------------------------------------
    # SCORE CHART
    # --------------------------------------------------

    st.subheader("Score comparison")

    score_chart = pd.DataFrame(
        {
            "Method": [
                "QAOA (simulated)",
                "Exact classical",
            ],
            "Priority score": [
                qaoa["score"],
                classical["score"],
            ],
        }
    ).set_index("Method")

    st.bar_chart(
        score_chart,
        y="Priority score",
        width="stretch",
    )

    if score_gap == 0:
        st.success(
            "The QAOA simulation matched the exact classical optimum "
            "for this capacity in this run."
        )
    else:
        st.warning(
            f"The QAOA result is {score_gap} points below the exact "
            f"classical optimum ({gap_percent:.1f}% optimality gap)."
        )

    # --------------------------------------------------
    # SELECTED BATCHES
    # --------------------------------------------------

    st.subheader("Selected e-waste batches")

    left, right = st.columns(2)

    def selected_batch_table(solution):
        selected_names = solution["selected"]
        selected_items = [
            item for item in items
            if item["name"] in selected_names
        ]

        columns = {
            "name": "E-waste batch",
            "weight": "Weight (kg)",
            "recovery": "Recovery value",
            "urgency": "Urgency",
            "environment": "Environmental priority",
            "score": "Priority score",
        }

        if not selected_items:
            return pd.DataFrame(columns=list(columns.values()))

        return pd.DataFrame(selected_items).rename(
            columns=columns
        )[
            list(columns.values())
        ]

    with left:
        st.markdown("#### QAOA selection")
        st.write(f"**Total weight:** {qaoa['weight']} kg")
        st.write(f"**Total priority score:** {qaoa['score']}")
        st.dataframe(
            selected_batch_table(qaoa),
            width="stretch",
            hide_index=True,
        )

    with right:
        st.markdown("#### Classical selection")
        st.write(f"**Total weight:** {classical['weight']} kg")
        st.write(f"**Total priority score:** {classical['score']}")
        st.dataframe(
            selected_batch_table(classical),
            width="stretch",
            hide_index=True,
        )

    # --------------------------------------------------
    # COMPARISON TABLE
    # --------------------------------------------------

    st.subheader("Method comparison")

    comparison = pd.DataFrame(
        [
            {
                "Method": "QAOA (simulated)",
                "Priority score": qaoa["score"],
                "Collected weight (kg)": qaoa["weight"],
                "Capacity used (%)": round(qaoa_utilization, 1),
                "Feasible": qaoa["feasible"],
            },
            {
                "Method": "Exact classical",
                "Priority score": classical["score"],
                "Collected weight (kg)": classical["weight"],
                "Capacity used (%)": round(classical_utilization, 1),
                "Feasible": classical["feasible"],
            },
        ]
    )

    st.dataframe(
        comparison,
        width="stretch",
        hide_index=True,
    )

    # --------------------------------------------------
    # EXPERIMENT DETAILS
    # --------------------------------------------------

    with st.expander("View QAOA experiment details"):
        st.write(f"**Parameter search:** {details['parameter_search']}")
        st.write(f"**Circuit repetitions:** {details['reps']}")
        st.write(f"**Measurement samples:** {details['shots']}")
        st.write(
            "**Expected penalized cost:** "
            f"{details['expected_penalized_cost']:.3f}"
        )

        st.markdown(
            """
            **How to interpret these results**

            - The classical baseline exhaustively checks every possible
              batch selection and returns the best feasible solution.
            - The QAOA-style circuit uses a statevector simulator and a
              coarse grid search over circuit parameters.
            - The optimality gap measures the difference between the
              QAOA score and the exact classical optimum.
            - This prototype uses six illustrative batches, so exhaustive
              classical optimization is computationally practical.
            - Matching the classical result does not establish quantum
              advantage or demonstrate better real-world performance.
            """
        )

    # --------------------------------------------------
    # DOWNLOAD RESULTS
    # --------------------------------------------------

    st.subheader("Export results")

    st.download_button(
        label="Download comparison as CSV",
        data=comparison.to_csv(index=False),
        file_name="e_waste_optimization_comparison.csv",
        mime="text/csv",
        width="stretch",
    )

else:
    st.divider()
    st.subheader("Ready to optimize?")
    st.write(
        "Choose a collection capacity using the sidebar, then run "
        "the optimization to compare both methods."
    )

    st.caption(
        "The score is a prototype prioritization metric, not a "
        "measured monetary value or verified environmental impact."
    )
