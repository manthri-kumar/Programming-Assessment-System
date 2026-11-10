from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock
from time import monotonic


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after: int


class RateLimiter:
    def __init__(self, limits: dict[str, int] | None = None, window_seconds: int = 60) -> None:
        self.limits = {"auth": 100, "submission": 60, "evaluation": 60, "import": 20, "extraction": 20, **(limits or {})}
        if window_seconds < 1 or any(value < 1 for value in self.limits.values()):
            raise ValueError("rate limits and window must be positive")
        self.window_seconds = window_seconds
        self._events: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, bucket: str, identity: str) -> RateLimitDecision:
        limit = self.limits[bucket]
        now = monotonic()
        cutoff = now - self.window_seconds
        key = (bucket, identity)
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                retry = max(1, int(self.window_seconds - (now - events[0]) + 0.999))
                return RateLimitDecision(False, retry)
            events.append(now)
            return RateLimitDecision(True, 0)

