import os
import time
import logging
import requests
from api_request import main as make_request
from alert import send_email
from dotenv import load_dotenv

# Configure the logging to output to a file
log_file = 'backup.log'
log_format = '%(levelname)s - %(message)s'
logging.basicConfig(filename=log_file, level=logging.INFO, format=log_format, filemode='a')  # 'a' stands for append

log_format = '%(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)
handler = logging.FileHandler(log_file)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter(log_format))
logger.addHandler(handler)

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")
BACKUPS_URL = os.getenv("BACKUPS_URL")
SEND_EMAILS = os.getenv("SEND_EMAILS", "True")  # Default to "True" if not set

def notify_error():
    if SEND_EMAILS.lower() == "true":
        send_email(
            os.getenv("EMAIL_SUBJECT"),
            os.getenv("EMAIL_BODY"),
            os.getenv("TO_EMAIL"),
            os.getenv("FROM_EMAIL"),
            os.getenv("FROM_PASSWORD"), 
        )

def backup_servers(server_ids):
    failed_servers = []
    
    if not server_ids:
        logger.error("ERROR could not find servers eligible for backing up.")
        notify_error()
        return
    
    headers = {"Authorization": API_KEY}

    for server_id in server_ids:
        try:
            url = f"{BACKUPS_URL}{server_id}/backups"
            backup = requests.post(url, data='', headers=headers)
            
            if backup.status_code == 200:
                logger.info(f"Backup succeeded for server {server_id}. Status code: {backup.status_code}")
                time.sleep(3)
            else:
                failed_servers.append(server_id)
                logger.error(f"Backup failed for server {server_id}. Error code: {backup.status_code}")
                time.sleep(30)
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred while making the backup request for server {server_id}: {str(e)}")
            failed_servers.append(server_id)
            time.sleep(30)
            
    retry_failed_servers(failed_servers, headers)

def retry_failed_servers(failed_servers, headers):
    for server_id in failed_servers:
        try:
            url = f"{BACKUPS_URL}{server_id}/backups"
            retry = requests.post(url, data='', headers=headers)
            
            if retry.status_code == 200:
                logger.info(f"Retry succeeded for server {server_id}. Status code: {retry.status_code}")
                time.sleep(5)
            else:
                logger.error(f"Retry failed for server {server_id}. Error code: {retry.status_code}")
                notify_error() 
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred while retrying the backup request for server {server_id}: {str(e)}")
            notify_error() 

server_ids = make_request()
backup_servers(server_ids)
