import logging
from dotenv import load_dotenv
import requests
import os
import time

# Clear the log file from previous executions
log_file = 'backup.log'
if os.path.exists(log_file):
    os.remove(log_file)

# Configure the logging format
log_format = '%(levelname)s - %(message)s'

# Configure the root logger
logging.basicConfig(level=logging.INFO, format=log_format)

# Create a file handler to log to a file
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(log_format))

# Add the file handler to the root logger
logging.getLogger('').addHandler(file_handler)


def validate_api_key(api_key):
    if api_key is None:
        logging.error("API key not found. Please set the API_KEY environment variable.")
        raise ValueError("API key not found")


def make_request():
    max_retries = 5
    retry_delay_secs = 15
    previous_status_code = None

    for retry in range(max_retries):
        try:
            load_dotenv()
            api_key = os.environ.get("API_KEY")
            geturl = os.environ.get("GET_URL")
            validate_api_key(api_key)

            # Make Request
            url = str(geturl)
            headers = {"Authorization": api_key}

            response = requests.get(url, headers=headers)
            server_identifiers = []

            # Check if the response was successful
            if response.status_code == 200:
                # Extract the JSON data from the response
                data = response.json()

                # Check for status code change
                if previous_status_code == 429:
                    logging.info("Status code changed from 429 to 200")

                # Initialize a set to store unique server identifiers
                server_identifiers = set()

                # Loop through the "data" objects
                for item in data['data']:
                    identifier = item['attributes']['identifier']
                    server_identifiers.add(identifier)

                logging.info(f"Server identifiers: {server_identifiers}")  # Log server identifiers

                return server_identifiers
            else:
                # Handle the error response
                logging.error(f"Error: {response.status_code} - {response.reason}")

            previous_status_code = response.status_code

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            # Handle timeout or connection error exceptions
            logging.error(f"Network Error: {str(e)}")

        except requests.exceptions.RequestException as e:
            # Handle general request exceptions
            logging.error(f"Request Exception: {str(e)}")

        if retry < max_retries - 1:
            # Retry after a delay
            logging.info(f"Retrying in {retry_delay_secs} seconds...")
            time.sleep(retry_delay_secs)
        else:
            # Ran out of retries
            logging.error("Max retries exceeded.")

    return None
