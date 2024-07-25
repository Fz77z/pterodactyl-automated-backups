import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

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
