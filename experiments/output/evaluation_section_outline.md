# Evaluation Section Outline (Ready-to-Paste)

## 4.1 Setup
- Simulator: SatSIM event-driven LEO network.
- Scenario: 600s run, burst traffic x3 at t=300-360s.
- Seeds: 5 random seeds {7, 11, 13, 17, 19}.
- Metrics: PDR, average delay, decision runtime, cache hit rate, PDR(t).

## 4.2 Main Quantitative Results
- Refer to Table 1 (tab:burst-main).
- Key claim: Quantum+Cache improves reliability by 9.77x and reduces delay by 38.54% versus baseline.
- Practical runtime: 29.05 +/- 7.34 ms decision overhead with 71.67% cache hit rate.

## 4.3 Temporal Robustness Under Burst
- Refer to Figure X (hero plot).
- Baseline remains in early congestion-collapse regime.
- Quantum+Cache shows graceful degradation during burst and stable post-burst behavior.
- Burst-window average instantaneous forwarding quality:
  - Baseline window-PDR mean: 0.0669
  - Quantum window-PDR mean: 0.6805

## 4.4 Discussion
- Why gains happen: global reweighting + anti-loop forwarding + cache reuse.
- Why this is practical: runtime overhead is now in tens-of-ms range.
- Scope of claims: simulation-level evidence; hardware-QPU latency not directly measured.
