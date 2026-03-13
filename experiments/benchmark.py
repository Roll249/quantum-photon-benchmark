import argparse
import csv
import time
import sys
from pathlib import Path
from statistics import mean

import networkx as nx
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import QuantumRoutingConfig
from quantum_routing import hamiltonian_from_adjacency


def random_graph(n: int, p: float = 0.06, seed: int = 7) -> nx.Graph:
    g = nx.erdos_renyi_graph(n, p, seed=seed, directed=False)
    while not nx.is_connected(g):
        seed += 1
        g = nx.erdos_renyi_graph(n, p, seed=seed, directed=False)

    rng = np.random.default_rng(seed)
    for u, v in g.edges:
        delay = float(rng.uniform(0.003, 0.030))
        bandwidth = float(rng.uniform(4e8, 3e9))
        conductivity = np.log1p(bandwidth) / (1.0 + delay * 1e3)
        g.edges[u, v]["delay_s"] = delay
        g.edges[u, v]["rate_bps"] = bandwidth
        g.edges[u, v]["conductivity"] = max(1e-9, float(conductivity))
        g.edges[u, v]["cost"] = 1.0 / g.edges[u, v]["conductivity"]
    return g


def to_adjacency(g: nx.Graph) -> np.ndarray:
    n = g.number_of_nodes()
    adjacency = np.zeros((n, n), dtype=float)
    for u, v, data in g.edges(data=True):
        adjacency[u, v] = data["conductivity"]
        adjacency[v, u] = data["conductivity"]
    return adjacency


def classical_path_cost(g: nx.Graph, s: int, d: int) -> float:
    path = nx.shortest_path(g, source=s, target=d, weight="cost")
    return sum(g.edges[path[i], path[i + 1]]["cost"] for i in range(len(path) - 1))


def dijkstra_path_cost(g: nx.Graph, s: int, d: int) -> float:
    path = nx.dijkstra_path(g, source=s, target=d, weight="cost")
    return sum(g.edges[path[i], path[i + 1]]["cost"] for i in range(len(path) - 1))


def astar_path_cost(g: nx.Graph, s: int, d: int) -> float:
    min_edge_cost = min(data["cost"] for _, _, data in g.edges(data=True))
    hop_to_goal = nx.single_source_shortest_path_length(g, d)

    def heuristic(node: int, goal: int) -> float:
        hops = hop_to_goal.get(node, g.number_of_nodes())
        return float(hops) * float(min_edge_cost)

    path = nx.astar_path(g, source=s, target=d, heuristic=heuristic, weight="cost")
    return sum(g.edges[path[i], path[i + 1]]["cost"] for i in range(len(path) - 1))


def quantum_peak_probability(g: nx.Graph, s: int, d: int, cfg: QuantumRoutingConfig) -> float:
    adjacency = to_adjacency(g)
    h = hamiltonian_from_adjacency(adjacency)

    eigvals, eigvecs = np.linalg.eigh(h)
    t_grid = np.linspace(cfg.t_min, cfg.t_max, cfg.t_steps)

    coeff = eigvecs.conj().T[:, s]
    phase = np.exp(-1j * np.outer(t_grid, eigvals))
    evolved = (phase * coeff) @ eigvecs.T
    curve = np.abs(evolved[:, d]) ** 2
    return float(np.max(curve))


def quantum_score(g: nx.Graph, s: int, d: int, cfg: QuantumRoutingConfig) -> float:
    pmax = quantum_peak_probability(g, s, d, cfg)
    return 1.0 / max(pmax, cfg.epsilon)


def run_benchmark(sizes=(50, 100, 500, 1000), trials=3, base_seed=7):
    cfg = QuantumRoutingConfig(t_min=0.0, t_max=6.0, t_steps=90)
    rows = []

    for n in sizes:
        dijkstra_times = []
        astar_times = []
        quantum_times = []
        dijkstra_costs = []
        astar_costs = []
        quantum_scores = []
        quantum_probs = []
        quality_ratios = []

        for t in range(trials):
            seed = base_seed + t
            g = random_graph(n=n, p=min(0.1, 6.0 / n), seed=seed)
            s, d = 0, n - 1

            start = time.perf_counter()
            d_cost = dijkstra_path_cost(g, s, d)
            dijkstra_times.append(time.perf_counter() - start)

            start = time.perf_counter()
            a_cost = astar_path_cost(g, s, d)
            astar_times.append(time.perf_counter() - start)

            start = time.perf_counter()
            q_prob = quantum_peak_probability(g, s, d, cfg)
            q_score = 1.0 / max(q_prob, cfg.epsilon)
            quantum_times.append(time.perf_counter() - start)

            dijkstra_costs.append(d_cost)
            astar_costs.append(a_cost)
            quantum_scores.append(q_score)
            quantum_probs.append(q_prob)

            quality_ratios.append(q_score / max(d_cost, 1e-9))

            rows.append(
                {
                    "size": n,
                    "trial": t,
                    "seed": seed,
                    "dijkstra_time_s": dijkstra_times[-1],
                    "astar_time_s": astar_times[-1],
                    "quantum_time_s": quantum_times[-1],
                    "dijkstra_cost": d_cost,
                    "astar_cost": a_cost,
                    "quantum_score": q_score,
                    "quantum_peak_prob": q_prob,
                    "quality_ratio": quality_ratios[-1],
                }
            )

        print(
            f"N={n:4d} | dijkstra_t={mean(dijkstra_times):.4f}s "
            f"| astar_t={mean(astar_times):.4f}s "
            f"| quantum_t={mean(quantum_times):.4f}s "
            f"| dijkstra_cost={mean(dijkstra_costs):.4f} "
            f"| astar_cost={mean(astar_costs):.4f} "
            f"| q_peak_prob={mean(quantum_probs):.4f} "
            f"| quality_ratio={mean(quality_ratios):.4f}"
        )

    return rows


def write_csv(rows, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "size",
        "trial",
        "seed",
        "dijkstra_time_s",
        "astar_time_s",
        "quantum_time_s",
        "dijkstra_cost",
        "astar_cost",
        "quantum_score",
        "quantum_peak_prob",
        "quality_ratio",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_args():
    parser = argparse.ArgumentParser(description="Run scaling benchmark for CTQW proposal vs classical baselines.")
    parser.add_argument("--sizes", nargs="+", type=int, default=[50, 100, 500, 1000])
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--output",
        type=str,
        default="experiments/output/benchmark_results.csv",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    benchmark_rows = run_benchmark(tuple(args.sizes), args.trials, args.seed)
    write_csv(benchmark_rows, ROOT / args.output)
    print(f"saved: {ROOT / args.output}")
