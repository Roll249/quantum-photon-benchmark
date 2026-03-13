import math
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import networkx as nx
import numpy as np
from scipy.linalg import expm

try:
    from .config import QuantumRoutingConfig
except ImportError:
    from config import QuantumRoutingConfig


@dataclass
class QuantumRoutingArtifacts:
    nodes: List[str]
    adjacency: np.ndarray
    hamiltonian: np.ndarray
    penalized_hamiltonian: np.ndarray
    penalties: np.ndarray
    time_grid: np.ndarray


def _node_energy_ratio(net, node_name: str) -> float:
    node = net.nodes[node_name]["n"]
    current = float(node.bmm.energy)
    max_energy = float(node.bmm.E_INIT)
    if max_energy <= 0:
        return 1.0
    return max(0.0, min(1.0, current / max_energy))


def _edge_metrics(net, u: str, v: str, packet_size_bits: int) -> Tuple[float, float, float]:
    edge = net.edges[u, v]["e"]
    rate = float(edge.cal_rate())
    prop_delay = float(edge.cal_prop_delay())
    tx_delay = packet_size_bits / max(rate, 1.0)
    total_delay = prop_delay + tx_delay
    energy_ratio = min(_node_energy_ratio(net, u), _node_energy_ratio(net, v))
    return rate, total_delay, energy_ratio


def build_quantum_graph(net, cfg: QuantumRoutingConfig) -> Tuple[nx.DiGraph, List[str], Dict[Tuple[str, str], bool]]:
    g = nx.DiGraph()
    g.add_nodes_from(net.nodes)
    edge_violations: Dict[Tuple[str, str], bool] = {}

    for u, v in net.edges:
        rate, delay_s, energy_ratio = _edge_metrics(net, u, v, cfg.packet_size_bits)
        rate_term = math.log1p(max(rate, 0.0))
        delay_term = 1.0 + delay_s * 1e3
        energy_term = 0.5 + energy_ratio
        conductivity = max(cfg.epsilon, (rate_term * energy_term) / delay_term)

        violated = (
            delay_s > cfg.delay_threshold_s
            or rate < cfg.bandwidth_threshold_bps
            or energy_ratio < cfg.min_energy_ratio
        )
        edge_violations[(u, v)] = violated

        base_cost = (1.0 / conductivity) + (cfg.gamma_penalty if violated else 0.0)

        g.add_edge(
            u,
            v,
            conductivity=conductivity,
            base_cost=base_cost,
            delay_s=delay_s,
            rate_bps=rate,
            energy_ratio=energy_ratio,
            violated=violated,
        )

    nodes = list(g.nodes)
    return g, nodes, edge_violations


def _sym_adjacency_from_digraph(g: nx.DiGraph, nodes: Sequence[str]) -> np.ndarray:
    n = len(nodes)
    index = {node: i for i, node in enumerate(nodes)}
    adjacency = np.zeros((n, n), dtype=float)

    for u, v, data in g.edges(data=True):
        i, j = index[u], index[v]
        value = float(data.get("conductivity", 0.0))
        if value <= 0:
            continue
        if value > adjacency[i, j]:
            adjacency[i, j] = value
        if value > adjacency[j, i]:
            adjacency[j, i] = value

    return adjacency


def hamiltonian_from_adjacency(adjacency: np.ndarray) -> np.ndarray:
    degree = np.diag(adjacency.sum(axis=1))
    return degree - adjacency


def build_penalty_vector(
    net,
    nodes: Sequence[str],
    g: nx.DiGraph,
    cfg: QuantumRoutingConfig,
) -> np.ndarray:
    penalties = np.zeros(len(nodes), dtype=float)
    index = {node: i for i, node in enumerate(nodes)}

    for node in nodes:
        energy_ratio = _node_energy_ratio(net, node)
        if energy_ratio < cfg.min_energy_ratio:
            penalties[index[node]] += 1.0

    for u, v, data in g.edges(data=True):
        if data.get("violated", False):
            penalties[index[u]] += 0.5
            penalties[index[v]] += 0.5

    return penalties


def apply_penalty(hamiltonian: np.ndarray, penalties: np.ndarray, gamma: float) -> np.ndarray:
    return hamiltonian + gamma * np.diag(penalties)


def initial_state(size: int, source_index: int) -> np.ndarray:
    psi0 = np.zeros(size, dtype=np.complex128)
    psi0[source_index] = 1.0 + 0.0j
    return psi0


def evolve_state(hamiltonian: np.ndarray, psi0: np.ndarray, t: float) -> np.ndarray:
    unitary = expm(-1j * hamiltonian * t)
    return unitary @ psi0


def destination_probability_curve(
    hamiltonian: np.ndarray,
    source_index: int,
    destination_index: int,
    time_grid: np.ndarray,
) -> np.ndarray:
    psi0 = initial_state(hamiltonian.shape[0], source_index)
    probs = np.zeros(len(time_grid), dtype=float)
    for i, t in enumerate(time_grid):
        psi_t = evolve_state(hamiltonian, psi0, float(t))
        probs[i] = float(np.abs(psi_t[destination_index]) ** 2)
    return probs


def _quantum_probability_vector(
    hamiltonian: np.ndarray,
    source_index: int,
    time_grid: np.ndarray,
    eigvals: Optional[np.ndarray] = None,
    eigvecs: Optional[np.ndarray] = None,
) -> np.ndarray:
    if eigvals is None or eigvecs is None:
        eigvals, eigvecs = np.linalg.eigh(hamiltonian)

    coeff = eigvecs.conj().T[:, source_index]
    phase = np.exp(-1j * np.outer(time_grid, eigvals))
    evolved = (phase * coeff) @ eigvecs.T
    all_probs = np.abs(evolved) ** 2
    target_mass = 1.0 - all_probs[:, source_index]
    t_opt_idx = int(np.argmax(target_mass))
    return all_probs[t_opt_idx]


def _build_weighted_graph(
    g: nx.DiGraph,
    quantum_probs: np.ndarray,
    node_index: Dict[str, int],
    cfg: QuantumRoutingConfig,
) -> nx.DiGraph:
    weighted_graph = nx.DiGraph()
    weighted_graph.add_nodes_from(g.nodes)
    for u, v, data in g.edges(data=True):
        prob_term = quantum_probs[node_index[v]]
        quantum_weight = 1.0 / (prob_term + cfg.epsilon)
        total_cost = float(data["base_cost"]) * (1.0 + cfg.quantum_bias * quantum_weight)
        weighted_graph.add_edge(u, v, weight=total_cost)
    return weighted_graph


def build_quantum_actions(
    net,
    cfg: Optional[QuantumRoutingConfig] = None,
) -> Tuple[Dict[str, Dict[str, str]], QuantumRoutingArtifacts]:
    cfg = cfg or QuantumRoutingConfig()
    g, nodes, _ = build_quantum_graph(net, cfg)
    adjacency = _sym_adjacency_from_digraph(g, nodes)
    hamiltonian = hamiltonian_from_adjacency(adjacency)
    penalties = build_penalty_vector(net, nodes, g, cfg)
    penalized_hamiltonian = apply_penalty(hamiltonian, penalties, cfg.gamma_penalty)
    time_grid = np.linspace(cfg.t_min, cfg.t_max, cfg.t_steps)
    node_index = {node: i for i, node in enumerate(nodes)}
    eigvals, eigvecs = np.linalg.eigh(penalized_hamiltonian)

    actions: Dict[str, Dict[str, str]] = {}
    for src in nodes:
        src_idx = node_index[src]
        quantum_probs = _quantum_probability_vector(
            penalized_hamiltonian,
            src_idx,
            time_grid,
            eigvals=eigvals,
            eigvecs=eigvecs,
        )
        node_actions: Dict[str, str] = {}
        weighted_graph = _build_weighted_graph(g, quantum_probs, node_index, cfg)

        successors = list(g.successors(src))
        fallback = random.choice(successors) if successors else src
        try:
            shortest_paths = nx.single_source_dijkstra_path(weighted_graph, source=src, weight="weight")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            shortest_paths = {}

        for dst in nodes:
            if src == dst:
                node_actions[dst] = src
                continue

            path = shortest_paths.get(dst)
            if path is not None and len(path) >= 2:
                node_actions[dst] = path[1]
            else:
                node_actions[dst] = fallback

        actions[src] = node_actions

    artifacts = QuantumRoutingArtifacts(
        nodes=nodes,
        adjacency=adjacency,
        hamiltonian=hamiltonian,
        penalized_hamiltonian=penalized_hamiltonian,
        penalties=penalties,
        time_grid=time_grid,
    )
    return actions, artifacts


def check_constraints(
    path: Sequence[str],
    g: nx.DiGraph,
    cfg: Optional[QuantumRoutingConfig] = None,
) -> bool:
    cfg = cfg or QuantumRoutingConfig()
    if len(path) < 2:
        return True

    total_delay = 0.0
    min_rate = float("inf")
    min_energy_ratio = 1.0

    for i in range(len(path) - 1):
        u = path[i]
        v = path[i + 1]
        if not g.has_edge(u, v):
            return False
        edge = g.edges[u, v]
        total_delay += float(edge["delay_s"])
        min_rate = min(min_rate, float(edge["rate_bps"]))
        min_energy_ratio = min(min_energy_ratio, float(edge["energy_ratio"]))

    return (
        total_delay <= cfg.delay_threshold_s
        and min_rate >= cfg.bandwidth_threshold_bps
        and min_energy_ratio >= cfg.min_energy_ratio
    )
