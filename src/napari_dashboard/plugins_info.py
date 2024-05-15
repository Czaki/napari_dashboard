import json
import re
from functools import lru_cache
from urllib.request import Request, urlopen


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
    url = "https://npe2api.vercel.app/api/extended_summary"
    with urlopen(Request(url)) as resp:
        return json.load(resp)


def plugin_name_list() -> list[str]:
    """
    Return a list of all known plugin names
    """
    return list({normalized_name(p["name"]) for p in plugins_list()})
