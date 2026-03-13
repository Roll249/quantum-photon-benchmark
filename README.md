# SatSIM Quantum Routing Integration

This repository now includes a CTQW-based routing core and experiment scripts for the 4-phase workflow:

1. Hamiltonian/Laplacian modeling
2. Schrödinger statevector simulation
3. Penalty-matrix constrained interference routing
4. Qiskit circuit + noise validation

## Main integration points

- `quantum_routing.py`: core Hamiltonian, penalties, and `build_quantum_actions`.
- `satnet.py`: hybrid routing mode (`actions` from outside or internal quantum generation).
- `metrics.py`: PDR, delay, and decision-overhead tracking.

## Experiments

- `python experiments/ctqw_toy.py`
- `python experiments/qiskit_noise.py`
- `python experiments/benchmark.py`
- `python experiments/system_simulation.py --seconds 600`

Outputs are written under `experiments/output`.
