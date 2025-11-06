from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class LogType(StrEnum):
    """Logging type. Save logs to the file or print them to the console."""

    CONSOLE = "console"
    FILE = "file"


@dataclass(frozen=True, slots=True)
class FunctionCall:
    """Store callable with its args and kwargs."""

    func: Callable
    args: tuple = ()
    kwargs: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LogConfig:
    log_type: LogType
    log_path: Path
    log_level: str
    verbose: bool
