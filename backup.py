import logging
from api_request import make_request
from alert import send_email
from dotenv import load_dotenv
import requests
import os
import time

# Configure the logging to output to a file
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s', filename='backup.log')

load_dotenv()
API_KEY = os.environ.get("API_KEY")

def backup_servers(server_ids):
    failed_servers = []
    
    if not server_ids:
        logging.error("ERROR could not find eligible for backing up.")
        send_email(
            os.environ.get("EMAIL_SUBJECT"),
            os.environ.get("EMAIL_BODY"),
            os.environ.get("TO_EMAIL"),
            os.environ.get("FROM_EMAIL"),
            os.environ.get("FROM_PASSWORD"), 
        )
        return
    
    for server_id in server_ids:
        try:
            backupsurl = os.environ.get("BACKUPS_URL")
            formaturl = str(backupsurl + server_id)
            url = f"{formaturl}/backups"
            headers = {"Authorization": API_KEY}
            
            backup = requests.post(url, data='', headers=headers)
            
            if backup.status_code == 200:
                logging.info(f"Backup succeeded for server {server_id}. Status code: {backup.status_code}")
                time.sleep(3)
            else:
                failed_servers.append(server_id)
                logging.error(f"Backup failed for server {server_id}. Error code: {backup.status_code}")
                time.sleep(30)
        except requests.exceptions.RequestException as e:
            logging.error(f"An error occurred while making the backup request for server {server_id}: {str(e)}")
            failed_servers.append(server_id)
            time.sleep(30)
            
    retry_failed_servers(failed_servers, headers)

def retry_failed_servers(failed_servers, headers):
    for server_id in failed_servers:
        try:
            backupsurl = os.environ.get("BACKUPS_URL")
            formaturl = str(backupsurl + server_id)
            url = f"{formaturl}/backups"
            retry = requests.post(url, data='', headers=headers)
            
            if retry.status_code == 200:
                logging.info(f"Retry succeeded for server {server_id}. Status code: {retry.status_code}")
                time.sleep(5)
            else:
                logging.error(f"Retry failed for server {server_id}. Error code: {retry.status_code}")
                send_email(
                os.environ.get("EMAIL_SUBJECT"),
                os.environ.get("EMAIL_BODY"),
                os.environ.get("TO_EMAIL"),
                os.environ.get("FROM_EMAIL"),
                os.environ.get("FROM_PASSWORD"), 
        ) 
        except requests.exceptions.RequestException as e:
            logging.error(f"An error occurred while retrying the backup request for server {server_id}: {str(e)}")
            send_email(
            os.environ.get("EMAIL_SUBJECT"),
            os.environ.get("EMAIL_BODY"),
            os.environ.get("TO_EMAIL"),
            os.environ.get("FROM_EMAIL"),
            os.environ.get("FROM_PASSWORD"), 
        ) 

server_ids = make_request()
backup_servers(server_ids)
