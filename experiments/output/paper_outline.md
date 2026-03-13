# Paper Outline (Burst-Traffic Quantum Routing in LEO SatNet)

## Title (draft)
**Quantum-Inspired Routing with Cache-Accelerated Decisions for Congestion-Resilient LEO Satellite Networks**

## Abstract (4-part skeleton)
1. **Problem:** Classical shortest-path routing suffers early congestion collapse under dynamic LEO traffic.
2. **Method:** We propose CTQW-based routing with constraint-aware penalties and a routing-table cache keyed by topology signature.
3. **Results:** In 600s burst experiments (5 seeds, burst x3 at t=300s), quantum routing sustains substantially higher reliability.
4. **Impact:** Cache reduces decision overhead to practical levels while preserving resilience under burst load.

## 1. Introduction
- Motivation: LEO networks are highly dynamic and vulnerable to congestion hotspots.
- Gap: Shortest-path greedy routing ignores global interference-like traffic effects.
- Contributions:
  - Constraint-aware CTQW routing integrated into event-driven SatSIM.
  - Anti-loop forwarding policy with retry/drop guards.
  - Topology-signature routing cache for latency reduction.
  - Multi-seed burst benchmark with mean/std and time-series variance.

## 2. System & Methodology
### 2.1 Simulator and Network Model
- Event-driven SatSIM, 66-satellite Iridium-like graph.
- Dynamic links and mobility updates.

### 2.2 Quantum-Inspired Routing Core
- Hamiltonian from graph Laplacian.
- Penalty matrix for delay/bandwidth/energy constraints.
- Time-evolved probability guidance to build weighted routing actions.

### 2.3 Runtime Stabilization
- Anti-loop/no-backtrack and per-node revisit cap.
- Retry cap and deterministic drop reasons.

### 2.4 Routing Table Cache
- LRU cache over discretized topology signature.
- Reuse prior quantum decisions when topology state is similar.

## 3. Experimental Setup
- Scenario: 600s simulation, burst x3 at t=300–360s.
- Seeds: 5 seeds {7,11,13,17,19}.
- Baselines: Randomized classical forwarding table (proxy for non-adaptive classical).
- Metrics:
  - Global: PDR, average delay, decision overhead.
  - Temporal: cumulative PDR(t), window PDR(t), queue depth.
  - Efficiency: cache hit rate.

## 4. Results
### 4.1 Main Quantitative Table (5-seed mean ± std)
- Source: `burst_traffic_600s_cached_multiseed_summary.csv`.
- Key numbers:
  - Baseline: PDR = 0.0797 ± 0.0175; Delay = 0.2226 ± 0.0032 s.
  - Quantum+Cache: PDR = 0.7784 ± 0.0062; Delay = 0.1368 ± 0.0015 s.
  - Quantum decision time = 0.0291 ± 0.0073 s.
  - Cache hit rate = 0.7167 ± 0.0000.

### 4.2 Hero Figure
- Figure: `burst_traffic_600s_cached_multiseed_hero.png`.
- Interpretation:
  - Baseline remains in low-PDR regime (early congestion collapse).
  - Quantum shows graceful degradation during burst and stable post-burst behavior.
  - Shaded ±1σ bands show robustness across seeds.

### 4.3 Cache Ablation Narrative
- Compare uncached vs cached quantum runs:
  - Overhead reduced from ~0.074s to ~0.020–0.030s per decision (depending on seed/run).
  - Reliability remains high while compute latency decreases.

## 5. Discussion
- Why baseline fails early: bottleneck amplification and lack of adaptive rerouting.
- Why quantum-guided routing helps: broader path exploration and dynamic reweighting.
- Practicality: ~20–30 ms decision latency is plausible for near-real-time control loops.

## 6. Threats to Validity
- Baseline choice can be further strengthened with deterministic Dijkstra-on-current-graph per-interval.
- Simulator assumptions (queue model, PHY abstractions) may affect absolute values.
- Real hardware/QPU execution not directly measured in this study.

## 7. Conclusion
- Quantum+Cache routing materially improves reliability and delay under burst traffic in dynamic LEO settings.
- Multi-seed variance analysis supports robustness of the observed gains.

## Appendix / Reproducibility
- Main burst command:
  - `python experiments/burst_traffic_benchmark.py --seconds 600 --seed <seed> --packet-interval 0.2 --burst-start 300 --burst-duration 60 --burst-multiplier 3 --output-prefix experiments/output/burst_traffic_600s_seed<seed>_cached`
- Aggregated outputs:
  - `experiments/output/burst_traffic_600s_cached_multiseed_summary.csv`
  - `experiments/output/burst_traffic_600s_cached_multiseed_timeseries.csv`
  - `experiments/output/burst_traffic_600s_cached_multiseed_hero.png`
