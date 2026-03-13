import argparse
import csv
import random
import sys
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SatSIM.satnet import SatNet


def build_random_actions(net: SatNet) -> dict:
    actions = {}
    nodes = list(net.nodes)
    for node in nodes:
        successors = list(net.successors(node))
        fallback = random.choice(successors) if successors else node
        node_actions = {}
        for dst in nodes:
            if dst == node:
                node_actions[dst] = node
            elif successors:
                node_actions[dst] = random.choice(successors)
            else:
                node_actions[dst] = fallback
        actions[node] = node_actions
    return actions


def run_mode(
    mode: str,
    sim_seconds: int,
    seed: int,
    packet_interval_s: float,
    burst_start_s: int,
    burst_duration_s: int,
    burst_multiplier: float,
):
    random.seed(seed)
    net = SatNet()
    net.packet_generation_interval = packet_interval_s
    net.init_num_packet = 0
    net.reset()
    net.configure_burst_traffic(
        enabled=True,
        start_s=burst_start_s,
        duration_s=burst_duration_s,
        multiplier=burst_multiplier,
    )

    rounds = int(sim_seconds / net.decision_interval)
    timeline = []
    cumulative_generated = 0
    cumulative_arrived = 0
    cumulative_dropped = 0

    for step_idx in range(rounds):
        elapsed_s = (step_idx + 1) * net.decision_interval
        in_burst = burst_start_s <= elapsed_s < (burst_start_s + burst_duration_s)
        if mode == "quantum":
            net.step(actions=None)
        else:
            actions = build_random_actions(net)
            net.step(actions=actions)

        ws = net.flush_window_stats()
        cumulative_generated += ws["generated"]
        cumulative_arrived += ws["arrived"]
        cumulative_dropped += ws["dropped"]
        cumulative_pdr = (cumulative_arrived / cumulative_generated) if cumulative_generated > 0 else 0.0
        cache_total = ws["cache_hits"] + ws["cache_misses"]
        cache_hit_rate = (ws["cache_hits"] / cache_total) if cache_total > 0 else 0.0
        timeline.append(
            {
                "mode": mode,
                "seed": seed,
                "time_s": elapsed_s,
                "in_burst": in_burst,
                "window_generated": ws["generated"],
                "window_arrived": ws["arrived"],
                "window_dropped": ws["dropped"],
                "window_pdr": ws["window_pdr"],
                "cumulative_generated": cumulative_generated,
                "cumulative_arrived": cumulative_arrived,
                "cumulative_dropped": cumulative_dropped,
                "cumulative_pdr": cumulative_pdr,
                "queue_depth": ws["queue_depth"],
                "cache_hits": ws["cache_hits"],
                "cache_misses": ws["cache_misses"],
                "cache_hit_rate": cache_hit_rate,
            }
        )

    summary = net.metrics.to_dict()
    total_cache = net.cache_hits + net.cache_misses
    summary.update(
        {
            "mode": mode,
            "seed": seed,
            "sim_seconds": sim_seconds,
            "packet_interval_s": packet_interval_s,
            "burst_start_s": burst_start_s,
            "burst_duration_s": burst_duration_s,
            "burst_multiplier": burst_multiplier,
            "cache_hits": net.cache_hits,
            "cache_misses": net.cache_misses,
            "cache_hit_rate": (net.cache_hits / total_cache) if total_cache > 0 else 0.0,
        }
    )
    return summary, timeline


def write_timeline_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_summary_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def plot_pdr_linechart(path: Path, timeline: list[dict], burst_start_s: int, burst_end_s: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    by_mode = {}
    for row in timeline:
        by_mode.setdefault(row["mode"], []).append(row)

    plt.figure(figsize=(10, 5))
    for mode, rows in sorted(by_mode.items()):
        rows = sorted(rows, key=lambda r: r["time_s"])
        x = [r["time_s"] for r in rows]
        y = [r["cumulative_pdr"] for r in rows]
        plt.plot(x, y, marker="o", linewidth=1.8, markersize=3, label=mode)

    plt.axvspan(burst_start_s, burst_end_s, alpha=0.15, color="red", label="burst window")
    plt.xlabel("Time (s)")
    plt.ylabel("Cumulative PDR")
    plt.title("Cumulative PDR over Time under Burst Traffic")
    plt.ylim(0.0, 1.05)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


def parse_args():
    parser = argparse.ArgumentParser(description="Burst traffic benchmark with PDR timeline.")
    parser.add_argument("--seconds", type=int, default=600)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--packet-interval", type=float, default=0.2)
    parser.add_argument("--burst-start", type=int, default=300)
    parser.add_argument("--burst-duration", type=int, default=60)
    parser.add_argument("--burst-multiplier", type=float, default=3.0)
    parser.add_argument("--output-prefix", type=str, default="experiments/output/burst_traffic_600s")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    summary_rows = []
    timeline_rows = []
    for mode in ("baseline", "quantum"):
        summary, timeline = run_mode(
            mode=mode,
            sim_seconds=args.seconds,
            seed=args.seed,
            packet_interval_s=args.packet_interval,
            burst_start_s=args.burst_start,
            burst_duration_s=args.burst_duration,
            burst_multiplier=args.burst_multiplier,
        )
        summary_rows.append(summary)
        timeline_rows.extend(timeline)

    prefix = ROOT / args.output_prefix
    timeline_csv = Path(str(prefix) + "_timeline.csv")
    summary_csv = Path(str(prefix) + "_summary.csv")
    chart_png = Path(str(prefix) + "_pdr_linechart.png")

    write_timeline_csv(timeline_csv, timeline_rows)
    write_summary_csv(summary_csv, summary_rows)
    plot_pdr_linechart(
        chart_png,
        timeline_rows,
        burst_start_s=args.burst_start,
        burst_end_s=args.burst_start + args.burst_duration,
    )

    print("=== Burst Benchmark Summary ===")
    for row in summary_rows:
        print(
            f"mode={row['mode']} pdr={row['pdr']:.4f} "
            f"avg_delay={row['average_delay_s']:.6f}s "
            f"avg_decision_time={row['average_decision_time_s']:.6f}s"
        )
    print(f"timeline: {timeline_csv}")
    print(f"summary:  {summary_csv}")
    print(f"chart:    {chart_png}")


if __name__ == "__main__":
    main()
