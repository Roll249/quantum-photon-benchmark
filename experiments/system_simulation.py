import argparse
import csv
import random
import sys
from pathlib import Path

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


def run_mode(mode: str, sim_seconds: int, seed: int, packet_interval_s: float) -> dict:
    random.seed(seed)
    net = SatNet()
    net.packet_generation_interval = packet_interval_s
    net.reset()

    rounds = int(sim_seconds / net.decision_interval)
    for _ in range(rounds):
        if mode == "quantum":
            net.step(actions=None)
        else:
            actions = build_random_actions(net)
            net.step(actions=actions)

    result = net.metrics.to_dict()
    result["mode"] = mode
    result["sim_seconds"] = sim_seconds
    result["decision_interval"] = net.decision_interval
    result["packet_interval_s"] = packet_interval_s
    result["rounds"] = rounds
    result["arrived_packets"] = len(net.packetsArrived)
    result["dropped_packets"] = len(net.packet_drop)
    return result


def write_csv(output_path: Path, rows: list[dict]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "mode",
        "sim_seconds",
        "decision_interval",
        "packet_interval_s",
        "rounds",
        "generated",
        "arrived",
        "dropped",
        "arrived_packets",
        "dropped_packets",
        "pdr",
        "average_delay_s",
        "decision_count",
        "decision_time_total_s",
        "average_decision_time_s",
        "total_delay",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SatSIM baseline vs quantum routing simulation.")
    parser.add_argument("--seconds", type=int, default=600, help="Simulation time in seconds (default: 600)")
    parser.add_argument("--seed", type=int, default=7, help="Random seed")
    parser.add_argument(
        "--packet-interval",
        type=float,
        default=0.2,
        help="Packet generation interval in seconds (default: 0.2)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="experiments/output/system_metrics.csv",
        help="Output CSV path",
    )
    args = parser.parse_args()

    baseline = run_mode("baseline", args.seconds, args.seed, args.packet_interval)
    quantum = run_mode("quantum", args.seconds, args.seed, args.packet_interval)

    rows = [baseline, quantum]
    output_path = ROOT / args.output
    write_csv(output_path, rows)

    print("=== System Simulation Results ===")
    for row in rows:
        print(
            f"mode={row['mode']} pdr={row['pdr']:.4f} "
            f"avg_delay={row['average_delay_s']:.6f}s "
            f"avg_decision_time={row['average_decision_time_s']:.6f}s"
        )
    print(f"saved: {output_path}")


if __name__ == "__main__":
    main()