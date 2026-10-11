# Project Title

## Project Metadata

- **Project Title:** Quantum E-Waste Triage
- **Team Name:** Sonali
- **Chosen Track:** Track 2: Open-Domain Optimization & Real-World Solvers
- **Video Presentation Link:** https://drive.google.com/file/d/1ftMwH1FjshFIXALlJBQ2AQNCMbdok_T4/view?usp=drivesdk
- **Live Demo Timestamp in Video:** 2 :55m

### Team Members (Max 4 members)

| Name | Email | GitHub Username |
|---|---|---|
| Sonali | sonali34409@gmail.com | @sonalibalii |

## 1. Project Overview & Motivation

Electronic waste (e-waste) contains valuable recoverable materials, but collection teams often have limited transport capacity and must decide which waste batches to collect first.

Quantum E-Waste Triage models this as a capacity-constrained binary optimization problem. Each batch has a weight, recovery estimate, urgency score, and environmental priority. The system selects a combination of batches that maximizes the total priority score without exceeding the available collection capacity.

The project uses Qiskit to simulate a QAOA-style optimization approach and compares its result against an exact classical baseline. An interactive Streamlit dashboard allows users to edit the inventory, change capacity, compare the solutions, and export the results.

The goal is to demonstrate how quantum optimization techniques can be explored for a practical resource-allocation problem while honestly evaluating their results against classical methods.

## 2. Quantum Architecture & Mechanics

### Problem Formulation

Each waste batch is represented by a binary decision variable \(x_i\):

- \(x_i=1\): Select the batch for collection.
- \(x_i=0\): Do not select the batch.

Let \(w_i\) represent the weight and \(p_i\) represent the priority score of batch \(i\). The objective is to maximize the total priority score without exceeding the available capacity \(C\).

\[
\text{Maximize }\sum_i p_i x_i
\]

Subject to:

\[
\sum_i w_i x_i \leq C,\qquad x_i\in\{0,1\}
\]

The priority score is calculated as:

\[
p_i=r_i+2u_i+2e_i
\]

where \(r_i\) is the recovery estimate, \(u_i\) is urgency, and \(e_i\) is environmental priority.

### Qiskit Implementation

The project uses a one-layer QAOA-style circuit simulation with Qiskit:

1. **Initialization:** Hadamard gates prepare a superposition of candidate selections.
2. **Cost operation:** A diagonal unitary encodes objective values for candidate selections.
3. **Mixer operation:** RX rotations mix candidate states.
4. **Parameter search:** A grid search evaluates combinations of circuit parameters.
5. **Simulation and selection:** Statevector simulation and sampled counts are used to identify a candidate solution.

This is a simulation-based QAOA-style prototype. It does not claim execution on quantum hardware or demonstrate quantum advantage.

### Classical Baseline

An exact classical solver enumerates possible batch combinations for small instances and chooses the highest-scoring feasible selection. The dashboard compares both methods using priority score, collected weight, capacity utilization, and feasibility.

## 3. Repository Structure & How to Run

### Project Structure

```text
quantum-e-waste-triage/
├── app.py
├── requirements.txt
├── src/
│   └── optimizer.py
├── test_optimizer.py
├── notebooks/
│   └── .gitkeep
├── references/
├── HACKATHON_GUIDE.md
└── README.md
```

- `app.py`: Streamlit dashboard for inventory editing, optimization, comparisons, visualizations, and CSV exports.
- `src/optimizer.py`: Qiskit-based simulation and classical optimization logic.
- `test_optimizer.py`: Validation checks for optimizer behavior.
- `requirements.txt`: Python dependencies.
- `notebooks/`: Directory reserved for notebooks.
- `references/`: Supporting project references.
- `HACKATHON_GUIDE.md`: Hackathon and project guidance.

### Installation & Execution Instructions

**Prerequisites:** Python and Git installed on your system.

1. Clone the repository:

```bash
git clone https://github.com/sonalibalii/quantum-e-waste-triage.git
cd quantum-e-waste-triage
```

2. Create and activate a virtual environment.

On Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

4. Launch the dashboard:

```bash
streamlit run app.py
```

5. Run the validation checks:

```bash
python test_optimizer.py
```

**Deployed application:** https://quantum-e-waste-triage-mcfeahihrqs3thu5cdwkhu.streamlit.app/

## 4. Implementation Walkthrough & Live Demo

The Streamlit dashboard provides an interactive interface for exploring capacity-constrained e-waste collection.

The demonstration will cover:

1. Opening the deployed dashboard.
2. Reviewing the sample e-waste inventory and batch attributes.
3. Editing batch weights, recovery estimates, urgency, and environmental priority.
4. Changing the collection capacity.
5. Running the QAOA-style simulation and exact classical baseline.
6. Comparing selected batches, priority scores, collected weight, and capacity utilization.
7. Inspecting comparison visualizations and exporting results as CSV files.

The demonstration will show how changing capacity or inventory affects the collection plan.

**Live demo:** https://quantum-e-waste-triage-mcfeahihrqs3thu5cdwkhu.streamlit.app/

**Video presentation:** To be added after recording and uploading the video.

## 5. Classical vs. Quantum Comparison

The project compares a QAOA-style quantum circuit simulation with an exact classical baseline.

| Feature | QAOA-Style Simulation | Exact Classical Baseline |
|---|---|---|
| Approach | Qiskit circuit simulation with parameter grid search | Enumeration of candidate combinations |
| Purpose | Explore a quantum optimization approach | Establish a reference solution |
| Feasibility | Evaluated against capacity constraints | Evaluated against capacity constraints |
| Output | Candidate selection and objective score | Highest-scoring feasible selection for the supported small instance |
| Execution | Classical simulation of a quantum circuit | Classical computation |

In the sample run with a 10 kg capacity, both approaches selected smartphones, used batteries, and cables.

| Metric | QAOA-Style Simulation | Exact Classical |
|---|---:|---:|
| Priority score | 115 | 115 |
| Collected weight | 10 kg | 10 kg |
| Capacity used | 100% | 100% |
| Feasible | Yes | Yes |

Both methods achieved the same score in this example. This result does not establish quantum advantage; the classical baseline provides a reference for evaluating the simulated solution.

## 6. Performance, Results & Limitations

### Results

The previously tested optimizer produced the following results:

| Capacity | Classical Score | Classical Weight | QAOA-Style Score | QAOA-Style Weight |
|---:|---:|---:|---:|---:|
| 5 kg | 62 | 5 kg | 62 | 5 kg |
| 10 kg | 115 | 10 kg | 115 | 10 kg |
| 15 kg | 163 | 14 kg | 163 | 14 kg |
| 20 kg | 199 | 20 kg | 199 | 20 kg |

The validation checks passed in the previously tested environment. Re-run the tests if the optimizer code has changed since those results were obtained.

### Limitations

- The sample inventory uses illustrative inputs rather than independently verified real-world measurements.
- Recovery estimates and priority scores are user-defined points, not verified financial returns or environmental impact measurements.
- The QAOA-style circuit is simulated classically; no quantum hardware execution is claimed.
- The finite parameter grid does not guarantee optimal parameters for every instance.
- Exact enumeration is practical for small instances but scales exponentially with the number of batches.
- Matching results on sample instances do not demonstrate quantum advantage.
- Real-world deployment would require validated waste data, operational constraints, and evaluation with collection teams.

### Future Improvements

Potential extensions include testing larger datasets, incorporating transportation and special-handling constraints, comparing additional optimization methods, and evaluating suitable implementations on quantum hardware when feasible.

## 7. References & Acknowledgments

- [Qiskit Documentation](https://docs.quantum.ibm.com/)
- [Qiskit Optimization Documentation](https://qiskit-community.github.io/qiskit-optimization/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [NumPy Documentation](https://numpy.org/doc/)
- [Qiskit Fall Fest 2026 IIIT Kottayam Hackathon Template](https://github.com/Shanwis/Qiskit-Fall-Fest-2026-IIITKottayam-Hackathon-Template)

We acknowledge the open-source communities behind Qiskit, Streamlit, NumPy, and Python for providing tools that support experimentation with optimization and quantum circuit simulation.

## About

Quantum E-Waste Triage is a Qiskit-powered e-waste collection optimization project developed for Qiskit Fall Fest 2026, Track 2: Open-Domain Optimization & Real-World Solvers.

The project combines a Qiskit-based QAOA-style simulation, an exact classical baseline, and an interactive Streamlit dashboard to explore capacity-constrained resource allocation.

**Repository:** https://github.com/sonalibalii/quantum-e-waste-triage

**Live Demo:** https://quantum-e-waste-triage-mcfeahihrqs3thu5cdwkhu.streamlit.app/
