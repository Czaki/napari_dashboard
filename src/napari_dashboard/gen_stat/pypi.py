from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from napari_dashboard.db_schema.pypi import (
    PackageRelease,
    PePyDownloadStat,
    PePyTotalDownloads,
    PyPiDownloadPerOS,
    PyPiDownloadPerPythonVersion,
)


def get_active_packages(session: Session, packages: set[str], threshold: int):
    month_ago = date.today() - timedelta(days=30)
    subquery = (
        session.query(
            PePyDownloadStat.name,
            func.sum(PePyDownloadStat.downloads).label("total_download"),
        )
        .filter(PePyDownloadStat.date >= month_ago)
        .filter(PePyDownloadStat.name.in_(packages))
        .group_by(PePyDownloadStat.name)
        .subquery()
    )

    return dict(
        session.query(subquery)
        .filter(subquery.c.total_download > threshold)
        .all()
    )


def get_download_info(session: Session, packages: list[str]):
    day_ago = date.today() - timedelta(days=1)
    week_ago = date.today() - timedelta(days=7)
    month_ago = date.today() - timedelta(days=30)

    query_month = dict(
        session.query(
            PePyDownloadStat.name,
            func.sum(PePyDownloadStat.downloads).label("Last month"),
        )
        .filter(PePyDownloadStat.date >= month_ago)
        .filter(PePyDownloadStat.name.in_(packages))
        .group_by(PePyDownloadStat.name)
        .all()
    )
    query_week = dict(
        session.query(
            PePyDownloadStat.name,
            func.sum(PePyDownloadStat.downloads).label("Last week"),
        )
        .filter(PePyDownloadStat.date >= week_ago)
        .filter(PePyDownloadStat.name.in_(packages))
        .group_by(PePyDownloadStat.name)
        .all()
    )

    query_day = dict(
        session.query(
            PePyDownloadStat.name,
            func.sum(PePyDownloadStat.downloads).label("Last day"),
        )
        .filter(PePyDownloadStat.date >= day_ago)
        .filter(PePyDownloadStat.name.in_(packages))
        .group_by(PePyDownloadStat.name)
        .all()
    )

    total_query = dict(
        session.query(PePyTotalDownloads.name, PePyTotalDownloads.downloads)
        .filter(PePyTotalDownloads.name.in_(packages))
        .all()
    )

    return {
        "Last day": query_day,
        "Last week": query_week,
        "Last month": query_month,
        "Total": total_query,
    }


def get_pepy_download_per_day(session: Session, package: str):
    return dict(
        session.query(
            PePyDownloadStat.date, func.sum(PePyDownloadStat.downloads)
        )
        .filter(PePyDownloadStat.name == package)
        .group_by(PePyDownloadStat.date)
        .all()
    )


def get_total_pypi_download(session: Session, packages: set[str]):
    return (
        session.query(func.sum(PePyTotalDownloads.downloads))
        .filter(PePyTotalDownloads.name.in_(packages))
        .scalar()
    )


def get_recent_releases_date(
    session: Session, packages: set[str], after: date
):
    return (
        session.query(PackageRelease.name)
        .filter(PackageRelease.name.in_(packages))
        .filter(PackageRelease.release_date >= after)
        .group_by(PackageRelease.name)
        .count()
    )


def get_weekly_download_per_os(session: Session, package: str, since: date):
    return dict(
        session.query(
            PyPiDownloadPerOS.os, func.sum(PyPiDownloadPerOS.downloads)
        )
        .filter(PyPiDownloadPerOS.package_name == package)
        .filter(PyPiDownloadPerOS.date >= since)
        .group_by(PyPiDownloadPerOS.os)
        .all()
    )


def get_weekly_download_per_python_version(
    session: Session, package: str, since: date
):
    return (
        session.query(
            PyPiDownloadPerPythonVersion.python_version_name,
            func.sum(PyPiDownloadPerPythonVersion.downloads),
        )
        .filter(PyPiDownloadPerPythonVersion.package_name == package)
        .filter(PyPiDownloadPerPythonVersion.package_date >= since)
        .group_by(PyPiDownloadPerPythonVersion.python_version_name)
        .all()
    )
