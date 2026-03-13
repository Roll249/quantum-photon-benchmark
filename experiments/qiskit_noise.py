import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import QiskitConfig


def build_hamiltonian_3node() -> np.ndarray:
    return np.array(
        [
            [11.0, -10.0, -1.0],
            [-10.0, 20.0, -10.0],
            [-1.0, -10.0, 11.0],
        ],
        dtype=float,
    )


def embed_to_qubits(h: np.ndarray) -> np.ndarray:
    dim = h.shape[0]
    qubits = int(np.ceil(np.log2(dim)))
    full_dim = 2 ** qubits
    embedded = np.zeros((full_dim, full_dim), dtype=complex)
    embedded[:dim, :dim] = h
    return embedded


def run() -> None:
    try:
        from qiskit import QuantumCircuit, transpile
        from qiskit.circuit.library import PauliEvolutionGate
        from qiskit.synthesis import LieTrotter
        from qiskit.quantum_info import Operator, SparsePauliOp
        from qiskit_aer import AerSimulator
        from qiskit_aer.noise import (
            NoiseModel,
            depolarizing_error,
            thermal_relaxation_error,
        )
    except Exception as exc:
        raise RuntimeError(
            "Qiskit dependencies are required. Install qiskit and qiskit-aer first."
        ) from exc

    cfg = QiskitConfig()
    h3 = build_hamiltonian_3node()
    h4 = embed_to_qubits(h3)
    num_qubits = int(np.log2(h4.shape[0]))

    op = SparsePauliOp.from_operator(Operator(h4))
    evo = PauliEvolutionGate(op, time=1.5, synthesis=LieTrotter(reps=cfg.trotter_steps))

    circuit = QuantumCircuit(num_qubits, num_qubits)
    circuit.append(evo, range(num_qubits))
    circuit.measure(range(num_qubits), range(num_qubits))

    ideal_backend = AerSimulator()
    t_ideal = transpile(circuit, ideal_backend)
    ideal_result = ideal_backend.run(t_ideal, shots=cfg.shots).result()
    ideal_counts = ideal_result.get_counts()

    noise_model = NoiseModel()
    t1 = cfg.t1_us * 1e-6
    t2 = cfg.t2_us * 1e-6
    one_qubit_thermal = thermal_relaxation_error(t1, t2, 80e-9)
    two_qubit_thermal = thermal_relaxation_error(t1, t2, 250e-9).tensor(
        thermal_relaxation_error(t1, t2, 250e-9)
    )

    one_qubit_gate_error = depolarizing_error(cfg.gate_error_1q, 1)
    two_qubit_gate_error = depolarizing_error(cfg.gate_error_2q, 2)

    for gate in ["rz", "sx", "x"]:
        noise_model.add_all_qubit_quantum_error(one_qubit_thermal.compose(one_qubit_gate_error), gate)
    for gate in ["cx"]:
        noise_model.add_all_qubit_quantum_error(two_qubit_thermal.compose(two_qubit_gate_error), gate)

    noisy_backend = AerSimulator(noise_model=noise_model)
    t_noisy = transpile(circuit, noisy_backend)
    noisy_result = noisy_backend.run(t_noisy, shots=cfg.shots).result()
    noisy_counts = noisy_result.get_counts()

    labels = ["node0", "node1", "node2"]

    def to_node_probs(counts):
        probs = np.zeros(3)
        total = sum(counts.values())
        if total == 0:
            return probs
        for bits, count in counts.items():
            idx = int(bits, 2)
            if idx < 3:
                probs[idx] += count / total
        return probs

    ideal_probs = to_node_probs(ideal_counts)
    noisy_probs = to_node_probs(noisy_counts)

    os.makedirs("experiments/output", exist_ok=True)
    x = np.arange(len(labels))
    width = 0.35
    plt.figure(figsize=(8, 5))
    plt.bar(x - width / 2, ideal_probs, width, label="Ideal")
    plt.bar(x + width / 2, noisy_probs, width, label="Noisy")
    plt.xticks(x, labels)
    plt.ylabel("Measurement probability")
    plt.title("Qiskit evolution with and without noise")
    plt.legend()
    plt.tight_layout()
    plt.savefig("experiments/output/qiskit_noise_histogram.png", dpi=150)

    print("ideal_counts:", ideal_counts)
    print("noisy_counts:", noisy_counts)
    print("saved: experiments/output/qiskit_noise_histogram.png")


if __name__ == "__main__":
    run()
