from __future__ import annotations

import json
import re
from functools import lru_cache
from urllib.request import Request, urlopen

from napari_dashboard.utils import requests_get


def normalized_name(name: str) -> str:
    """
    Normalize a plugin name by replacing underscores and dots by dashes and
    lower casing it.
    """
    return re.sub(r"[-_.]+", "-", name).lower()


@lru_cache(maxsize=1)
def plugins_list() -> list[dict]:
    """
    Contact the npe2api to get the list of plugins
    """
    url = "https://api.napari.org/api/extended_summary"
    data = requests_get(url)
    return json.load(data)


def plugin_name_list() -> list[str]:
    """
    Return a list of all known plugin names
    """
    return list({normalized_name(p["name"]) for p in plugins_list()})


def get_packages_to_fetch() -> list[str]:
    return ["napari", "napari-plugin-manager", "npe2"] + plugin_name_list()
