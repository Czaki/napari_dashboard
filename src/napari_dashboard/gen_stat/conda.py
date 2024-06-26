import datetime
from typing import NamedTuple

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from napari_dashboard.db_schema.conda import CondaDownload


class CondaDownloadInfo(NamedTuple):
    pypi_name: str
    total_downloads: int
    last_version_downloads: int


def _get_conda_download_info(
    session: Session, pypi_name: str
) -> CondaDownloadInfo:
    recent_date = (
        session.query(CondaDownload.date)
        .filter(CondaDownload.pypi_name == pypi_name)
        .order_by(desc(CondaDownload.date))
        .first()
    )
    if recent_date is None:
        return CondaDownloadInfo(
            pypi_name=pypi_name, total_downloads=0, last_version_downloads=0
        )

    total_downloads = (
        session.query(func.sum(CondaDownload.download_count))
        .filter(
            CondaDownload.pypi_name == pypi_name,
            CondaDownload.date == recent_date[0],
        )
        .first()[0]
    )
    last_version_downloads = (
        session.query(func.sum(CondaDownload.download_count))
        .filter(
            CondaDownload.pypi_name == pypi_name,
            CondaDownload.date == recent_date[0],
            CondaDownload.latest_version == True,  # noqa: E712
        )
        .first()[0]
    )

    return CondaDownloadInfo(
        pypi_name=pypi_name,
        total_downloads=total_downloads,
        last_version_downloads=last_version_downloads,
    )


def _last_date(session: Session, packages: set[str]) -> datetime.date:
    return (
        session.query(func.max(CondaDownload.date))
        .filter(CondaDownload.pypi_name.in_(packages))
        .scalar()
    )


def get_conda_total_download_info(
    session: Session, packages: set[str]
) -> dict[str, int]:
    last_date = _last_date(session, packages)
    return dict(
        session.query(
            CondaDownload.pypi_name, func.sum(CondaDownload.download_count)
        )
        .filter(CondaDownload.pypi_name.in_(packages))
        .filter(CondaDownload.date == last_date)
        .group_by(CondaDownload.pypi_name)
        .all()
    )


def get_conda_latest_download_info(
    session: Session, packages: set[str]
) -> dict[str, int]:
    last_date = _last_date(session, packages)
    return dict(
        session.query(
            CondaDownload.pypi_name, func.sum(CondaDownload.download_count)
        )
        .filter(CondaDownload.pypi_name.in_(packages))
        .filter(CondaDownload.date == last_date)
        .filter(CondaDownload.latest_version == True)  # noqa: E712
        .group_by(CondaDownload.pypi_name)
        .all()
    )


def get_total_conda_download(session: Session, packages: set[str]):
    last_date = _last_date(session, packages)
    return (
        session.query(func.sum(CondaDownload.download_count))
        .filter(CondaDownload.pypi_name.in_(packages))
        .filter(CondaDownload.date == last_date)
        .scalar()
    )
