
import pandas as pd
import streamlit as st

from src.optimizer import (
    BATCHES,
    prepare_items,
    classical_baseline,
    qaoa_solution,
    MAX_QAOA_BATCHES,
)

st.set_page_config(
    page_title="Quantum E-Waste Triage",
    page_icon="♻️",
    layout="wide",
)

st.title("♻️ Quantum E-Waste Triage")

st.markdown(
    """
    **Plan e-waste collection under limited capacity.**

    Enter collection batches, estimate their recovery potential and
    priorities, and compare a Qiskit-based simulation with an exact
    classical optimization baseline.
    """
)

st.info(
    "Research prototype. Entered weights can represent actual measurements. "
    "Recovery and priority scores are user estimates, not verified market "
    "prices or certified environmental-impact measurements. Simulation only; "
    "no quantum advantage is claimed."
)

# --------------------------------------------------
# COLLECTION SETTINGS
# --------------------------------------------------

st.sidebar.header("Collection settings")

capacity = st.sidebar.number_input(
    "Available collection capacity (kg)",
    min_value=0.1,
    max_value=100000.0,
    value=10.0,
    step=1.0,
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Priority scoring")
st.sidebar.write("Recovery estimate: 1×")
st.sidebar.write("Urgency: 2×")
st.sidebar.write("Environmental priority: 2×")
st.sidebar.caption("These are illustrative scoring weights.")

# --------------------------------------------------
# EDITABLE INVENTORY
# --------------------------------------------------

st.header("1. Enter your e-waste batches")

st.write(
    "Edit the example rows, delete rows, or add your own batches. "
    "Each row represents one collection batch."
)

st.caption(
    "Recovery estimate is a non-negative priority score. "
    "Urgency and environmental priority range from 0 to 10."
)

default_rows = [
    {
        "Batch name": batch["name"],
        "Weight (kg)": float(batch["weight"]),
        "Recovery estimate (points)": float(batch["recovery"]),
        "Urgency (0–10)": float(batch["urgency"]),
        "Environmental priority (0–10)": float(batch["environment"]),
        "Special handling required": (
            batch["name"].lower() == "used batteries"
        ),
    }
    for batch in BATCHES
]

default_inventory = pd.DataFrame(default_rows)

edited_inventory = st.data_editor(
    default_inventory,
    num_rows="dynamic",
    hide_index=True,
    width="stretch",
    key="editable_inventory",
    column_config={
        "Batch name": st.column_config.TextColumn(
            "Batch name",
            help="Give every batch a unique name.",
        ),
        "Weight (kg)": st.column_config.NumberColumn(
            "Weight (kg)",
            min_value=0.01,
            max_value=100000.0,
            step=0.5,
            format="%.2f",
        ),
        "Recovery estimate (points)": st.column_config.NumberColumn(
            "Recovery estimate (points)",
            min_value=0.0,
            max_value=100000.0,
            step=1.0,
            format="%.2f",
        ),
        "Urgency (0–10)": st.column_config.NumberColumn(
            "Urgency (0–10)",
            min_value=0.0,
            max_value=10.0,
            step=1.0,
        ),
        "Environmental priority (0–10)": st.column_config.NumberColumn(
            "Environmental priority (0–10)",
            min_value=0.0,
            max_value=10.0,
            step=1.0,
        ),
        "Special handling required": st.column_config.CheckboxColumn(
            "Special handling required",
            help=(
                "Flags a batch for manual review. "
                "It does not enforce safety or transport regulations."
            ),
        ),
    },
)

st.caption(
    "The special-handling flag is only a reminder. Check applicable "
    "packaging, segregation, transport, and hazardous-waste requirements "
    "before arranging real collections."
)

# --------------------------------------------------
# OPTIMIZATION
# --------------------------------------------------

st.header("2. Validate and optimize")

if st.button(
    "Run optimization and compare",
    type="primary",
    width="stretch",
):
    if edited_inventory.empty:
        st.error("Add at least one batch.")
        st.stop()

    if len(edited_inventory) > MAX_QAOA_BATCHES:
        st.error(
            f"The Qiskit statevector prototype supports at most "
            f"{MAX_QAOA_BATCHES} batches. Remove some rows to continue."
        )
        st.stop()

    optimizer_input = edited_inventory.rename(
        columns={
            "Batch name": "name",
            "Weight (kg)": "weight",
            "Recovery estimate (points)": "recovery",
            "Urgency (0–10)": "urgency",
            "Environmental priority (0–10)": "environment",
            "Special handling required": "special_handling",
        }
    ).to_dict(orient="records")

    names = []

    for row_number, batch in enumerate(optimizer_input, start=1):
        name = batch.get("name")

        if not isinstance(name, str) or not name.strip():
            st.error(f"Row {row_number}: enter a batch name.")
            st.stop()

        names.append(name.strip().casefold())

        for field in ("weight", "recovery", "urgency", "environment"):
            value = batch.get(field)

            if (
                value is None
                or pd.isna(value)
                or isinstance(value, bool)
                or not isinstance(value, (int, float))
            ):
                st.error(
                    f"Row {row_number}: enter a valid number for {field}."
                )
                st.stop()

        if batch["weight"] <= 0:
            st.error(
                f"Row {row_number}: weight must be greater than zero."
            )
            st.stop()

        if batch["recovery"] < 0:
            st.error(
                f"Row {row_number}: recovery estimate cannot be negative."
            )
            st.stop()

        for field in ("urgency", "environment"):
            if not 0 <= batch[field] <= 10:
                st.error(
                    f"Row {row_number}: {field} must be between 0 and 10."
                )
                st.stop()

    if len(names) != len(set(names)):
        st.error(
            "Batch names must be unique. Rename duplicate rows."
        )
        st.stop()

    try:
        items = prepare_items(optimizer_input)

        with st.spinner("Evaluating collection choices..."):
            classical = classical_baseline(items, capacity)
            qaoa, details = qaoa_solution(items, capacity)

    except (ValueError, TypeError, OverflowError) as error:
        st.error(f"Could not optimize these batches: {error}")
        st.stop()

    if not classical["feasible"] or not qaoa["feasible"]:
        st.error(
            "An optimizer returned an infeasible selection. "
            "Do not use these results as a collection plan."
        )
        st.stop()

    if qaoa["score"] > classical["score"]:
        st.error(
            "The simulated score exceeded the exact classical baseline. "
            "Please review the optimizer."
        )
        st.stop()

    # --------------------------------------------------
    # METRICS
    # --------------------------------------------------

    st.divider()
    st.header("3. Optimization results")

    score_gap = classical["score"] - qaoa["score"]

    gap_percent = (
        100 * score_gap / classical["score"]
        if classical["score"] > 0
        else 0.0
    )

    qaoa_utilization = 100 * qaoa["weight"] / capacity
    classical_utilization = 100 * classical["weight"] / capacity

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("QAOA-style score", f"{qaoa['score']:g}")
    col2.metric("Classical optimum", f"{classical['score']:g}")
    col3.metric("Score gap", f"{score_gap:g}")
    col4.metric("Optimality gap", f"{gap_percent:.1f}%")

    st.caption(
        "These scores use the estimates you entered. They are not "
        "monetary values or verified environmental measurements."
    )

    # --------------------------------------------------
    # RECOMMENDED COLLECTION PLAN
    # --------------------------------------------------

    st.subheader("Recommended plan — exact classical baseline")

    st.write(
        "The classical baseline checks every possible batch combination "
        "and returns the highest-scoring selection that fits the capacity."
    )

    selected_names = set(classical["selected"])

    selected_items = [
        item for item in items
        if item["name"] in selected_names
    ]

    plan_columns = {
        "name": "Batch name",
        "weight": "Weight (kg)",
        "recovery": "Recovery estimate (points)",
        "urgency": "Urgency",
        "environment": "Environmental priority",
        "score": "Priority score",
        "special_handling": "Special handling required",
    }

    if selected_items:
        plan_df = pd.DataFrame(selected_items).rename(
            columns=plan_columns
        )
        plan_df = plan_df[list(plan_columns.values())]
    else:
        plan_df = pd.DataFrame(columns=list(plan_columns.values()))

    p1, p2, p3 = st.columns(3)
    p1.metric("Selected batches", len(classical["selected"]))
    p2.metric("Total weight", f"{classical['weight']:g} kg")
    p3.metric("Capacity used", f"{classical_utilization:.1f}%")

    st.dataframe(plan_df, width="stretch", hide_index=True)

    if any(
        item.get("special_handling", False)
        for item in selected_items
    ):
        st.warning(
            "A selected batch is flagged for special handling. Confirm "
            "applicable safety, segregation, packaging, and transport "
            "requirements before collecting it."
        )

    rejected_items = [
        item for item in items
        if item["name"] not in selected_names
    ]

    with st.expander("View batches not selected"):
        if rejected_items:
            rejected_df = pd.DataFrame(rejected_items).rename(
                columns=plan_columns
            )
            st.dataframe(
                rejected_df,
                width="stretch",
                hide_index=True,
            )
            st.caption(
                "These batches were excluded from this capacity-limited "
                "selection. Review deadlines and handling requirements "
                "before deciding when to collect them."
            )
        else:
            st.write("All entered batches were selected.")

    # --------------------------------------------------
    # METHOD COMPARISON
    # --------------------------------------------------

    st.subheader("Qiskit simulation vs classical baseline")

    left, right = st.columns(2)

    with left:
        st.markdown("#### QAOA-style simulation")
        st.metric("Selected weight", f"{qaoa['weight']:g} kg")
        st.metric("Capacity used", f"{qaoa_utilization:.1f}%")
        st.write("Selected batches:")
        st.write(qaoa["selected"] or "None")

    with right:
        st.markdown("#### Exact classical baseline")
        st.metric("Selected weight", f"{classical['weight']:g} kg")
        st.metric("Capacity used", f"{classical_utilization:.1f}%")
        st.write("Selected batches:")
        st.write(classical["selected"] or "None")

    score_chart = pd.DataFrame(
        {
            "Method": ["QAOA-style simulation", "Exact classical"],
            "Priority score": [qaoa["score"], classical["score"]],
        }
    ).set_index("Method")

    st.bar_chart(score_chart, y="Priority score", width="stretch")

    if score_gap == 0:
        st.success(
            "The simulation matched the exact classical optimum "
            "for these inputs in this run."
        )
    else:
        st.warning(
            f"The simulation was {score_gap:g} points below the classical "
            f"optimum ({gap_percent:.1f}% optimality gap)."
        )

    with st.expander("Qiskit experiment details and limitations"):
        st.write(f"Parameter search: {details['parameter_search']}")
        st.write(f"Circuit repetitions: {details['reps']}")
        st.write(f"Measurement samples: {details['shots']}")
        st.write(
            "Expected penalized cost: "
            f"{details['expected_penalized_cost']:.3f}"
        )

        st.markdown(
            """
            - The classical baseline checks all possible selections.
            - The QAOA-style prototype uses a statevector simulator and
              coarse grid search.
            - This is not a run on quantum hardware.
            - Matching the classical result does not demonstrate
              quantum advantage.
            - This version does not optimize travel routes, pickup
              deadlines, storage compatibility, or regulatory compliance.
            """
        )

    # --------------------------------------------------
    # EXPORT
    # --------------------------------------------------

    st.subheader("4. Export results")

    st.download_button(
        "Download selected collection plan (CSV)",
        data=plan_df.to_csv(index=False),
        file_name="e_waste_collection_plan.csv",
        mime="text/csv",
        width="stretch",
    )

    comparison = pd.DataFrame(
        [
            {
                "Method": "QAOA-style simulation",
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

    st.download_button(
        "Download optimizer comparison (CSV)",
        data=comparison.to_csv(index=False),
        file_name="e_waste_optimization_comparison.csv",
        mime="text/csv",
        width="stretch",
    )

else:
    st.divider()
    st.subheader("Ready to plan a collection?")

    st.write(
        "Edit the table above, set your collection capacity, "
        "and click **Run optimization and compare**."
    )

    st.caption(
        "The default rows are illustrative examples. Replace them with "
        "your own data before using results for planning."
    )
