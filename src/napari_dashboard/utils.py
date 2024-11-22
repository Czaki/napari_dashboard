import time

import requests


def requests_get(url: str, depth: int = 10):
    """this is util function to workaround a problem with status 500 in vercell"""
    for _ in range(depth):
        res = requests.get(url)
        if res.status_code != 500:
            return res
        time.sleep(1)  # wait
    raise RuntimeError(f"Failed to get data from the server for {url}")
