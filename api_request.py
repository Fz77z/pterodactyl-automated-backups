from functools import lru_cache

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from common import API_KEY, MAX_RETRIES, RETRY_BACKOFF_FACTOR, logger


__all__ = ["request"]


@lru_cache(1)
def get_session():
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_BACKOFF_FACTOR,
    )

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + API_KEY,
        # https://dashflo.net/docs/api/pterodactyl/v1/
        "Content-Type": "application/json",
        "Accept": "application/json",
    })

    adapter = HTTPAdapter(max_retries=retry_strategy)

    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


def request(url, method: str = "GET", data=None) -> dict:
    for retry in range(MAX_RETRIES):
        try:
            response = get_session().request(method=method, url=url, data=data)
            response.raise_for_status()
            return response.json()
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            logger.error(f"Network Error: {str(e)}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Exception: {str(e)}")
