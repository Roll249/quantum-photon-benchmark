from dataclasses import dataclass, asdict


@dataclass
class SimulationMetrics:
    generated: int = 0
    arrived: int = 0
    dropped: int = 0
    total_delay: float = 0.0
    decision_count: int = 0
    decision_time_total_s: float = 0.0
    loop_avoided: int = 0
    retry_events: int = 0
    drop_no_route: int = 0
    drop_retry_exceeded: int = 0

    def record_generated(self, count: int = 1) -> None:
        self.generated += count

    def record_arrived(self, delay_s: float) -> None:
        self.arrived += 1
        self.total_delay += delay_s

    def record_dropped(self, delay_s: float) -> None:
        self.dropped += 1
        self.total_delay += delay_s

    def record_decision_time(self, duration_s: float) -> None:
        self.decision_count += 1
        self.decision_time_total_s += duration_s

    def record_loop_avoided(self) -> None:
        self.loop_avoided += 1

    def record_retry_event(self) -> None:
        self.retry_events += 1

    def record_drop_no_route(self) -> None:
        self.drop_no_route += 1

    def record_drop_retry_exceeded(self) -> None:
        self.drop_retry_exceeded += 1

    @property
    def pdr(self) -> float:
        if self.generated == 0:
            return 0.0
        return self.arrived / self.generated

    @property
    def average_delay_s(self) -> float:
        completed = self.arrived + self.dropped
        if completed == 0:
            return 0.0
        return self.total_delay / completed

    @property
    def average_decision_time_s(self) -> float:
        if self.decision_count == 0:
            return 0.0
        return self.decision_time_total_s / self.decision_count

    def to_dict(self) -> dict:
        data = asdict(self)
        data.update(
            {
                "pdr": self.pdr,
                "average_delay_s": self.average_delay_s,
                "average_decision_time_s": self.average_decision_time_s,
            }
        )
        return data
