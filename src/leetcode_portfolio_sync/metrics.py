from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class PerformanceMetrics:
    timings: dict[str, list[float]] = field(default_factory=dict)
    counters: dict[str, int] = field(default_factory=dict)

    @contextmanager
    def timer(self, name: str) -> Iterator[None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            self.timings.setdefault(name, []).append(time.perf_counter() - start)

    def increment(self, name: str, amount: int = 1) -> None:
        self.counters[name] = self.counters.get(name, 0) + amount

    def snapshot(self) -> dict[str, object]:
        return {
            "timings": {
                name: {
                    "count": len(values),
                    "avg_ms": (
                        round(sum(values) / len(values) * 1000, 2) if values else 0
                    ),
                    "max_ms": round(max(values) * 1000, 2) if values else 0,
                }
                for name, values in self.timings.items()
            },
            "counters": self.counters,
        }
