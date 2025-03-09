import os
import time
from typing import Dict, List, Any

from logprise import logger
import requests

from api_request import request
from config import GET_URL, POST_BACKUP_SCRIPT, ROTATE, SERVERS_URL


def remove_old_backup(server: Dict[str, Any]) -> None:
    """Remove older backups when limit is reached."""
    server_id = server["attributes"]["identifier"]
    backup_limit = server["attributes"]["feature_limits"]["backups"]
    server_name = server["attributes"]["name"]

    logger.info(
        f"[{server_id}] Checking backups for '{server_name}' (limit: {backup_limit})"
    )

    if server_id != "339ff417":
        return

    try:
        url = f"{SERVERS_URL}{server_id}/backups"
        response = request(url)
        backups = sorted(response["data"], key=lambda b: b["attributes"]["created_at"])
        backup_count = len(backups)

        if backup_count >= backup_limit:
            # Calculate how many backups to remove
            if backup_limit == 0:
                to_delete = backup_count
                logger.info(f"[{server_id}] Removing all {to_delete} backups")
            else:
                to_delete = backup_count - backup_limit + 1
                logger.info(
                    f"[{server_id}] Need to remove {to_delete} backup(s) to stay under limit"
                )

            i = 0
            deleted = 0

            while to_delete > 0 and i < backup_count:
                backup = backups[i]
                backup_name = backup["attributes"]["name"]
                backup_uuid = backup["attributes"]["uuid"]
                i += 1

                if backup["attributes"]["is_locked"]:
                    logger.warning(
                        f"[{server_id}] Backup '{backup_name}' is locked, skipping"
                    )
                    continue

                url = f"{SERVERS_URL}{server_id}/backups/{backup_uuid}"
                logger.info(
                    f"[{server_id}] Removing backup: '{backup_name}' (UUID: {backup_uuid})"
                )

                request(url, method="DELETE")
                deleted += 1
                to_delete -= 1
                time.sleep(2)

            if to_delete > 0:
                logger.error(
                    f"[{server_id}] Failed to delete enough backups: {to_delete} more needed, "
                    f"deleted {deleted}, {backup_count-deleted} remain"
                )
        else:
            logger.info(
                f"[{server_id}] No backups need removal ({backup_count}/{backup_limit})"
            )

    except requests.exceptions.RequestException as e:
        logger.error(f"[{server_id}] Error deleting backups: {e}")


def backup_servers(all_servers: Dict[str, Any]) -> List[str]:
    """Backup all servers and return list of failed server IDs."""
    failed_servers = []
    servers = all_servers["data"]
    server_count = len(servers)

    logger.info(f"Starting backup process for {server_count} servers")

    for i, server in enumerate(servers, 1):
        server_attr = server["attributes"]
        server_id = server_attr["identifier"]
        server_name = server_attr["name"]
        backup_limit = server_attr["feature_limits"]["backups"]

        logger.info(f"[{server_id}] ({i}/{server_count}) Processing '{server_name}'")

        try:
            if ROTATE:
                remove_old_backup(server)

            if backup_limit == 0:
                logger.info(f"[{server_id}] Backup limit is 0, skipping backup")
                continue

            url = f"{SERVERS_URL}{server_id}/backups"
            backup = request(url, method="POST")
            backup_uuid = backup["attributes"]["uuid"]

            logger.info(f"[{server_id}] Backup started (UUID: {backup_uuid})")

            if POST_BACKUP_SCRIPT:
                logger.info(f"[{server_id}] Waiting for backup completion...")
                wait_start = time.time()
                completion_checks = 0

                while True:
                    completion_checks += 1
                    response = request(f"{url}/{backup_uuid}")

                    if response["attributes"]["completed_at"]:
                        elapsed = time.time() - wait_start
                        logger.info(
                            f"[{server_id}] Backup completed after {elapsed:.1f}s, running post-backup script"
                        )
                        run_script(server_id, backup_uuid)
                        break

                    if completion_checks % 6 == 0:  # Log every minute
                        elapsed = time.time() - wait_start
                        logger.info(
                            f"[{server_id}] Still waiting for backup completion ({elapsed:.1f}s elapsed)"
                        )

                    time.sleep(10)

            logger.info(f"[{server_id}] Backup process complete")
            time.sleep(2)

        except requests.exceptions.RequestException as e:
            logger.error(f"[{server_id}] Error during backup: {e}")
            failed_servers.append(server_id)
            time.sleep(30)

    if failed_servers:
        logger.error(
            f"Backup process completed with {len(failed_servers)} failures: {', '.join(failed_servers)}"
        )
    else:
        logger.success(
            f"Backup process completed successfully for all {server_count} servers"
        )

    return failed_servers


def run_script(server_id: str, backup_uuid: str) -> None:
    """Run post-backup script and log result."""
    script_cmd = f"sh {POST_BACKUP_SCRIPT} {server_id} {backup_uuid}"
    logger.info(f"[{server_id}] Executing: {script_cmd}")

    exit_status = os.system(script_cmd)

    if exit_status > 0:
        logger.error(
            f"[{server_id}] Post-backup script failed with exit code {exit_status}"
        )
    else:
        logger.success(f"[{server_id}] Post-backup script completed successfully")


if __name__ == "__main__":
    logger.info(
        f"Backup script started, ROTATE={ROTATE}, POST_BACKUP_SCRIPT={POST_BACKUP_SCRIPT}"
    )
    try:
        server_list = request(GET_URL)
        server_count = len(server_list.get("data", []))
        logger.info(f"Retrieved {server_count} servers")

        failed = backup_servers(server_list)

        if failed:
            exit_code = 1
            logger.warning(f"Exiting with code {exit_code} due to failed backups")
            exit(exit_code)
    except Exception as e:
        logger.exception(f"Unhandled exception in backup script: {e}")
        exit(2)
