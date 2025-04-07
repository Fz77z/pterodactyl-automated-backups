import importlib
import os
import time

from logprise import logger, appriser

from config import LOG_LEVEL, SEND_EMAILS


__all__ = ["notify_error"]

# Add file handler for all logs
logger.add(
    "backup.log",
    rotation="500 KB",
    retention=15,
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
)

# Add file handler for errors only
logger.add(
    "backup_error.log",
    rotation="500 KB",
    retention=5,
    level="ERROR",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {process} - {message}",
)

# Set global log level (filters at the sink level)
if LOG_LEVEL not in [
    "TRACE",
    "DEBUG",
    "INFO",
    "SUCCESS",
    "WARNING",
    "ERROR",
    "CRITICAL",
]:
    logger.warning(f"Invalid LOG_LEVEL {LOG_LEVEL}, defaulting to INFO")
    LOG_LEVEL = "INFO"


def notify_error(error: str = "") -> None:
    """Send error notification via email if enabled."""
    if not SEND_EMAILS:
        return

    subject = os.getenv("EMAIL_SUBJECT", "Backup Error")
    body = os.getenv("EMAIL_BODY", "An error occurred during backup:") + f"\n\n{error}"
    to_email = os.getenv("TO_EMAIL")

    if not to_email:
        logger.error("TO_EMAIL not set, can't send error notification")
        return

    logger.info(
        f"Sending error notification: {error[:50]}{'...' if len(error) > 50 else ''}"
    )

    from_email = os.getenv("FROM_EMAIL", "")
    from_password = os.getenv("FROM_PASSWORD", "")
    smtp_server = os.getenv("SMTP_SERVER", "")
    smtp_port = os.getenv("SMTP_PORT", "587")

    mail_url = (
        f"mailto://{from_email}:{from_password}@{smtp_server}:{smtp_port}/"
        f"?from={from_email}&to={to_email}"
    )

    appriser.add(mail_url)

    try:
        result = appriser.notify(title=subject, body=body)
        if not result:
            logger.error("Failed to send notification email")
    except Exception as e:
        logger.exception(f"Error sending notification: {e}")


def _check_required(name: str) -> None:
    """Check that required configuration variables are set."""
    mod = importlib.import_module("config")
    if name not in mod.__dict__ or not mod.__dict__[name]:
        err_msg = (
            f"{name} environment variable missing. Please set it in your .env file."
        )
        logger.error(err_msg)
        notify_error(err_msg)
        exit(1)


# Initialize and validate configuration
logger.info(f"Initializing with log level: {LOG_LEVEL}")
start_time = time.time()

_check_required("API_KEY")
_check_required("GET_URL")
_check_required("SERVERS_URL")

if SEND_EMAILS:
    logger.info("Email notifications enabled, checking email configuration")
    _check_required("FROM_EMAIL")
    _check_required("SMTP_SERVER")
    _check_required("SMTP_PORT")
    _check_required("TO_EMAIL")
else:
    logger.info("Email notifications disabled")

logger.debug(f"Initialization completed in {time.time() - start_time:.3f}s")
