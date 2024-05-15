import datetime
from pathlib import Path

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
