from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
    Table,
)
from sqlalchemy.orm import Mapped, relationship

from napari_dashboard.db_schema.base import Base

tag_to_topic_table = Table(
    "forum_tag_to_topic",
    Base.metadata,
    Column("tag_name", ForeignKey("forum_tags.name"), primary_key=True),
    Column("topic_id", ForeignKey("forum_topics.id"), primary_key=True),
)

user_to_topic_table = Table(
    "forum_user_to_topic",
    Base.metadata,
    Column("user_id", ForeignKey("forum_users.id"), primary_key=True),
    Column("topic_id", ForeignKey("forum_topics.id"), primary_key=True),
)


class ForumTag(Base):
    __tablename__ = "forum_tags"

    name: Mapped[str] = Column(String, primary_key=True)
    tagged_topics: Mapped[list["ForumTopic"]] = relationship(
        secondary=tag_to_topic_table, back_populates="tags"
    )


class ForumUser(Base):
    __tablename__ = "forum_users"
    __table_args__ = (PrimaryKeyConstraint("id"),)

    id: Mapped[int] = Column(Integer)
    username: Mapped[str] = Column(String)
    name: Mapped[str] = Column(String)
    topics: Mapped[list["ForumTopic"]] = relationship(
        secondary=user_to_topic_table, back_populates="users"
    )


class ForumTopic(Base):
    __tablename__ = "forum_topics"
    __table_args__ = (PrimaryKeyConstraint("id"),)

    id: Mapped[int] = Column(Integer)
    title: Mapped[str] = Column(String)
    fancy_title: Mapped[str] = Column(String)
    slug: Mapped[str] = Column(String)
    created_at: Mapped[DateTime] = Column(DateTime)
    last_posted_at: Mapped[DateTime] = Column(DateTime)
    post_count: Mapped[int] = Column(Integer)

    tags: Mapped[list[ForumTag]] = relationship(
        secondary=tag_to_topic_table, back_populates="tagged_topics"
    )
    users: Mapped[list[ForumUser]] = relationship(
        secondary=user_to_topic_table, back_populates="topics"
    )
