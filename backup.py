import os
import time
import requests
from setup import logger
from api_request import main as make_request
from alert import EmailAlert

API_KEY = f"Bearer {os.getenv('API_KEY')}"
SERVERS_URL = os.getenv("SERVERS_URL")
SEND_EMAILS = os.getenv("SEND_EMAILS", "True")  # Default to "True" if not set
ROTATE = os.getenv("ROTATE", "False")  # Default to "False" if not set
POST_BACKUP_SCRIPT = os.getenv("POST_BACKUP_SCRIPT")  # optional

# Instantiate EmailAlert object
email_alert = EmailAlert(
    os.getenv("FROM_EMAIL"),
    os.getenv("FROM_PASSWORD"),
    os.getenv("SMTP_SERVER"),
    os.getenv("SMTP_PORT"),
)


def notify_error():
    if SEND_EMAILS.lower() == "true":
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


if not API_KEY:
    logger.error("API_KEY environment variable not set. Can't proceed without it.")
    notify_error()
    exit(1)

if not SERVERS_URL:
    logger.error("SERVERS_URL environment variable not set. Can't proceed without it.")
    notify_error()
    exit(1)


# remove backups when limits reached
def remove_old_backup(server):
    headers = {"Authorization": API_KEY}
    server_id = server["attributes"]["identifier"]
    backup_limit = server["attributes"]["feature_limits"]["backups"]
    logger.info(f"  backup limit is {backup_limit}")
    try:
        url = f"{SERVERS_URL}{server_id}/backups"
        response = requests.get(url, data="", headers=headers)

        if response.status_code == 200:
            backups = sorted(
                response.json()["data"], key=lambda b: b["attributes"]["created_at"]
            )

            if len(backups) >= backup_limit:
                # backup limit reached
                # remove oldest N backups
                if backup_limit == 0:
                    N = len(backups)  # remove all backup
                else:
                    N = (
                        len(backups) - backup_limit + 1
                    )  # remove difference and leave space for one more

                for i in range(0, N):
                    # delete oldest backup
                    if backups[i]["attributes"]["is_locked"]:
                        logger.warning(
                            f"  backup {backups[i]['attributes']['name']} is locked, skipping"
                        )
                    else:
                        url = f"{SERVERS_URL}{server_id}/backups/{backups[i]['attributes']['uuid']}"
                        logger.info(
                            f"  removing backup: \"{backups[i]['attributes']['name']}\""
                        )

                        response = requests.delete(url, headers=headers)
                        if response.status_code == 204:
                            logger.info("  -> success")
                        else:
                            logger.info(
                                f"  -> failed with status {response.status_code}"
                            )

                    time.sleep(2)
            else:
                logger.info("  nothing to delete")

    except requests.exceptions.RequestException as e:
        logger.error(
            f"An error occurred while deleting backups from server {server_id}: {str(e)}"
        )


def backup_servers(server_list):
    failed_servers = []

    headers = {"Authorization": API_KEY}

    for server in server_list:
        server_attr = server["attributes"]
        server_id = server_attr["identifier"]
        server_name = server_attr["name"]
        backup_limit = server["attributes"]["feature_limits"]["backups"]

        logger.info(f"processing server {server_id} '{server_name}'")

        try:
            if ROTATE.lower() == "true":
                remove_old_backup(server)

            if backup_limit == 0:
                logger.info("  skipping backup")
                continue

            url = f"{SERVERS_URL}{server_id}/backups"
            response = requests.post(url, data="", headers=headers)
            if response.status_code == 200:
                backup = response.json()
                backup_uuid = backup["attributes"]["uuid"]

                logger.info("  backup started")

                if POST_BACKUP_SCRIPT:
                    # we should only run this when the backup has been finished....
                    # this will prevent that the backups are made concurrently, thats OK, maybe it is
                    # even better as it reduces overall load
                    logger.info("  waiting for backup to finish...")
                    while True:
                        response = requests.get(
                            f"{url}/{backup_uuid}", data="", headers=headers
                        )

                        if response.status_code == 200:
                            if response.json()["attributes"]["completed_at"]:
                                logger.info("  running post-backup script")
                                run_script(server_id, backup_uuid)
                                break
                        else:
                            logger.error(
                                f"  failed to get backup info, giving up to run post-backup script. Error code: {response.status_code} {response.text}"
                            )
                            break

                        time.sleep(10)
                time.sleep(2)
            else:
                failed_servers.append(server_id)
                logger.error(
                    f"  backup failed. Error code: {response.status_code} {response.text}"
                )
                time.sleep(30)
        except requests.exceptions.RequestException as e:
            logger.error(
                f"  An error occurred while making the backup request: {str(e)}"
            )
            failed_servers.append(server_id)
            time.sleep(30)


def retry_failed_servers(failed_servers, headers):
    for server_id in failed_servers:
        try:
            url = f"{SERVERS_URL}{server_id}/backups"
            retry = requests.post(url, data="", headers=headers)

            if retry.status_code == 200:
                logger.info(
                    f"  Retry succeeded for server {server_id}. Status code: {retry.status_code}"
                )
                time.sleep(5)
            else:
                logger.error(
                    f"  Retry failed for server {server_id}. Error code: {retry.status_code}"
                )
                notify_error()
        except requests.exceptions.RequestException as e:
            logger.error(
                f"  An error occurred while retrying the backup request for server {server_id}: {str(e)}"
            )
            notify_error()


def run_script(server_id, backup_uuid):
    exit_status = os.system(f"sh {POST_BACKUP_SCRIPT} {server_id} {backup_uuid}")
    if exit_status > 0:
        logger.error(f"  post backup script: failed with exit status {exit_status}")


server_list = make_request()

backup_servers(server_list)
