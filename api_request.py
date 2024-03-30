import os
import time
import json
import logging
from logging.handlers import RotatingFileHandler
import requests
from dotenv import load_dotenv
from http import HTTPStatus

# Constants
LOG_FILE = 'backup.log'
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
MAX_LOG_FILE_BYTES = 500000
BACKUP_COUNT = 2

# Load and validate environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")
GET_URL = os.getenv("GET_URL")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 5))
RETRY_DELAY_SECS = int(os.getenv("RETRY_DELAY_SECS", 15))

if not API_KEY:
    raise ValueError("API key not found. Please set the API_KEY environment variable.")
if not GET_URL:
    raise ValueError("URL not found. Please set the GET_URL environment variable.")

# Configure logging
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)
handler = RotatingFileHandler(LOG_FILE, maxBytes=MAX_LOG_FILE_BYTES, backupCount=BACKUP_COUNT)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(handler)

def get_session(api_key):
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {api_key}"})
    return session

def get_response(session):
    for retry in range(MAX_RETRIES):
        try:
            response = session.get(GET_URL)
            if response.status_code == HTTPStatus.OK:
                if 'application/json' in response.headers['Content-Type']:
                    return response
                else:
                    logger.error("Invalid API Key - received non-JSON response")
                    raise ValueError("Invalid API Key")
            else:
                logger.error(f"Error: {response.status_code} - {HTTPStatus(response.status_code).phrase}")
                raise requests.exceptions.HTTPError(response.status_code)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            logger.error(f"Network Error: {str(e)}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Exception: {str(e)}")

        if retry < MAX_RETRIES - 1:
            logger.info(f"Retrying in {RETRY_DELAY_SECS} seconds...")
            time.sleep(RETRY_DELAY_SECS)
        else:
            raise requests.exceptions.RetryError("Max retries exceeded.")



def process_response(response):
    try:
        if 'application/json' in response.headers['Content-Type']:
            data = response.json()
            server_identifiers = {item['attributes']['identifier'] for item in data['data']}
            logger.info(f"Server identifiers: {server_identifiers}")
            backup_limits = {item['attributes']['identifier']: item['attributes']['feature_limits']['backups'] for item in data['data']}
           
            return (server_identifiers, backup_limits)
        else:
            logger.error("Received non-JSON response")
            raise ValueError("Received non-JSON response")
    except (ValueError, KeyError):
        logger.error("Error processing response")
        raise
    except json.JSONDecodeError:
        logger.error("Error decoding JSON response")
        raise

def main():
    with get_session(API_KEY) as session:
        response = get_response(session)
        return process_response(response)

if __name__ == "__main__":
    try:
        result = main()
        logger.info(f"Request executed successfully. Result: {result}")
    except Exception as e:
        logger.error(f"Script execution failed: {e}")
