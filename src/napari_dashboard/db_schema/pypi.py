"""
Database schema for pypi_downloads table

Schema:
ibis.Schema {
  timestamp     !timestamp('UTC')
  country_code  string
  url           !string
  project       !string
  file          !struct<filename: string, project: string, version: string, type: string>
  details       struct<installer: struct<name: string, version: string>, python: string, implementation: struct<name: string, version: string>, distro: struct<name: string, version: string, id: string, libc: struct<lib: string, version: string>>, system: struct<name: string, release: string>, cpu: string, openssl_version: string, setuptools_version: string, rustc_version: string, ci: boolean>
  tls_protocol  string
  tls_cipher    string
}
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, DateTime, String

from napari_dashboard.db_schema.base import Base


class PyPi(Base):
    __tablename__ = "pypi_downloads"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    country_code: Mapped[Optional[str]] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)
    project: Mapped[str] = mapped_column(String)
    file: Mapped[dict] = mapped_column(JSON)
    details: Mapped[dict] = mapped_column(JSON)
    tls_protocol: Mapped[str] = mapped_column(String)
    tls_cipher: Mapped[str] = mapped_column(String)
