import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.request_context import request_id_var


BASE_DIR = Path(__file__).resolve().parents[2]

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "devtrack.log"


class RequestIDFilter(logging.Filter):

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def configure_logging() -> None:

    log_format = (
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "request_id=%(request_id)s | "
        "%(message)s"
    )

    formatter = logging.Formatter(log_format)

    request_id_filter = RequestIDFilter()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(request_id_filter)

    file_handler = RotatingFileHandler(
        filename=LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(request_id_filter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if not any(
        getattr(handler, "_devtrack_handler", False)
        for handler in root_logger.handlers
    ):
        console_handler._devtrack_handler = True
        file_handler._devtrack_handler = True

        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)