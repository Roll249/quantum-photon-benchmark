# Paper-Ready Snippets (Burst 600s, 5 Seeds, Cached Quantum)

## Abstract (ready-to-edit)
Low Earth Orbit (LEO) satellite routing is vulnerable to early congestion collapse under dynamic and bursty traffic. We present a constraint-aware continuous-time quantum walk (CTQW) routing framework with anti-loop forwarding guards and a topology-signature routing-table cache. In a 600-second burst-traffic benchmark (burst multiplier 3x at 300-360s, 5 random seeds), the proposed method achieves substantially higher reliability than the classical baseline: packet delivery ratio (PDR) improves from 0.0797 +/- 0.0175 to 0.7784 +/- 0.0062, while average delay decreases from 0.2226 +/- 0.0032 s to 0.1368 +/- 0.0015 s. Cache reuse reaches 0.7167 +/- 0.0000 hit rate and reduces quantum decision overhead to 29.05 +/- 7.34 ms, supporting practical online deployment.

## Results paragraph (Evaluation section)
Table 1 summarizes the 5-seed burst benchmark. Quantum+Cache improves end-to-end reliability by 9.77x versus baseline (PDR: 0.7784 vs 0.0797) and reduces average delay by 38.54% (0.1368 s vs 0.2226 s). The decision latency remains low (29.05 ms on average), with cache hit rate of 71.67%. Time-series analysis further shows distinct resilience under overload: during the burst window (300-360s), baseline window-PDR stays near collapse (mean 0.0669), whereas Quantum+Cache maintains substantially higher successful forwarding (mean 0.6805), then remains stable post-burst.

## Figure caption (Hero chart)
Figure X. Cumulative PDR over time under burst traffic (mean +/- 1 sigma across 5 seeds). A 3x traffic burst is injected between t=300s and t=360s (shaded region). The classical baseline remains in an early-collapse regime with persistently low delivery, while Quantum+Cache exhibits graceful degradation during the burst and stable post-burst recovery. Shaded error bands indicate low cross-seed variance for the quantum method.

## Threats-to-validity paragraph
The baseline in this study is a non-adaptive classical forwarding policy and may underestimate stronger deterministic routing baselines under identical runtime constraints. Results are obtained in a simulation environment with abstracted PHY/queue models and do not directly represent hardware QPU execution time. Therefore, absolute latencies should be interpreted as simulation-level runtime indicators, while comparative trends (reliability, delay, and burst resilience) are the primary empirical claim.

## Reproducibility note
All core aggregated artifacts are provided in:
- experiments/output/burst_traffic_600s_cached_multiseed_summary.csv
- experiments/output/burst_traffic_600s_cached_multiseed_timeseries.csv
- experiments/output/burst_traffic_600s_cached_multiseed_hero.png
