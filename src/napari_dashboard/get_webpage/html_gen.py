import contextlib
import datetime
import json
import os
from pathlib import Path

import pypistats
import requests
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from napari_dashboard.db_update.github import get_repo, setup_cache
from napari_dashboard.gen_stat.github import (
    calc_stars_per_day_cumulative,
    generate_basic_stats,
)

TEMPLATE_DIR = Path(__file__).parent / "webpage_tmpl"
LABELS = [
    "bugfix",
    "feature",
    "documentation",
    "performance",
    "enhancement",
    "maintenance",
]


def get_topics_count():
    index = 1
    count = 0
    user_set = set()
    while True:
        topics = requests.get(
            f"https://forum.image.sc/tag/napari/l/latest.json?page={index}",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0"
            },
        ).json()
        if not topics["topic_list"]["topics"]:
            break

        count += len(topics["topic_list"]["topics"])
        for user in topics["users"]:
            user_set.add(user["username"])
        index += 1
    return count, len(user_set)


def get_conda_downloads(name):
    if name is None:
        return 0, 0
    conda_info = requests.get(
        f"https://api.anaconda.org/package/{name}"
    ).json()
    total_downloads = sum(file["ndownloads"] for file in conda_info["files"])
    last_version = conda_info["files"][-1]["ndownloads"]
    return total_downloads, last_version


def get_plugin_count():
    return len(requests.get("https://api.napari.org/api/plugins").json())


def get_bundle_app_download():
    download_count = {"Windows": 0, "Linux": 0, "macOS": 0}
    repo = get_repo("napari", "napari")

    for release in repo.get_releases():
        if release.prerelease:
            continue
        for asset in release.get_assets():
            if asset.name.endswith(".sh"):
                download_count["Linux"] += asset.download_count
            if asset.name.endswith(".exe"):
                download_count["Windows"] += asset.download_count
            if asset.name.endswith(".pkg"):
                download_count["macOS"] += asset.download_count
    return download_count


def get_plugin_downloads():
    plugins = requests.get("https://api.napari.org/api/plugins").json()
    conda_translation = requests.get("https://api.napari.org/api/conda").json()
    res_dict = {}
    for plugin in plugins:
        with contextlib.suppress(KeyError):
            res_dict[plugin] = get_package_downloads(plugin, conda_translation)
    return res_dict


def get_package_downloads(package, conda_translation):
    pepy = requests.get(
        f"https://pepy.tech/api/v2/projects/{package}",
        headers={"X-Api-Key": os.environ["PEPY_KEY"]},
    ).json()
    pepy["downloads"] = {
        datetime.date.fromisoformat(k): v for k, v in pepy["downloads"].items()
    }
    yesterday = datetime.date.today() - datetime.timedelta(
        days=1
    )  # our data source has one day delay
    week_ago = yesterday - datetime.timedelta(days=7)
    month_ago = yesterday - datetime.timedelta(days=30)
    pepy["last_day"] = sum(pepy["downloads"].get(yesterday, {"": 0}).values())
    pepy["last_week"] = sum(
        sum(v.values())
        for k, v in pepy["downloads"].items()
        if week_ago <= k <= yesterday
    )
    pepy["last_month"] = sum(
        sum(v.values())
        for k, v in pepy["downloads"].items()
        if month_ago <= k <= yesterday
    )
    pepy["release_date"] = get_plugin_last_release_date(package)
    pepy["conda_download"] = (
        0
        if package not in conda_translation
        else get_conda_downloads(conda_translation[package])[0]
    )
    return pepy


def active_plugins(plugin_info: dict, last_mont_count: int = 1500) -> dict:
    """
    Get list of active plugins

    Parameters
    ----------
    plugin_info : dict
        Dictionary with plugin info
    last_mont_count : int
        Lower threshold for plugin activity based on downloads

    Returns
    -------
    dict
        Dictionary with active plugins
    """
    return {
        k: v
        for k, v in plugin_info.items()
        if v["last_month"] > last_mont_count
    }


def plugins_released_since(plugin_info: dict, since: datetime.date):
    """
    Get list of plugins released since given date

    Parameters
    ----------
    plugin_info : dict
        Dictionary with plugin info
    since : datetime.date
        Date to compare with

    Returns
    -------
    dict
        Dictionary with plugins released since given date
    """
    return {k: v for k, v in plugin_info.items() if v["release_date"] >= since}


def get_plugin_last_release_date(plugin_name: str) -> datetime.datetime:
    data = requests.get(f"https://pypi.org/pypi/{plugin_name}/json").json()
    last_release = data["info"]["version"]

    release_info = data["releases"][last_release]
    return min(
        datetime.datetime.fromisoformat(x["upload_time"]) for x in release_info
    )


def generate_webpage(
    target_path: Path, db_path: Path, date: datetime.datetime
) -> None:
    """
    Generate webpage from template

    Parameters
    ----------
    target_path: Path
        Path where to save the generated webpage
    """
    target_path.mkdir(parents=True, exist_ok=True)
    print(f"db path {db_path.absolute()}, sqlite://{db_path.absolute()}")
    engine = create_engine(f"sqlite:///{db_path.absolute()}")
    setup_cache()

    with Session(engine) as session:
        stats = generate_basic_stats("napari", "napari", session, date, LABELS)
        stars = calc_stars_per_day_cumulative("napari", "napari", session)
        stats["stars"] = stars[-1]["stars"]

    pypi_download_info = {
        "Last day": {},
        "Last week": {},
        "Last month": {},
        "Total": {},
    }
    conda_download_info = {"Total": {}, "Last version": {}}
    pepy_download = {}

    for package in ("napari", "npe2", "napari-plugin-manager"):
        pypi_stats = json.loads(pypistats.recent(package, format="json"))
        pypi_download_info["Last day"][package] = pypi_stats["data"][
            "last_day"
        ]
        pypi_download_info["Last week"][package] = pypi_stats["data"][
            "last_week"
        ]
        pypi_download_info["Last month"][package] = pypi_stats["data"][
            "last_month"
        ]

        pepy = requests.get(
            f"https://pepy.tech/api/v2/projects/{package}",
            headers={"X-Api-Key": os.environ["PEPY_KEY"]},
        ).json()
        pepy_download[package] = pepy
        pypi_download_info["Total"][package] = pepy["total_downloads"]
        total_downloads, last_version = get_conda_downloads(
            f"conda-forge/{package}"
        )
        conda_download_info["Total"][package] = total_downloads
        conda_download_info["Last version"][package] = last_version

    topics_count, users_count = get_topics_count()

    plugin_download = get_plugin_downloads()
    active_plugin_stats = active_plugins(plugin_download)
    all_plugin_downloads_from_pypi = sum(
        v["total_downloads"] for v in plugin_download.values()
    )
    all_plugin_downloads_from_conda = sum(
        v["conda_download"] for v in plugin_download.values()
    )
    under_active_development = plugins_released_since(plugin_download, date)
    napari_downloads_per_day = {
        k: sum(v.values())
        for k, v in pepy_download["napari"]["downloads"].items()
    }

    # Data to be rendered
    data = {
        "title": "Napari dashboard",
        "project": "Napari",
        "author": "Grzegorz Bokota",
        "stats": stats,
        "stars": [
            {"day": f"{x['day'].strftime('%Y-%m-%d')}", "stars": x["stars"]}
            for x in stars
        ],
        "napari_downloads_per_day_dates": list(
            napari_downloads_per_day.keys()
        ),
        "napari_downloads_per_day_values": list(
            napari_downloads_per_day.values()
        ),
        "today": datetime.datetime.now().strftime("%Y-%m-%d"),
        "base_day": date.strftime("%Y-%m-%d"),
        "pypi_downloads": pypi_download_info,
        "bundle_download": get_bundle_app_download(),
        "topics_count": topics_count,
        "users_count": users_count,
        "conda_downloads": conda_download_info,
        "plugins": {
            "count": get_plugin_count(),
            "all_plugin_downloads_from_pypi": all_plugin_downloads_from_pypi,
            "all_plugin_downloads_from_conda": all_plugin_downloads_from_conda,
            "active": len(active_plugin_stats),
            "under_active_development": len(under_active_development),
        },
    }

    # Create an environment
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

    # Load the template
    index_template = env.get_template("index.html")
    dashboard_template = env.get_template("dashboard.js")
    dashboard_css_template = env.get_template("dashboard.css")
    color_mode_template = env.get_template("color-modes.js")

    # Render the template with data
    with open(target_path / "index.html", "w") as f:
        f.write(index_template.render(data))

    with open(target_path / "dashboard.js", "w") as f:
        f.write(dashboard_template.render(data))

    with open(target_path / "dashboard.css", "w") as f:
        f.write(dashboard_css_template.render(data))

    with open(target_path / "color-modes.js", "w") as f:
        f.write(color_mode_template.render(data))

    # Print the rendered HTML


# conda download stats
# plugin download stats
# more plots
