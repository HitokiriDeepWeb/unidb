import logging
from collections.abc import Callable
from logging.config import dictConfig
from pathlib import Path

from core.models import LogType


def level_filter_maker(level: str) -> Callable:
    """Filter to not repeat same level messages in different log files."""
    level_priority = getattr(logging, level)

    def filter(record: logging.LogRecord) -> bool:
        return record.levelno < level_priority

    return filter


logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{name} {levelname} {asctime} {module} "
            "{process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "filters": {
        "level_filter": {
            "()": f"{__name__}.level_filter_maker",
            "level": "WARNING",
        }
    },
    "handlers": {
        "debug_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "backupCount": 5,
            "maxBytes": 10**7,
            "formatter": "verbose",
            "filename": "",
            "level": "DEBUG",
            "filters": ["level_filter"],
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "backupCount": 5,
            "maxBytes": 10**7,
            "formatter": "verbose",
            "filename": "",
            "level": "WARNING",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "level": "DEBUG",
        },
    },
    "loggers": {
        "": {
            "handlers": [],
            "level": "",
            "propagate": True,
        },
    },
}


def setup_logging(
    log_path: Path, log_level: str, log_type: LogType, verbose: bool
) -> logging.Logger:
    """Setup logging config according to provided values."""
    validated_log_level = _validate_log_level(log_level)
    _set_log_level(validated_log_level)
    _set_log_path(log_path, log_type)
    _set_formatter(verbose)
    _set_log_handler(log_type, log_path)
    _set_file_log_path(log_type, log_path)

    dictConfig(logging_config)

    # log warnings to track deprecation warnings and others.
    logging.captureWarnings(capture=True)
    return logging.getLogger(__name__)


def _validate_log_level(log_level: str) -> str:
    upper_log_level = log_level.upper()

    match upper_log_level:
        case "INFO":
            return upper_log_level
        case "ERROR":
            return upper_log_level
        case "DEBUG":
            return upper_log_level
        case "WARNING":
            return upper_log_level
        case "CRITICAL":
            return upper_log_level
        case _:
            raise ValueError(f"Invalid level name: {upper_log_level}")


def _set_log_level(log_level: str) -> None:
    logging_config["loggers"][""]["level"] = log_level


def _set_file_log_path(log_type: LogType, log_path: Path | None) -> None:
    if log_path and log_type == LogType.FILE:
        logging_config["handlers"]["debug_file"]["filename"] = log_path / "debug.log"
        logging_config["handlers"]["error_file"]["filename"] = log_path / "error.log"
    else:
        logging_config["handlers"].pop("debug_file")
        logging_config["handlers"].pop("error_file")


def _set_log_handler(log_type: LogType, log_path: Path | None) -> None:
    if log_path and log_type == LogType.FILE:
        logging_config["loggers"][""]["handlers"] = ["debug_file", "error_file"]
    else:
        logging_config["loggers"][""]["handlers"] = ["console"]


def _set_log_path(log_path: Path, log_type: LogType) -> None:
    if log_type == LogType.FILE:
        log_path.mkdir(parents=True, exist_ok=True)


def _set_formatter(verbose: bool) -> None:
    if not verbose:
        logging_config["handlers"]["debug_file"]["formatter"] = "simple"
        logging_config["handlers"]["error_file"]["formatter"] = "simple"
        logging_config["handlers"]["console"]["formatter"] = "simple"
