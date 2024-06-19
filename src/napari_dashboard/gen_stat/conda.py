from typing import NamedTuple

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from napari_dashboard.db_schema.conda import CondaDownload


class CondaDownloadInfo(NamedTuple):
    pypi_name: str
    total_downloads: int
    last_version_downloads: int


def get_conda_download_info(
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
