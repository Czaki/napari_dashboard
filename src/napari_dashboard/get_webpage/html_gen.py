import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from napari_dashboard.db_update.util import setup_cache
from napari_dashboard.gen_stat.conda import (
    get_conda_latest_download_info,
    get_conda_total_download_info,
    get_total_conda_download,
)
from napari_dashboard.gen_stat.github import (
    calc_stars_per_day_cumulative,
    generate_basic_stats,
    generate_contributors_stats,
)
from napari_dashboard.gen_stat.imagesc import get_topics_count
from napari_dashboard.gen_stat.pypi import (
    get_active_packages,
    get_download_info,
    get_pepy_download_per_day,
    get_recent_releases_date,
    get_total_pypi_download,
    get_weekly_download_per_python_version,
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


def get_plugin_count():
    return len(requests.get("https://api.napari.org/api/plugins").json())


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
    setup_cache(timeout=60 * 60 * 4)

    skip_plugins = {"PartSeg", "skan"}
    plugins = requests.get("https://api.napari.org/api/plugins").json()
    valid_plugins = {x for x in plugins if x not in skip_plugins}

    with Session(engine) as session:
        stats = generate_basic_stats("napari", "napari", session, date, LABELS)
        stars = calc_stars_per_day_cumulative("napari", "napari", session)
        stats["stars"] = stars[-1]["stars"]
        stats["contributors"] = generate_contributors_stats(
            [("napari", "napari"), ("napari", "docs"), ("napari", "npe2")],
            session,
            date,
        )
        forums_stats = get_topics_count(date, session)
        pypi_download_info = get_download_info(
            session, ["napari", "npe2", "napari-plugin-manager"]
        )
        napari_downloads_per_day = get_pepy_download_per_day(session, "napari")
        active_plugin_stats = get_active_packages(
            session, packages=valid_plugins, threshold=1500
        )
        all_plugin_downloads_from_pypi = get_total_pypi_download(
            session, valid_plugins
        )
        all_plugin_downloads_from_conda = get_total_conda_download(
            session, valid_plugins
        )
        under_active_development = get_recent_releases_date(
            session, valid_plugins, date
        )
        conda_download_info = {
            "Total": get_conda_total_download_info(
                session, {"napari", "npe2", "napari-plugin-manager"}
            ),
            "Last version": get_conda_latest_download_info(
                session, {"napari", "npe2", "napari-plugin-manager"}
            ),
        }
        python_version_info = get_weekly_download_per_python_version(
            session, "napari", date
        )

    df = pd.DataFrame(python_version_info, columns=["version", "downloads"])
    py_version = px.pie(df, values="downloads", names="version").to_html(
        full_html=False, include_plotlyjs="cdn"
    )
    df_downloads = pd.DataFrame(
        napari_downloads_per_day.items(), columns=["date", "downloads"]
    )
    napari_downloads_per_day_plot = px.line(
        df_downloads, x="date", y="downloads"
    ).to_html(full_html=False, include_plotlyjs="cdn")

    napari_issue_activity = go.Figure()
    napari_issue_activity.add_trace(
        go.Scatter(
            x=stats["pr_issue_time_stats"]["days"],
            y=stats["pr_issue_time_stats"]["issues_open_cumulative"],
            mode="lines",
            name="Issues open",
        )
    )
    napari_issue_activity.add_trace(
        go.Scatter(
            x=stats["pr_issue_time_stats"]["days"],
            y=stats["pr_issue_time_stats"]["issues_closed_cumulative"],
            mode="lines",
            name="Issues close",
        )
    )
    napari_issue_activity_plot = napari_issue_activity.to_html(
        full_html=False, include_plotlyjs="cdn"
    )
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
        "napari_downloads_per_day_dates": [
            x.isoformat() for x in napari_downloads_per_day
        ],
        "napari_downloads_per_day_values": list(
            napari_downloads_per_day.values()
        ),
        "today": datetime.datetime.now().strftime("%Y-%m-%d"),
        "base_day": date.strftime("%Y-%m-%d"),
        "pypi_downloads": pypi_download_info,
        "forum": forums_stats,
        "conda_downloads": conda_download_info,
        "plugins": {
            "count": get_plugin_count(),
            "all_plugin_downloads_from_pypi": all_plugin_downloads_from_pypi,
            "all_plugin_downloads_from_conda": all_plugin_downloads_from_conda,
            "active": len(active_plugin_stats),
            "under_active_development": under_active_development,
            "skip": skip_plugins,
        },
        "py_version": py_version,
        "napari_downloads_per_day": napari_downloads_per_day_plot,
        "napari_issue_activity": napari_issue_activity_plot,
    }
    print("generating webpage")

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

    print("Save data to excel")

    # with Session(engine) as session:
    #     generate_excel_file(target_path / "napari_dashboard.xlsx", session)

    # Print the rendered HTML


# conda download stats
# plugin download stats
# more plots
