
from src.optimizer import (
    BATCHES,
    prepare_items,
    classical_baseline,
    qaoa_solution,
)

items = prepare_items(BATCHES)

print("OPTIMIZER VALIDATION")
print("=" * 40)

for capacity in [5, 10, 15, 20]:
    baseline = classical_baseline(items, capacity)
    qaoa, details = qaoa_solution(items, capacity)

    print(f"\nCapacity: {capacity} kg")
    print(f"Classical score: {baseline['score']}")
    print(f"Classical weight: {baseline['weight']} kg")
    print(f"QAOA score: {qaoa['score']}")
    print(f"QAOA weight: {qaoa['weight']} kg")

    assert baseline["feasible"], "Classical solution is infeasible"
    assert qaoa["feasible"], "QAOA solution is infeasible"
    assert baseline["weight"] <= capacity
    assert qaoa["weight"] <= capacity
    assert qaoa["score"] <= baseline["score"]

print("\nAll validation checks passed!")
