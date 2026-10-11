

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit.circuit.library import DiagonalGate


# Example data for the dashboard.
# Real users will be able to supply their own batches.
BATCHES = [
    {
        "name": "Laptop circuit boards",
        "weight": 4,
        "recovery": 14,
        "urgency": 8,
        "environment": 9,
    },
    {
        "name": "Smartphones",
        "weight": 3,
        "recovery": 10,
        "urgency": 9,
        "environment": 8,
    },
    {
        "name": "Used batteries",
        "weight": 5,
        "recovery": 13,
        "urgency": 10,
        "environment": 10,
    },
    {
        "name": "Computer monitors",
        "weight": 6,
        "recovery": 12,
        "urgency": 5,
        "environment": 7,
    },
    {
        "name": "Cables",
        "weight": 2,
        "recovery": 4,
        "urgency": 4,
        "environment": 3,
    },
    {
        "name": "Small appliances",
        "weight": 4,
        "recovery": 9,
        "urgency": 7,
        "environment": 6,
    },
]

MAX_QAOA_BATCHES = 10
MAX_CLASSICAL_BATCHES = 16


def prepare_items(batches):
    """Validate batch data and calculate a priority score."""
    if not isinstance(batches, (list, tuple)) or not batches:
        raise ValueError("Enter at least one e-waste batch.")

    if len(batches) > MAX_CLASSICAL_BATCHES:
        raise ValueError(
            f"The exact classical baseline supports at most "
            f"{MAX_CLASSICAL_BATCHES} batches."
        )

    items = []
    required_fields = (
        "name",
        "weight",
        "recovery",
        "urgency",
        "environment",
    )

    for position, batch in enumerate(batches, start=1):
        if not isinstance(batch, dict):
            raise ValueError(f"Batch {position} must be a dictionary.")

        missing = [
            field for field in required_fields
            if field not in batch
        ]
        if missing:
            raise ValueError(
                f"Batch {position} is missing: {', '.join(missing)}."
            )

        name = batch["name"]
        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                f"Batch {position} needs a non-empty name."
            )

        item = batch.copy()
        item["name"] = name.strip()

        for field in ("weight", "recovery", "urgency", "environment"):
            value = item[field]

            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float, np.integer, np.floating))
                or not np.isfinite(value)
            ):
                raise ValueError(
                    f"{item['name']}: {field} must be a finite number."
                )

            if value < 0:
                raise ValueError(
                    f"{item['name']}: {field} cannot be negative."
                )

        if item["weight"] <= 0:
            raise ValueError(
                f"{item['name']}: weight must be greater than zero."
            )

        # Recovery, urgency and environmental values are
        # priority scores, not verified monetary values.
        item["score"] = (
            item["recovery"]
            + 2 * item["urgency"]
            + 2 * item["environment"]
        )

        items.append(item)

    return items


def validate_capacity(capacity):
    """Check that the available collection capacity is valid."""
    if (
        isinstance(capacity, bool)
        or not isinstance(capacity, (int, float, np.integer, np.floating))
        or not np.isfinite(capacity)
        or capacity <= 0
    ):
        raise ValueError(
            "Collection capacity must be a positive finite number."
        )


def evaluate(index, items, capacity):
    """Evaluate one possible selection of batches."""
    chosen = [(index >> i) & 1 for i in range(len(items))]

    weight = sum(
        bit * item["weight"]
        for bit, item in zip(chosen, items)
    )

    score = sum(
        bit * item["score"]
        for bit, item in zip(chosen, items)
    )

    names = [
        item["name"]
        for bit, item in zip(chosen, items)
        if bit
    ]

    return {
        "selected": names,
        "weight": weight,
        "score": score,
        "feasible": weight <= capacity,
        "index": index,
    }


def classical_baseline(items, capacity):
    """Find the best feasible selection by checking every combination."""
    validate_capacity(capacity)

    if not items:
        raise ValueError("At least one batch is required.")

    if len(items) > MAX_CLASSICAL_BATCHES:
        raise ValueError(
            f"The exact classical baseline supports at most "
            f"{MAX_CLASSICAL_BATCHES} batches."
        )

    best = None

    for index in range(2 ** len(items)):
        candidate = evaluate(index, items, capacity)

        if not candidate["feasible"]:
            continue

        if best is None or candidate["score"] > best["score"]:
            best = candidate

    return best


def qaoa_solution(items, capacity, reps=1, shots=2048):
    """Run a one-layer QAOA-style circuit using Qiskit."""
    validate_capacity(capacity)

    if not items:
        raise ValueError("At least one batch is required.")

    if len(items) > MAX_QAOA_BATCHES:
        raise ValueError(
            f"The statevector QAOA prototype supports at most "
            f"{MAX_QAOA_BATCHES} batches. Reduce the number of "
            f"batches or use a scalable classical optimizer."
        )

    if reps != 1:
        raise ValueError("This version supports reps=1.")

    if (
        isinstance(shots, bool)
        or not isinstance(shots, int)
        or shots <= 0
    ):
        raise ValueError("Shots must be a positive integer.")

    n = len(items)
    penalty = 100.0

    energies = np.zeros(2 ** n)

    for index in range(2 ** n):
        candidate = evaluate(index, items, capacity)
        overload = max(0, candidate["weight"] - capacity)

        energies[index] = (
            -candidate["score"] + penalty * overload ** 2
        )

    def make_circuit(gamma, beta):
        circuit = QuantumCircuit(n)

        # Create the initial superposition.
        for qubit in range(n):
            circuit.h(qubit)

        # Apply the cost unitary.
        circuit.append(
            DiagonalGate(np.exp(-1j * gamma * energies)),
            list(range(n)),
        )

        # Apply the mixer unitary.
        for qubit in range(n):
            circuit.rx(2 * beta, qubit)

        return circuit

    # Coarse grid search avoids the SciPy optimizer dependency.
    best_parameters = None
    best_cost = float("inf")

    for gamma in np.linspace(0, 2 * np.pi, 13, endpoint=False):
        for beta in np.linspace(0, np.pi, 13, endpoint=False):
            circuit = make_circuit(gamma, beta)
            state = Statevector.from_instruction(circuit)

            cost = float(
                np.dot(state.probabilities(), energies)
            )

            if cost < best_cost:
                best_cost = cost
                best_parameters = (gamma, beta)

    final_state = Statevector.from_instruction(
        make_circuit(*best_parameters)
    )

    counts = final_state.sample_counts(shots=shots)
    feasible_samples = []

    for bitstring in counts:
        index = int(bitstring, 2)
        candidate = evaluate(index, items, capacity)

        if candidate["feasible"]:
            feasible_samples.append(candidate)

    if feasible_samples:
        best = max(
            feasible_samples,
            key=lambda candidate: candidate["score"],
        )
    else:
        # Fall back to the most probable feasible state.
        feasible_indices = [
            index
            for index in range(2 ** n)
            if evaluate(index, items, capacity)["feasible"]
        ]

        probabilities = final_state.probabilities()

        best_index = max(
            feasible_indices,
            key=lambda index: probabilities[index],
        )

        best = evaluate(best_index, items, capacity)

    details = {
        "parameter_search": "Coarse grid search",
        "expected_penalized_cost": float(best_cost),
        "shots": shots,
        "reps": reps,
    }

    return best, details
