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
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    logger.debug(
        f"Created requests session with {MAX_RETRIES} retries, backoff factor {RETRY_BACKOFF_FACTOR}"
    )
    return session


def _make_single_request(
    url: str, method: str, data: Optional[Dict[str, Any]], request_id: str
) -> Dict[str, Any]:
    """Execute a single API request with retry capability."""
    start_time = time.time()

    for retry in range(MAX_RETRIES):
        try:
            if retry > 0:
                logger.info(f"[{request_id}] Retry attempt {retry}/{MAX_RETRIES}")

            response = _get_session().request(method=method, url=url, json=data)
            elapsed = time.time() - start_time

            if response.status_code >= 400:
                error_info = response.json().get(
                    "errors", [{"detail": "Unknown error"}]
                )[0]["detail"]
                logger.error(
                    f"[{request_id}] API returned error {response.status_code}: {error_info}"
                )
                raise requests.exceptions.RequestException(error_info)

            if not response.ok:
                logger.error(
                    f"[{request_id}] Failed with status {response.status_code}"
                )
                raise requests.exceptions.RequestException(
                    f"Request failed with status {response.status_code}"
                )

            result = response.json() if response.content else {}
            logger.debug(
                f"[{request_id}] Success in {elapsed:.3f}s (size: {len(response.content)} bytes)"
            )
            return result

        except (
            requests.exceptions.RequestException,
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ) as e:
            logger.error(f"[{request_id}] Request Error: {e}")
            logger.error(f"[{request_id}] URL: {url}")
            logger.error(f"[{request_id}] Method: {method}")
            if data:
                logger.error(f"[{request_id}] Data: {data}")

            if retry == MAX_RETRIES - 1:
                logger.critical(f"[{request_id}] Max retries exceeded, exiting")
                exit(1)

    return {}  # Should never reach here due to exit(1) above


def _get_next_page_url(base_url: str, current_page: int) -> str:
    """Construct URL for the next page."""
    if "?" in base_url:
        url_part, params = base_url.split("?", 1)
        return f"{url_part}?page={current_page}&{params}"
    else:
        return f"{base_url}?page={current_page}"


def request(
    url: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
    fetch_all_pages: bool = True,
) -> Dict[str, Any]:
    """Make API request(s) with pagination support.

    Returns JSON response or empty dict if no content.
    When fetch_all_pages=True, automatically fetches all paginated data.
    """
    method = method.upper()
    request_id = f"{method}:{url[-30:]}"
    logger.debug(f"[{request_id}] Making {method} request")

    if method == "GET" and not data:
        data = {"per_page": 100}

    all_data = None
    current_url = url
    current_page = 1

    while current_url:
        result = _make_single_request(current_url, method, data, request_id)

        # Handle pagination
        if (
            fetch_all_pages
            and "data" in result
            and "meta" in result
            and "pagination" in result["meta"]
        ):
            pagination = result["meta"]["pagination"]

            # Initialize all_data on first page
            if all_data is None:
                all_data = result.copy()
            else:
                # Append data from subsequent pages
                all_data["data"].extend(result["data"])
                # Update pagination metadata
                all_data["meta"]["pagination"] = pagination

            # Check if there are more pages to fetch
            if current_page < pagination["total_pages"]:
                current_page += 1
                current_url = _get_next_page_url(url, current_page)
                logger.debug(
                    f"[{request_id}] Fetching page {current_page}/{pagination['total_pages']}"
                )
            else:
                return all_data
        else:
            # No pagination or fetch_all_pages=False
            return result

    return all_data or {}
