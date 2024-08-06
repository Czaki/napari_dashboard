from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    PrimaryKeyConstraint,
    String,
    Table,
)
from sqlalchemy.orm import Mapped, declared_attr, relationship

from napari_dashboard.db_schema.base import Base

BOT_SET = {
    "dependabot[bot]",
    "pre-commit-ci[bot]",
    "napari-bot",
    "github-actions[bot]",
}


def pull_request_relation():
    return (
        Column("pull_request_num", primary_key=True),
        Column("repository_name", primary_key=True),
        Column("repository_user", primary_key=True),
        ForeignKeyConstraint(
            ["pull_request_num", "repository_name", "repository_user"],
            [
                "github_pull_requests.pull_request",
                "github_pull_requests.repository_name",
                "github_pull_requests.repository_user",
            ],
        ),
    )


pr_to_coauthors_table = Table(
    "github_pr_to_coauthors_table",
    Base.metadata,
    Column(
        "github_users", ForeignKey("github_users.username"), primary_key=True
    ),
    *pull_request_relation(),
)


class GithubUser(Base):
    __tablename__ = "github_users"
    __table_args__ = (PrimaryKeyConstraint("username"),)

    username: Mapped[str] = Column(String)
    stars: Mapped[list["Stars"]] = relationship(back_populates="gh_user")
    pull_requests_coauthor: Mapped[list["PullRequests"]] = relationship(
        secondary=pr_to_coauthors_table, back_populates="coauthors"
    )


class Repository(Base):
    __tablename__ = "github_repositories"
    __table_args__ = (PrimaryKeyConstraint("user", "name"),)

    user: Mapped[str] = Column(String, ForeignKey("github_users.username"))
    name: Mapped[str] = Column(String)
    stars: Mapped[list["Stars"]] = relationship(back_populates="gh_repository")


class RepositoryRelated(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                ["repository_name", "repository_user"],
                ["github_repositories.name", "github_repositories.user"],
            ),
        )

    __repo_primary_key__ = ("repository_name", "repository_user")

    repository_name: Mapped[str] = Column(String, primary_key=True)
    repository_user: Mapped[str] = Column(String, primary_key=True)
    # repository_name: Mapped[str] = Column(String, ForeignKey("github_repositories.name"), primary_key=True)
    # repository_user: Mapped[str] = Column(String, ForeignKey("github_repositories.user"), primary_key=True)


class Stars(RepositoryRelated):
    __tablename__ = "github_stars"

    datetime: Mapped[DateTime] = Column(DateTime)
    date: Mapped[Date] = Column(Date)
    user: Mapped[str] = Column(
        String, ForeignKey("github_users.username"), primary_key=True
    )
    gh_user: Mapped[GithubUser] = relationship(back_populates="stars")
    gh_repository: Mapped[Repository] = relationship(back_populates="stars")


pr_to_labels_table = Table(
    "github_pr_to_labels_table",
    Base.metadata,
    Column(
        "github_labels", ForeignKey("github_labels.label"), primary_key=True
    ),
    *pull_request_relation(),
)

issues_to_labels_table = Table(
    "github_issues_to_labels_table",
    Base.metadata,
    Column("label", ForeignKey("github_labels.label"), primary_key=True),
    Column("issue_num", primary_key=True),
    Column("repository_name", primary_key=True),
    Column("repository_user", primary_key=True),
    ForeignKeyConstraint(
        ["issue_num", "repository_name", "repository_user"],
        [
            "github_issues.issue",
            "github_issues.repository_name",
            "github_issues.repository_user",
        ],
    ),
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


class PullRequests(RepositoryRelated):
    __tablename__ = "github_pull_requests"
    # __table_args__ = (
    #     *RepositoryRelated.__table_args_repo__,
    # )

    user: Mapped[str] = Column(String, ForeignKey("github_users.username"))
    pull_request: Mapped[int] = Column(Integer, primary_key=True)
    open_time: Mapped[DateTime] = Column(DateTime)
    close_time: Mapped[DateTime] = Column(DateTime)
    merge_time: Mapped[DateTime] = Column(DateTime)
    last_modification_time: Mapped[DateTime] = Column(DateTime)
    title: Mapped[str] = Column(String)
    description: Mapped[str] = Column(String)
    labels: Mapped[list["Labels"]] = relationship(
        secondary=pr_to_labels_table, back_populates="pull_requests"
    )
    coauthors: Mapped[list["GithubUser"]] = relationship(
        secondary=pr_to_coauthors_table,
        back_populates="pull_requests_coauthor",
    )


class PullRequestRelated(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                ["repository_name", "repository_user", "pr_num"],
                [
                    "github_pull_requests.repository_name",
                    "github_pull_requests.repository_user",
                    "github_pull_requests.pull_request",
                ],
            ),
        )

    repository_name: Mapped[str] = Column(String)
    repository_user: Mapped[str] = Column(String)
    pr_num: Mapped[int] = Column(Integer)


class PullRequestInteraction(PullRequestRelated):
    __abstract__ = True

    id: Mapped[int] = Column(Integer, primary_key=True)
    user: Mapped[str] = Column(String, ForeignKey("github_users.username"))
    date: Mapped[DateTime] = Column(DateTime)


class PullRequestComments(PullRequestInteraction):
    __tablename__ = "github_pr_comments"


class PullRequestReviews(PullRequestInteraction):
    __tablename__ = "github_pr_reviews"
    state: Mapped[str] = Column(String)


GithubUser.pull_requests_reviewer = relationship(
    PullRequests, secondary="github_pr_reviews", back_populates="reviewers"
)
PullRequests.reviewers = relationship(
    GithubUser,
    secondary="github_pr_reviews",
    back_populates="pull_requests_reviewer",
)


class Issues(RepositoryRelated):
    __tablename__ = "github_issues"
    # __table_args__ = (
    #     *RepositoryRelated.__table_args_repo__,
    # )

    user: Mapped[str] = Column(String, ForeignKey("github_users.username"))
    issue: Mapped[int] = Column(Integer, primary_key=True)
    open_time: Mapped[DateTime] = Column(DateTime)
    close_time: Mapped[DateTime] = Column(DateTime)
    last_modification_time: Mapped[DateTime] = Column(DateTime)
    title: Mapped[str] = Column(String)
    description: Mapped[str] = Column(String)
    labels: Mapped[list["Labels"]] = relationship(
        secondary=issues_to_labels_table, back_populates="issues"
    )


class Release(RepositoryRelated):
    __tablename__ = "github_releases"
    # __table_args__ = (
    #     *RepositoryRelated.__table_args_repo__,
    # )

    release_tag: Mapped[str] = Column(String, primary_key=True)


class ArtifactDownloads(Base):
    __tablename__ = "github_artifact_downloads"
    # __table_args__ = (
    #     PrimaryKeyConstraint("release_repository_name", "release_repository_user", "release_tag", "artifact_name"),
    #     ForeignKeyConstraint(
    #         ["release_repository_name", "release_repository_user", "release_tag"],
    #         ["github_releases.repository_name", "github_releases.repository_user", "github_releases.release_tag"],
    #     )
    # )

    repository_name: Mapped[str] = Column(
        String, ForeignKey("github_releases.repository_name"), primary_key=True
    )
    repository_user: Mapped[str] = Column(
        String, ForeignKey("github_releases.repository_user"), primary_key=True
    )
    release_tag: Mapped[str] = Column(
        String, ForeignKey("github_releases.release_tag"), primary_key=True
    )

    download_count: Mapped[int] = Column(Integer)
    artifact_name: Mapped[str] = Column(String)
    platform: Mapped[str] = Column(String)
