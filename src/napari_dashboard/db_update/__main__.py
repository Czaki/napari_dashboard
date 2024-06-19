import argparse
import logging
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from napari_dashboard.db_schema.base import Base
from napari_dashboard.db_update.conda import save_conda_download_information
from napari_dashboard.db_update.github import (
    save_issues,
    save_pull_requests,
    save_stars,
    update_artifact_download,
)
from napari_dashboard.db_update.imagesc import save_forum_info
from napari_dashboard.db_update.util import setup_cache


def update_github(session: Session):
    save_stars("napari", "napari", session)
    save_stars("napari", "docs", session)
    save_stars("napari", "npe2", session)

    save_pull_requests("napari", "napari", session)
    save_pull_requests("napari", "docs", session)
    save_pull_requests("napari", "npe2", session)

    save_issues("napari", "napari", session)
    save_issues("napari", "docs", session)
    save_issues("napari", "npe2", session)

    update_artifact_download("napari", "napari", session)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("db_path", help="Path to the database", type=Path)
    args = parser.parse_args()

    setup_cache()
    logging.basicConfig(level=logging.INFO)

    engine = create_engine(f"sqlite:///{args.db_path.absolute()}")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        update_github(session)
        save_forum_info(session)
        save_conda_download_information(session)


if __name__ == "__main__":
    main()
