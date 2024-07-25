import os
import time

import requests

from api_request import request
from common import GET_URL, POST_BACKUP_SCRIPT, ROTATE, SERVERS_URL, logger


# remove backups when limits reached
def remove_old_backup(server):
    server_id = server["attributes"]["identifier"]
    backup_limit = server["attributes"]["feature_limits"]["backups"]
    logger.info(f"  backup limit is {backup_limit}")
    try:
        url = f"{SERVERS_URL}{server_id}/backups"
        response = request(url)

        backups = sorted(
            response["data"], key=lambda b: b["attributes"]["created_at"]
        )

        if len(backups) >= backup_limit:
            # backup limit reached
            # remove oldest N backups
            if backup_limit == 0:
                n = len(backups)  # remove all backup
            else:
                n = (
                    len(backups) - backup_limit + 1
                )  # remove difference and leave space for one more

            for i in range(n):
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

                    request(url, method='DELETE')

                time.sleep(2)
        else:
            logger.info("  nothing to delete")

    except requests.exceptions.RequestException as e:
        logger.error(
            f"An error occurred while deleting backups from server {server_id}: {str(e)}"
        )


def backup_servers(server_list):
    failed_servers = []

    for server in server_list:
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
            backup = request(url, method='POST')
            backup_uuid = backup["attributes"]["uuid"]

            logger.info("  backup started")

            if POST_BACKUP_SCRIPT:
                # we should only run this when the backup has been finished....
                # this will prevent that the backups are made concurrently, thats OK, maybe it is
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
            logger.error(
                f"  An error occurred while making the backup request: {str(e)}"
            )
            failed_servers.append(server_id)
            time.sleep(30)


def run_script(server_id, backup_uuid):
    exit_status = os.system(f"sh {POST_BACKUP_SCRIPT} {server_id} {backup_uuid}")
    if exit_status > 0:
        logger.error(f"  post backup script: failed with exit status {exit_status}")


if __name__ == '__main__':
    server_list = request(GET_URL)
    backup_servers(server_list)
