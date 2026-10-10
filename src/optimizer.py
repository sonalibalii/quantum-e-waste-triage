
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit.circuit.library import DiagonalGate


# Illustrative data for our hackathon prototype
BATCHES = [
    {"name": "Laptop circuit boards", "weight": 4, "recovery": 14, "urgency": 8, "environment": 9},
    {"name": "Smartphones", "weight": 3, "recovery": 10, "urgency": 9, "environment": 8},
    {"name": "Used batteries", "weight": 5, "recovery": 13, "urgency": 10, "environment": 10},
    {"name": "Computer monitors", "weight": 6, "recovery": 12, "urgency": 5, "environment": 7},
    {"name": "Cables", "weight": 2, "recovery": 4, "urgency": 4, "environment": 3},
    {"name": "Small appliances", "weight": 4, "recovery": 9, "urgency": 7, "environment": 6},
]


def prepare_items(batches):
    items = []
    for batch in batches:
        item = batch.copy()
        item["score"] = (
            item["recovery"]
            + 2 * item["urgency"]
            + 2 * item["environment"]
        )
        items.append(item)
    return items


def evaluate(index, items, capacity):
    chosen = [(index >> i) & 1 for i in range(len(items))]
    weight = sum(bit * item["weight"] for bit, item in zip(chosen, items))
    score = sum(bit * item["score"] for bit, item in zip(chosen, items))
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
    candidates = [
        evaluate(index, items, capacity)
        for index in range(2 ** len(items))
    ]
    feasible = [candidate for candidate in candidates if candidate["feasible"]]
    return max(feasible, key=lambda candidate: candidate["score"])


def qaoa_solution(items, capacity, reps=1, shots=2048):
    """Run a one-layer QAOA-style cost and mixer circuit using Qiskit."""
    if reps != 1:
        raise ValueError("This version supports reps=1.")

    n = len(items)
    penalty = 100.0

    energies = np.zeros(2**n)
    for index in range(2**n):
        candidate = evaluate(index, items, capacity)
        overload = max(0, candidate["weight"] - capacity)
        energies[index] = -candidate["score"] + penalty * overload**2

    def make_circuit(gamma, beta):
        circuit = QuantumCircuit(n)
        for qubit in range(n):
            circuit.h(qubit)

        circuit.append(
    DiagonalGate(np.exp(-1j * gamma * energies)),
    list(range(n)),
)
        

        for qubit in range(n):
            circuit.rx(2 * beta, qubit)

        return circuit

    # Grid search avoids the SciPy optimizer DLL currently blocked on Windows.
    best_parameters = None
    best_cost = float("inf")

    for gamma in np.linspace(0, 2 * np.pi, 13, endpoint=False):
        for beta in np.linspace(0, np.pi, 13, endpoint=False):
            circuit = make_circuit(gamma, beta)
            state = Statevector.from_instruction(circuit)
            cost = float(np.dot(state.probabilities(), energies))

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
        best = max(feasible_samples, key=lambda candidate: candidate["score"])
    else:
        feasible_indices = [
            i for i in range(2**n)
            if evaluate(i, items, capacity)["feasible"]
        ]
        probabilities = final_state.probabilities()
        best_index = max(
            feasible_indices,
            key=lambda i: probabilities[i],
        )
        best = evaluate(best_index, items, capacity)

    details = {
        "parameter_search": "Coarse grid search",
        "expected_penalized_cost": float(best_cost),
        "shots": shots,
        "reps": reps,
    }
    return best, details
