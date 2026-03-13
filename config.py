from dataclasses import dataclass


@dataclass
class QuantumRoutingConfig:
    delay_threshold_s: float = 0.05
    bandwidth_threshold_bps: float = 1e9
    min_energy_ratio: float = 0.20
    gamma_penalty: float = 50.0
    packet_size_bits: int = 12000
    t_min: float = 0.0
    t_max: float = 10.0
    t_steps: int = 120
    quantum_bias: float = 0.25
    epsilon: float = 1e-9


@dataclass
class QiskitConfig:
    trotter_steps: int = 2
    shots: int = 1000
    t1_us: float = 120.0
    t2_us: float = 90.0
    gate_error_1q: float = 0.001
    gate_error_2q: float = 0.01


@dataclass
class RuntimeConfig:
    use_quantum_routing_by_default: bool = True
    enable_qiskit_stage: bool = True
    max_send_retries: int = 4
    tabu_backtrack_hops: int = 2
    max_visits_per_node: int = 2
