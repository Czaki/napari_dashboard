"""
Implement helper functions to dump content of database to an Excel file.
"""

import logging
from pathlib import Path
from typing import Union

import pandas as pd
from sqlalchemy.orm import Session

from napari_dashboard.db_schema import base


def generate_excel_file(file_path: Union[str, Path], session: Session):
    with pd.ExcelWriter(file_path) as writer:
        for name, table in base.Base.metadata.tables.items():
            if name in ("sqlite_sequence", "alembic_version"):
                continue
            try:
                df = pd.read_sql_table(table.name, session.bind)
                df.to_excel(writer, sheet_name=table.name, index=False)
            except ValueError:
                logging.exception("Error while reading table %s", table.name)
