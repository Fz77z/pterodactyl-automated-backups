import os
import time
import logging
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")
GET_URL = os.getenv("GET_URL")

# Configure logging
log_file = 'backup.log'
if os.path.exists(log_file):
    os.remove(log_file)

log_format = '%(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)
handler = logging.FileHandler(log_file)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter(log_format))
logger.addHandler(handler)

def validate_env_vars(api_key, url):
    if api_key is None:
        logger.error("API key not found. Please set the API_KEY environment variable.")
        raise ValueError("API key not found")
    if url is None:
        logger.error("URL not found. Please set the GET_URL environment variable.")
        raise ValueError("URL not found")

def get_response(url, headers, max_retries=5, retry_delay_secs=15):
    for retry in range(max_retries):
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response
            else:
                logger.error(f"Error: {response.status_code} - {response.reason}")
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            logger.error(f"Network Error: {str(e)}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Exception: {str(e)}")

        if retry < max_retries - 1:
            logger.info(f"Retrying in {retry_delay_secs} seconds...")
            time.sleep(retry_delay_secs)
        else:
            logger.error("Max retries exceeded.")
            return None

def process_response(response):
    data = response.json()
    server_identifiers = set()
    for item in data['data']:
        identifier = item['attributes']['identifier']
        server_identifiers.add(identifier)
    logger.info(f"Server identifiers: {server_identifiers}")
    return server_identifiers

def main():
    validate_env_vars(API_KEY, GET_URL)
    headers = {"Authorization": API_KEY}
    response = get_response(GET_URL, headers)
    if response:
        return process_response(response)
    else:
        return None

if __name__ == "__main__":
    main()
