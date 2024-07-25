import importlib
import logging.config
import os

from alert import EmailAlert
from config import LOG_LEVEL, SEND_EMAILS

__all__ = ["notify_error"]

LOGGING_CONFIG = {
    "version": 1,
    "formatters": {"standard": {"format": "%(asctime)s - %(levelname)s - %(message)s"}},
    "handlers": {
        "default": {
            "level": "DEBUG",
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "standard",
            "filename": "backup.log",
            "maxBytes": 500000,
            "backupCount": 15,
        },
    },
    "loggers": {"": {"level": LOG_LEVEL, "handlers": ["default", "file"]}},
}
logging.config.dictConfig(LOGGING_CONFIG)


def notify_error(error: str = "") -> None:
    if not SEND_EMAILS:
        return

    EmailAlert().send(
        os.getenv("EMAIL_SUBJECT"),
        os.getenv("EMAIL_BODY") + f"\n\n{error}",
        os.getenv("TO_EMAIL"),
    )


def _check_required(name: str) -> None:
    mod = importlib.import_module("config")
    if name not in mod or not mod[name]:
        logging.getLogger(__name__).error(
            f"{name} environment variable missing. Please set it in your .env file."
        )
        notify_error()
        exit(1)


_check_required("API_KEY")
_check_required("GET_URL")
_check_required("SERVERS_URL")

if SEND_EMAILS:
    _check_required("FROM_EMAIL")
    _check_required("SMTP_SERVER")
    _check_required("SMTP_PORT")

    _check_required("EMAIL_SUBJECT")
    _check_required("EMAIL_BODY")
    _check_required("TO_EMAIL")
