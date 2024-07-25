import logging
import os
import smtplib
import sys
from email.message import EmailMessage
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv

__all__ = ["logger", "API_KEY", "GET_URL", "SERVERS_URL", "MAX_RETRIES", "RETRY_BACKOFF_FACTOR", "ROTATE", "POST_BACKUP_SCRIPT"]

# Environment .env
load_dotenv()

# Logger
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
MAX_LOG_FILE_BYTES = 500000
BACKUP_COUNT = 15
LOG_LEVEL = logging.__getattribute__(os.getenv("LOG_LEVEL") or "ERROR")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# console log (stderr)
handler = logging.StreamHandler(stream=sys.stderr)
handler.setLevel(LOG_LEVEL)
handler.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(handler)

# file logger
handler = RotatingFileHandler(
    "backup.log", maxBytes=MAX_LOG_FILE_BYTES, backupCount=BACKUP_COUNT
)
handler.setLevel(logging.INFO)  # log file log level is always INFO
handler.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(handler)

# API key stuff
API_KEY = os.getenv("API_KEY") or ""
GET_URL = os.getenv("GET_URL") or ""
SERVERS_URL = os.getenv("SERVERS_URL") or ""
MAX_RETRIES = int(os.getenv("MAX_RETRIES") or "") or 5
RETRY_BACKOFF_FACTOR = int(os.getenv("RETRY_BACKOFF_FACTOR") or "0") or 1
SEND_EMAILS = (str(os.getenv("SEND_EMAILS") or "").lower() or "true") == "true"
ROTATE = (str(os.getenv("ROTATE") or "").lower() or "false") == "true"
POST_BACKUP_SCRIPT = os.getenv("POST_BACKUP_SCRIPT")   # Optional



class EmailAlert:
    def __init__(self, from_email, from_password, smtp_server, smtp_port):
        self.from_email = from_email
        self.from_password = from_password
        self.smtp_server = smtp_server
        self.smtp_port = int(smtp_port)

    def anonymize_email(self, email):
        local_part, domain = email.split("@")
        return f"{'*' * len(local_part)}@{domain}"

    def send(self, subject, body, to_email):
        if not all(
                isinstance(i, str)
                for i in [subject, body, to_email, self.from_email, self.from_password]
        ):
            raise ValueError("All parameters must be of type str")

        logger.info(f"Preparing to send email to {self.anonymize_email(to_email)}")

        # Create the email message
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = self.from_email
        msg["To"] = to_email

        try:
            # Connect to the mail server using TLS
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                # Enable TLS encryption
                server.starttls()
                # Log in to your email account
                server.login(self.from_email, self.from_password)

                # Send the email
                server.send_message(msg)
                logger.info(f"Email sent to {self.anonymize_email(to_email)}")
        except smtplib.SMTPException as e:
            logger.error(
                f"SMTP error occurred when sending email to {self.anonymize_email(to_email)}: {e}"
            )
        except Exception as e:
            logger.error(
                f"Unexpected error occurred when sending email to {self.anonymize_email(to_email)}: {e}"
            )


# Instantiate EmailAlert object
email_alert = EmailAlert(
    os.getenv("FROM_EMAIL"),
    os.getenv("FROM_PASSWORD"),
    os.getenv("SMTP_SERVER"),
    os.getenv("SMTP_PORT"),
)


def notify_error():
    if not SEND_EMAILS:
        return

    if not (
            os.getenv("EMAIL_SUBJECT")
            and os.getenv("EMAIL_BODY")
            and os.getenv("TO_EMAIL")
    ):
        logger.error(
            "One or more email environment variables are not set. Can't send notification email."
        )
        return
    email_alert.send(
        os.getenv("EMAIL_SUBJECT"), os.getenv("EMAIL_BODY"), os.getenv("TO_EMAIL")
    )


for required_url in ["API_KEY", "GET_URL", "SERVERS_URL"]:
    if not locals()[required_url]:
        logger.error(f"{required_url} environment variable not set. Can't proceed without it.")
        notify_error()
        exit(1)
