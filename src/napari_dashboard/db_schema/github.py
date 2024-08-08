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


class GithubUser(Base):
    __tablename__ = "github_users"
    __table_args__ = (PrimaryKeyConstraint("username"),)

    username: Mapped[str] = Column(String)
    stars: Mapped[list["Stars"]] = relationship(back_populates="gh_user")


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

    user: Mapped[str] = Column(String, ForeignKey("github_users.username"))
    pull_request: Mapped[int] = Column(Integer, primary_key=True)
    open_time: Mapped[DateTime] = Column(DateTime, nullable=False)
    close_time: Mapped[DateTime] = Column(DateTime)
    merge_time: Mapped[DateTime] = Column(DateTime)
    last_modification_time: Mapped[DateTime] = Column(DateTime, nullable=False)
    title: Mapped[str] = Column(String)
    description: Mapped[str] = Column(String)
    labels: Mapped[list["Labels"]] = relationship(
        secondary=pr_to_labels_table, back_populates="pull_requests"
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


class PullRequestCommits(PullRequestRelated):
    __tablename__ = "github_pr_commits"

    @declared_attr
    def __table_args__(cls):
        return (
            PrimaryKeyConstraint("sha"),
            *PullRequestRelated.__table_args__,
            ForeignKeyConstraint(["user"], ["github_users.username"]),
        )

    sha: Mapped[str] = Column(String)
    user: Mapped[str] = Column(String)
    date: Mapped[DateTime] = Column(DateTime, nullable=False)


GithubUser.commits = relationship(
    PullRequests, secondary="github_pr_commits", back_populates="commits"
)
PullRequests.commits = relationship(
    GithubUser, secondary="github_pr_commits", back_populates="commits"
)


class PullRequestInteraction(PullRequestRelated):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (
            PrimaryKeyConstraint("id"),
            *PullRequestRelated.__table_args__,
            ForeignKeyConstraint(["user"], ["github_users.username"]),
        )

    id: Mapped[int] = Column(Integer, primary_key=True)
    user: Mapped[str] = Column(String)
    date: Mapped[DateTime] = Column(DateTime, nullable=False)


class PullRequestComments(PullRequestInteraction):
    __tablename__ = "github_pr_comments"


class PullRequestReviews(PullRequestInteraction):
    __tablename__ = "github_pr_reviews"
    state: Mapped[str] = Column(String)


GithubUser.pull_requests_reviews = relationship(
    PullRequests, secondary="github_pr_reviews", back_populates="reviewers"
)
PullRequests.reviewers = relationship(
    GithubUser,
    secondary="github_pr_reviews",
    back_populates="pull_requests_reviews",
)

GithubUser.pull_requests_comments = relationship(
    PullRequests, secondary="github_pr_comments", back_populates="pr_comments"
)
PullRequests.pr_comments = relationship(
    GithubUser,
    secondary="github_pr_comments",
    back_populates="pull_requests_comments",
)


class Issues(RepositoryRelated):
    __tablename__ = "github_issues"

    user: Mapped[str] = Column(String, ForeignKey("github_users.username"))
    issue: Mapped[int] = Column(Integer, primary_key=True)
    open_time: Mapped[DateTime] = Column(DateTime, nullable=False)
    close_time: Mapped[DateTime] = Column(DateTime)
    last_modification_time: Mapped[DateTime] = Column(DateTime, nullable=False)
    title: Mapped[str] = Column(String)
    description: Mapped[str] = Column(String)
    labels: Mapped[list["Labels"]] = relationship(
        secondary=issues_to_labels_table, back_populates="issues"
    )


class IssuesRelated(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (
            ForeignKeyConstraint(
                ["repository_name", "repository_user", "issue"],
                [
                    "github_issues.repository_name",
                    "github_issues.repository_user",
                    "github_issues.issue",
                ],
            ),
        )

    repository_name: Mapped[str] = Column(String)
    repository_user: Mapped[str] = Column(String)
    issue: Mapped[int] = Column(Integer)


class IssueComment(IssuesRelated):
    __tablename__ = "github_issue_comments"

    @declared_attr
    def __table_args__(cls):
        return (
            PrimaryKeyConstraint("id"),
            *IssuesRelated.__table_args__,
            ForeignKeyConstraint(["user"], ["github_users.username"]),
        )

    user: Mapped[str] = Column(String)
    date: Mapped[DateTime] = Column(DateTime, nullable=False)
    id: Mapped[int] = Column(Integer, primary_key=True)


GithubUser.issue_comments = relationship(
    Issues,
    secondary="github_issue_comments",
    back_populates="issue_commenters",
)
Issues.issue_commenters = relationship(
    GithubUser,
    secondary="github_issue_comments",
    back_populates="issue_comments",
)


class Release(RepositoryRelated):
    __tablename__ = "github_releases"
    # __table_args__ = (
    #     *RepositoryRelated.__table_args_repo__,
    # )

    release_tag: Mapped[str] = Column(String, primary_key=True)


class ArtifactDownloads(Base):
    __tablename__ = "github_artifact_downloads"
    __table_args__ = (
        PrimaryKeyConstraint(
            "repository_name",
            "repository_user",
            "release_tag",
            "artifact_name",
        ),
        ForeignKeyConstraint(
            ["repository_name", "repository_user", "release_tag"],
            [
                "github_releases.repository_name",
                "github_releases.repository_user",
                "github_releases.release_tag",
            ],
        ),
    )

    repository_name: Mapped[str] = Column(String)
    repository_user: Mapped[str] = Column(String)
    release_tag: Mapped[str] = Column(String)

    download_count: Mapped[int] = Column(Integer)
    artifact_name: Mapped[str] = Column(String)
    platform: Mapped[str] = Column(String)
