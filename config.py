import os

from dotenv import load_dotenv

__all__ = [
    "API_KEY",
    "SEND_EMAILS",
    "GET_URL",
    "SERVERS_URL",
    "MAX_RETRIES",
    "RETRY_BACKOFF_FACTOR",
    "ROTATE",
    "POST_BACKUP_SCRIPT",
    "LOG_LEVEL",
]


# Environment .env
load_dotenv()

# API key stuff
API_KEY = os.getenv("API_KEY") or ""
GET_URL = os.getenv("GET_URL") or ""
SERVERS_URL = os.getenv("SERVERS_URL") or ""
MAX_RETRIES = int(os.getenv("MAX_RETRIES") or "5") or 5
RETRY_BACKOFF_FACTOR = int(os.getenv("RETRY_BACKOFF_FACTOR") or "0") or 1
SEND_EMAILS = (str(os.getenv("SEND_EMAILS") or "").lower() or "true") == "true"
ROTATE = (str(os.getenv("ROTATE") or "").lower() or "false") == "true"
POST_BACKUP_SCRIPT = os.getenv("POST_BACKUP_SCRIPT")  # Optional
LOG_LEVEL = os.getenv("LOG_LEVEL") or "ERROR"

EMAIL_SUBJECT = os.getenv("EMAIL_SUBJECT")
EMAIL_BODY = os.getenv("EMAIL_BODY")
TO_EMAIL = os.getenv("TO_EMAIL")
