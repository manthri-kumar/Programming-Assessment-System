"""
Base Agent.

Common interface and lightweight execution logging for all agents in
the pipeline (Evaluation Agent, Feedback Agent), per Section 27.
"""

from typing import Any


class BaseAgent:
    """Base class for all pipeline agents."""

    name: str = "BaseAgent"

    def __init__(self) -> None:
        self._log_lines: list[str] = []

    def log(self, message: str) -> None:
        """Record a log line and print it immediately for visibility."""
        line = f"    {message}"
        self._log_lines.append(line)
        print(line)

    def log_header(self, step_number: int, title: str) -> None:
        line = f"[{step_number}] {title}"
        self._log_lines.append(line)
        print(line)

    def get_log(self) -> list[str]:
        return list(self._log_lines)

    def run(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("Subclasses must implement run().")