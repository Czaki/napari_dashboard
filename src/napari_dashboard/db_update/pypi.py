from __future__ import annotations

import datetime
import typing

from sqlalchemy.orm import Session

from napari_dashboard.db_schema.pypi import PyPi
from napari_dashboard.plugins_info import plugin_name_list

if typing.TYPE_CHECKING:
    from sqlalchemy import Engine

START_DATE = "2018-01-01"


def indexed_projects(engine: Engine) -> list[str]:
    with Session(engine) as session:
        dist = session.query(PyPi.project).distinct()
    return [d[0] for d in dist]


def new_projects(engine: Engine) -> list[str]:
    all_projects = plugin_name_list()
    return sorted(set(all_projects) - set(indexed_projects(engine)))


def get_last_entry(engine: Engine) -> PyPi | None:
    with Session(engine) as session:
        return session.query(PyPi).order_by(PyPi.timestamp.desc()).first()


def get_last_entry_timestamp(engine: Engine) -> str:
    last_entry = get_last_entry(engine)
    if last_entry is None:
        return START_DATE
    return last_entry.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f UTC")


def get_now_timestamp() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f UTC")


QUERY = """
SELECT *
FROM `bigquery-public-data.pypi.file_downloads`
WHERE file.project in ({projects})
  AND timestamp > '{timestamp_lower}'
  AND timestamp < '{timestamp_upper}'
"""


def build_update_query(engine: Engine) -> str:
    projects = indexed_projects(engine)
    timstamp_lower = get_last_entry_timestamp(engine)
    timstamp_upper = get_now_timestamp()
    if not projects:
        projects = ["napari"]
    return QUERY.format(
        projects=", ".join(f"'{x}'" for x in projects),
        timestamp_lower=timstamp_lower,
        timestamp_upper=timstamp_upper,
    )


def build_new_projects_query(engine: Engine) -> str:
    projects = new_projects(engine)
    return QUERY.format(
        projects=", ".join(f"'{x}'" for x in projects),
        timestamp_lower=START_DATE,
        timestamp_upper=get_now_timestamp(),
    )
