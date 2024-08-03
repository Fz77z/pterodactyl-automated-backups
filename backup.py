import logging
import os
import time

import requests

from api_request import request
from config import GET_URL, POST_BACKUP_SCRIPT, ROTATE, SERVERS_URL

logger = logging.getLogger(__name__)


# remove backups when limits reached
def remove_old_backup(server):
    server_id = server["attributes"]["identifier"]
    backup_limit = server["attributes"]["feature_limits"]["backups"]
    logger.info(f"  backup limit is {backup_limit}")
    try:
        url = f"{SERVERS_URL}{server_id}/backups"
        response = request(url)

        backups = sorted(response["data"], key=lambda b: b["attributes"]["created_at"])

        if len(backups) >= backup_limit:
            # backup limit reached
            # remove oldest N backups
            if backup_limit == 0:
                n = len(backups)  # remove all backup
            else:
                n = (
                    len(backups) - backup_limit + 1
                )  # remove difference and leave space for one more

            to_delete = n
            i = 0

            while to_delete > 0 and i < len(backups):
                backup = backups[i]
                i += 1

                # delete oldest backup
                if backup["attributes"]["is_locked"]:
                    logger.warning(
                        f"  backup {backup['attributes']['name']} is locked, skipping"
                    )
                else:
                    url = f"{SERVERS_URL}{server_id}/backups/{backup['attributes']['uuid']}"
                    logger.info(
                        f"  removing backup: \"{backup['attributes']['name']}\""
                    )

                    request(url, method="DELETE")
                    time.sleep(2)

                    to_delete -= 1

            if to_delete > 0:
                logger.error(
                    "Failed to find enough backups to delete. I still need to delete %d...",
                    to_delete,
                )

        else:
            logger.info("  nothing to delete")

    except requests.exceptions.RequestException as e:
        logger.error(
            f"An error occurred while deleting backups from server {server_id}: {e}"
        )


def backup_servers(all_servers):
    failed_servers = []

    all_servers = all_servers["data"]

    for server in all_servers:
        server_attr = server["attributes"]
        server_id = server_attr["identifier"]
        server_name = server_attr["name"]
        backup_limit = server["attributes"]["feature_limits"]["backups"]

        logger.info(f"processing server {server_id} '{server_name}'")

        try:
            if ROTATE:
                remove_old_backup(server)

            if backup_limit == 0:
                logger.info("  skipping backup")
                continue

            url = f"{SERVERS_URL}{server_id}/backups"
            backup = request(url, method="POST")
            backup_uuid = backup["attributes"]["uuid"]

            logger.info("  backup started")

            if POST_BACKUP_SCRIPT:
                # we should only run this when the backup has been finished....
                # this will prevent that the backups are made concurrently, that's OK, maybe it is
                # even better as it reduces overall load
                logger.info("  waiting for backup to finish...")
                while True:
                    response = request(f"{url}/{backup_uuid}")

                    if response["attributes"]["completed_at"]:
                        logger.info("  running post-backup script")
                        run_script(server_id, backup_uuid)
                        break

                    time.sleep(10)
            time.sleep(2)
        except requests.exceptions.RequestException as e:
            logger.error(f"  An error occurred while making the backup request: {e}")
            failed_servers.append(server_id)
            time.sleep(30)


def run_script(server_id, backup_uuid):
    exit_status = os.system(f"sh {POST_BACKUP_SCRIPT} {server_id} {backup_uuid}")
    if exit_status > 0:
        logger.error(f"  post backup script: failed with exit status {exit_status}")


if __name__ == "__main__":
    server_list = request(GET_URL)
    backup_servers(server_list)
