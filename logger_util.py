from __future__ import annotations

import logging
from pathlib import Path


# Store all access records in logs/server.log.
LOG_PATH = Path(__file__).resolve().parent / "logs" / "server.log"


def setup_logger() -> logging.Logger:
    # Create the logs directory automatically before writing records.
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("comp2322_web_server")
    if logger.handlers:
        # Reuse the existing logger so repeated imports do not add duplicate handlers.
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Keep the log format simple because each request must occupy one line.
    handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    return logger


LOGGER = setup_logger()


def write_access_log(
    client_ip: str,
    access_time: str,
    method: str,
    requested_file_name: str,
    response_type: str,
) -> None:
    # One request maps to one line in the log file.
    log_line = (
        f"{client_ip} | {access_time} | {method} {requested_file_name} | {response_type}"
    )
    LOGGER.info(log_line)
