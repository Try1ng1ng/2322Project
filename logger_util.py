from __future__ import annotations

import logging
from pathlib import Path


LOG_PATH = Path(__file__).resolve().parent / "logs" / "server.log"


def setup_logger() -> logging.Logger:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("comp2322_web_server")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    return logger


LOGGER = setup_logger()


def write_access_log(
    client_ip: str,
    access_time: str,
    method: str,
    path: str,
    version: str,
    status_code: int,
) -> None:
    # One request maps to one line in the log file.
    log_line = (
        f"{client_ip} | {access_time} | {method} {path} {version} | {status_code}"
    )
    LOGGER.info(log_line)
