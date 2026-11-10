from __future__ import annotations

from dataclasses import dataclass
import shutil


@dataclass(frozen=True)
class ToolchainStatus:
    language: str
    available: bool
    executable: str | None
    reason: str | None = None


def check(language: str) -> ToolchainStatus:
    command = {"c": "clang", "java": "javac", "python": "python"}.get(language)
    if command is None:
        return ToolchainStatus(language, False, None, "unsupported language")
    path = shutil.which(command)
    return ToolchainStatus(language, bool(path), path, None if path else f"{command} unavailable")
