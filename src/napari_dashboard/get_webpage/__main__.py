from __future__ import annotations

import argparse
import datetime
import typing
from pathlib import Path

from napari_dashboard.get_webpage import generate_webpage

if typing.TYPE_CHECKING:
    from collections.abc import Sequence


def main(args: Sequence[str] | None = None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "directory", help="Directory to save the webpage", type=Path
    )
    parser.add_argument("db_path", help="Path to the database", type=Path)
    args = parser.parse_args(args)

    generate_webpage(
        args.directory,
        args.db_path,
        datetime.datetime(year=2024, month=1, day=1),
    )


if __name__ == "__main__":
    main()
