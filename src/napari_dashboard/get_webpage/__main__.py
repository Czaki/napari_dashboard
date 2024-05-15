import argparse
import datetime
from pathlib import Path

from napari_dashboard.get_webpage import generate_webpage


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "directory", help="Directory to save the webpage", type=Path
    )
    parser.add_argument("db_path", help="Path to the database", type=Path)
    args = parser.parse_args()

    generate_webpage(
        args.directory,
        args.db_path,
        datetime.datetime(year=2024, month=1, day=1),
    )


if __name__ == "__main__":
    main()
