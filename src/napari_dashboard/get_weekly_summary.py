import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from napari_dashboard.gen_stat.github import (
    get_last_week,
    get_last_week_closed_pr,
    get_last_week_merged_pr,
    get_last_week_new_pr,
    get_updated_pr,
)
from napari_dashboard.get_webpage.gdrive import fetch_database


def main():
    logging.basicConfig(level=logging.INFO)
    fetch_database()
    engine = create_engine("sqlite:///dashboard.db")
    start, end = get_last_week()
    with Session(engine) as session:
        print(f"# Weekly Summary {start.date()}-{end.date()}\n")

        print("## New Pull Requests\n")
        for text in get_last_week_new_pr(session):
            print(f" - {text}")

        print("\n## Updated Pull Requests (state unchanged)\n")
        for text in get_updated_pr(session):
            print(f" - {text}")

        print("\n## Merged Pull Requests\n")
        for text in get_last_week_merged_pr(session):
            print(f" - {text}")

        print("\n## Closed Pull Requests (not merged)\n")
        for text in get_last_week_closed_pr(session):
            print(f" - {text}")


if __name__ == "__main__":
    main()
