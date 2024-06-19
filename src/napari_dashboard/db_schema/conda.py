from sqlalchemy import Boolean, Column, Date, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped

from napari_dashboard.db_schema.base import Base


class CondaDownload(Base):
    __tablename__ = "conda_downloads"
    __table_args__ = (UniqueConstraint("name", "full_binary_name", "date"),)

    id: Mapped[int] = Column(Integer, primary_key=True)
    pypi_name: Mapped[str] = Column(String)
    name: Mapped[str] = Column(String)
    version: Mapped[str] = Column(String)
    download_count: Mapped[int] = Column(Integer)
    date: Mapped[Date] = Column(Date)
    full_binary_name: Mapped[str] = Column(String)
    latest_version: Mapped[bool] = Column(Boolean)
