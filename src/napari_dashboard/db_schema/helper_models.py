from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.orm import Mapped

from napari_dashboard.db_schema.base import Base


class UpdateDBInfo(Base):
    __tablename__ = "update_db_info"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    datetime: Mapped[DateTime] = Column(DateTime)
