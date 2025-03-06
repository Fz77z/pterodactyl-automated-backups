from functools import lru_cache
from typing import Dict, Any, Optional
import time

from logprise import logger
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from config import API_KEY, MAX_RETRIES, RETRY_BACKOFF_FACTOR


__all__ = ["request"]


@lru_cache(1)
def _get_session() -> requests.Session:
    """Create and configure a requests Session with retry strategy."""
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_BACKOFF_FACTOR,
    )

    session = requests.Session()
    session.headers.update(
        {
            "Authorization": "Bearer " + API_KEY,
            # https://dashflo.net/docs/api/pterodactyl/v1/
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    session.mount("https://", adapter)
    session.mount("http://", adapter)

    logger.debug(f"Created requests session with {MAX_RETRIES} retries, backoff factor {RETRY_BACKOFF_FACTOR}")
    return session


def request(url: str, method: str = "GET", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Make an API request with retry capability.

    Returns JSON response or empty dict if no content.
    Exits on network or request errors after MAX_RETRIES.
    """
    method = method.upper()
    request_id = f"{method}:{url[-30:]}"

    logger.debug(f"[{request_id}] Making {method} request")
    start_time = time.time()

    for retry in range(MAX_RETRIES):
        try:
            if retry > 0:
                logger.info(f"[{request_id}] Retry attempt {retry}/{MAX_RETRIES}")

            response = _get_session().request(method=method, url=url, json=data)
            elapsed = time.time() - start_time

            if response.status_code >= 400:
                error_info = response.json().get("errors", [{"detail": "Unknown error"}])[0]["detail"]
                logger.error(f"[{request_id}] API returned error {response.status_code}: {error_info}")
                raise requests.exceptions.RequestException(error_info)

            if not response.ok:
                logger.error(f"[{request_id}] Failed with status {response.status_code}")
                raise requests.exceptions.RequestException(
                    f"Request failed with status {response.status_code}"
                )

            result = response.json() if response.content else {}
            logger.debug(f"[{request_id}] Success in {elapsed:.3f}s (size: {len(response.content)} bytes)")
            return result

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            logger.error(f"[{request_id}] Network Error: {e}")
            logger.error(f"[{request_id}] URL: {url}")
            logger.error(f"[{request_id}] Method: {method}")
            if data:
                logger.error(f"[{request_id}] Data: {data}")

            if retry == MAX_RETRIES - 1:
                logger.critical(f"[{request_id}] Max retries exceeded, exiting")
                exit(1)

        except requests.exceptions.RequestException as e:
            logger.error(f"[{request_id}] Request Exception: {e}")
            logger.error(f"[{request_id}] URL: {url}")
            logger.error(f"[{request_id}] Method: {method}")
            if data:
                logger.error(f"[{request_id}] Data: {data}")

            if retry == MAX_RETRIES - 1:
                logger.critical(f"[{request_id}] Max retries exceeded, exiting")
                exit(1)