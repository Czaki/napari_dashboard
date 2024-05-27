from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, relationship

from napari_dashboard.db_schema.base import Base


class GithubUser(Base):
    __tablename__ = "github_users"
    __table_args__ = (PrimaryKeyConstraint("username"),)

    username: Mapped[str] = Column(String)
    stars: Mapped[list["Stars"]] = relationship(back_populates="gh_user")


class Repository(Base):
    __tablename__ = "github_repositories"
    __table_args__ = (UniqueConstraint("user", "name"),)

    id: Mapped[int] = Column(
        Integer, primary_key=True, autoincrement=True, nullable=False
    )
    user: Mapped[str] = Column(String, ForeignKey("github_users.username"))
    name: Mapped[str] = Column(String)
    stars: Mapped[list["Stars"]] = relationship(back_populates="gh_repository")


class Stars(Base):
    __tablename__ = "github_stars"
    __table_args__ = (PrimaryKeyConstraint("user", "repository"),)

    datetime: Mapped[DateTime] = Column(DateTime)
    date: Mapped[Date] = Column(Date)
    user: Mapped[str] = Column(String, ForeignKey("github_users.username"))
    repository: Mapped[int] = Column(
        Integer, ForeignKey("github_repositories.id")
    )
    gh_user: Mapped[GithubUser] = relationship(back_populates="stars")
    gh_repository: Mapped[Repository] = relationship(back_populates="stars")


pr_to_labels_table = Table(
    "github_pr_to_labels_table",
    Base.metadata,
    Column(
        "github_labels", ForeignKey("github_labels.label"), primary_key=True
    ),
    Column(
        "github_pull_requests",
        ForeignKey("github_pull_requests.id"),
        primary_key=True,
    ),
)

issues_to_labels_table = Table(
    "github_issues_to_labels_table",
    Base.metadata,
    Column(
        "github_labels", ForeignKey("github_labels.label"), primary_key=True
    ),
    Column("github_issues", ForeignKey("github_issues.id"), primary_key=True),
)


class Labels(Base):
    __tablename__ = "github_labels"

    label: Mapped[str] = Column(String, primary_key=True, unique=True)
    pull_requests: Mapped[list["PullRequests"]] = relationship(
        secondary=pr_to_labels_table, back_populates="labels"
    )
    issues: Mapped[list["Issues"]] = relationship(
        secondary=issues_to_labels_table, back_populates="labels"
    )


class PullRequests(Base):
    __tablename__ = "github_pull_requests"
    __table_args__ = (UniqueConstraint("user", "repository", "pull_request"),)

    id: Mapped[int] = Column(
        Integer, primary_key=True, autoincrement=True, nullable=False
    )
    user: Mapped[str] = Column(String, ForeignKey("github_users.username"))
    repository: Mapped[int] = Column(
        Integer, ForeignKey("github_repositories.id")
    )
    pull_request: Mapped[int] = Column(Integer)
    open_time: Mapped[DateTime] = Column(DateTime)
    close_time: Mapped[DateTime] = Column(DateTime)
    merge_time: Mapped[DateTime] = Column(DateTime)
    title: Mapped[str] = Column(String)
    description: Mapped[str] = Column(String)
    labels: Mapped[list["Labels"]] = relationship(
        secondary=pr_to_labels_table, back_populates="pull_requests"
    )


class Issues(Base):
    __tablename__ = "github_issues"
    __table_args__ = (UniqueConstraint("user", "repository", "issue"),)

    id: Mapped[int] = Column(
        Integer, primary_key=True, autoincrement=True, nullable=False
    )
    user: Mapped[str] = Column(String, ForeignKey("github_users.username"))
    repository: Mapped[int] = Column(
        Integer, ForeignKey("github_repositories.id")
    )
    issue: Mapped[int] = Column(Integer)
    open_time: Mapped[DateTime] = Column(DateTime)
    close_time: Mapped[DateTime] = Column(DateTime)
    title: Mapped[str] = Column(String)
    description: Mapped[str] = Column(String)
    labels: Mapped[list["Labels"]] = relationship(
        secondary=issues_to_labels_table, back_populates="issues"
    )


class Release(Base):
    __tablename__ = "github_releases"
    __table_args__ = (UniqueConstraint("repository", "release_tag"),)

    id: Mapped[int] = Column(
        Integer, primary_key=True, autoincrement=True, nullable=False
    )
    repository: Mapped[int] = Column(
        Integer, ForeignKey("github_repositories.id")
    )
    release_tag: Mapped[str] = Column(String)


class ArtifactDownloads(Base):
    __tablename__ = "github_artifact_downloads"
    __table_args__ = (UniqueConstraint("release", "artifact_name"),)

    id: Mapped[int] = Column(
        Integer, primary_key=True, autoincrement=True, nullable=False
    )
    release: Mapped[int] = Column(Integer, ForeignKey("github_releases.id"))
    download_count: Mapped[int] = Column(Integer)
    artifact_name: Mapped[str] = Column(String)
    platform: Mapped[str] = Column(String)
