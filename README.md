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
- `python experiments/burst_traffic_benchmark.py --seconds 600 --burst-start 300 --burst-duration 60 --burst-multiplier 3`

Outputs are written under `experiments/output`.

## Burst traffic + Hero chart

The burst benchmark writes:

- `<prefix>_timeline.csv`: window-level PDR over time for baseline and quantum.
- `<prefix>_summary.csv`: overall run summary.
- `<prefix>_pdr_linechart.png`: line chart of PDR vs time with burst window highlighted.

Default prefix:

- `experiments/output/burst_traffic_600s`

## Routing table cache

Quantum route actions are cached in `SatNet` by a discretized topology signature
(energy + link rate + propagation delay bins) with LRU eviction.
Cache behavior is controlled by `RuntimeConfig` fields in `config.py`.
