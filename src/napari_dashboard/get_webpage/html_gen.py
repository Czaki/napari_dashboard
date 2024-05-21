import datetime
import json
import os
from pathlib import Path

import pypistats
import requests
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

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

    with Session(engine) as session:
        stats = generate_basic_stats("napari", "napari", session, date, LABELS)
        stars = calc_stars_per_day_cumulative("napari", "napari", session)

    # Create an environment
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

    # Load the template
    index_template = env.get_template("index.html")
    dashboard_template = env.get_template("dashboard.js")
    dashboard_css_template = env.get_template("dashboard.css")
    color_mode_template = env.get_template("color-modes.js")
    download_stats_template = env.get_template("download_stats.js")

    download_info = {
        "Last day": {},
        "Last week": {},
        "Last month": {},
        "Total": {},
    }

    for package in ("napari", "npe2", "napari-plugin-manager"):
        pypi_stats = json.loads(pypistats.recent(package, format="json"))
        download_info["Last day"][package] = pypi_stats["data"]["last_day"]
        download_info["Last week"][package] = pypi_stats["data"]["last_week"]
        download_info["Last month"][package] = pypi_stats["data"]["last_month"]

        pepy = requests.get(
            f"https://pepy.tech/api/v2/projects/{package}",
            headers={"X-Api-Key": os.environ["PEPY_KEY"]},
        ).json()
        download_info["Total"][package] = pepy["total_downloads"]

    topics_count, users_count = get_topics_count()

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
        "today": datetime.datetime.now().strftime("%Y-%m-%d"),
        "base_day": date.strftime("%Y-%m-%d"),
        "download_stats": download_info,
        "bundle_download": {"Windows": 3668, "Linux": 419, "macOS": 1542},
        "topics_count": topics_count,
        "users_count": users_count,
    }

    # Render the template with data
    with open(target_path / "index.html", "w") as f:
        f.write(index_template.render(data))

    with open(target_path / "dashboard.js", "w") as f:
        f.write(dashboard_template.render(data))

    with open(target_path / "dashboard.css", "w") as f:
        f.write(dashboard_css_template.render(data))

    with open(target_path / "color-modes.js", "w") as f:
        f.write(color_mode_template.render(data))

    with open(target_path / "download_stats.js", "w") as f:
        f.write(download_stats_template.render(data))

    # Print the rendered HTML
