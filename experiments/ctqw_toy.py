import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import QuantumRoutingConfig
from quantum_routing import (
    apply_penalty,
    check_constraints,
    destination_probability_curve,
    hamiltonian_from_adjacency,
)


def build_toy_graph() -> nx.DiGraph:
    g = nx.DiGraph()
    g.add_nodes_from(range(5))

    edges = [
        (0, 1, 2.0, 0.015, 5e8, 0.95),
        (1, 4, 2.0, 0.015, 5e8, 0.95),
        (0, 2, 10.0, 0.008, 2e9, 0.90),
        (2, 3, 10.0, 0.008, 2e9, 0.90),
        (3, 4, 10.0, 0.008, 2e9, 0.90),
    ]

    for u, v, conductivity, delay_s, rate_bps, energy_ratio in edges:
        g.add_edge(
            u,
            v,
            conductivity=conductivity,
            delay_s=delay_s,
            rate_bps=rate_bps,
            energy_ratio=energy_ratio,
            violated=False,
        )
        g.add_edge(
            v,
            u,
            conductivity=conductivity,
            delay_s=delay_s,
            rate_bps=rate_bps,
            energy_ratio=energy_ratio,
            violated=False,
        )

    return g


def build_adjacency(g: nx.DiGraph) -> np.ndarray:
    n = g.number_of_nodes()
    adjacency = np.zeros((n, n), dtype=float)
    for u, v, data in g.edges(data=True):
        adjacency[u, v] = max(adjacency[u, v], float(data["conductivity"]))
        adjacency[v, u] = max(adjacency[v, u], float(data["conductivity"]))
    return adjacency


def main() -> None:
    cfg = QuantumRoutingConfig(
        delay_threshold_s=0.030,
        bandwidth_threshold_bps=1e9,
        min_energy_ratio=0.25,
        gamma_penalty=50.0,
        t_min=0.0,
        t_max=10.0,
        t_steps=220,
    )

    g = build_toy_graph()
    adjacency = build_adjacency(g)
    h = hamiltonian_from_adjacency(adjacency)

    source = 0
    destination = 4
    time_grid = np.linspace(cfg.t_min, cfg.t_max, cfg.t_steps)

    curve_base = destination_probability_curve(h, source, destination, time_grid)

    short_path = [0, 1, 4]
    long_path = [0, 2, 3, 4]
    print("short_path_constraints:", check_constraints(short_path, g, cfg))
    print("long_path_constraints:", check_constraints(long_path, g, cfg))

    penalties = np.zeros(h.shape[0], dtype=float)
    penalties[1] = 1.0
    h_penalized = apply_penalty(h, penalties, cfg.gamma_penalty)
    curve_penalty = destination_probability_curve(h_penalized, source, destination, time_grid)

    best_base_idx = int(np.argmax(curve_base))
    best_penalty_idx = int(np.argmax(curve_penalty))
    print(f"max P_dst without penalty = {curve_base[best_base_idx]:.4f} at t={time_grid[best_base_idx]:.3f}")
    print(f"max P_dst with penalty    = {curve_penalty[best_penalty_idx]:.4f} at t={time_grid[best_penalty_idx]:.3f}")

    os.makedirs("experiments/output", exist_ok=True)
    plt.figure(figsize=(9, 5))
    plt.plot(time_grid, curve_base, label="P_dst(t) baseline")
    plt.plot(time_grid, curve_penalty, label="P_dst(t) with penalty", linestyle="--")
    plt.xlabel("Time t")
    plt.ylabel("Destination probability")
    plt.title("CTQW toy model (5 nodes): destination probability over time")
    plt.legend()
    plt.tight_layout()
    plt.savefig("experiments/output/ctqw_toy_probability.png", dpi=150)
    print("saved: experiments/output/ctqw_toy_probability.png")


if __name__ == "__main__":
    main()
