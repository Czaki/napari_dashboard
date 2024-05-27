import logging
import os
import sys

from github import Auth, Github, Repository as GHRepository
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session
from tqdm import tqdm

from napari_dashboard.db_schema.github import (
    ArtifactDownloads,
    GithubUser,
    Issues,
    Labels,
    PullRequests,
    Release,
    Repository,
    Stars,
)
from napari_dashboard.gen_stat.github import get_repo_model

GH_TOKEN_ = os.environ.get("GH_TOKEN_")

_G = None


def get_github(token: str = GH_TOKEN_):
    global _G
    if _G is None:
        auth = Auth.Token(token)
        _G = Github(auth=auth)
    return _G


def get_repo(user: str, repo: str) -> GHRepository:
    g = get_github()
    return g.get_repo(f"{user}/{repo}")


def get_repo_with_model(
    user: str, repo: str, session: Session
) -> tuple[GHRepository, Repository]:
    if (
        session.query(Repository)
        .filter(Repository.user == user, Repository.name == repo)
        .count()
        == 0
    ):
        session.add(Repository(user=user, name=repo))
        session.commit()
    repo_ = get_repo(user, repo)
    return repo_, get_repo_model(user, repo, session)


def setup_cache(timeout=3600):
    """
    setup cache for speedup execution and reduce number of requests to GitHub API
    by default cache will expire after 1h (3600s)
    """
    try:
        import requests_cache
    except ImportError:
        print("requests_cache not installed", file=sys.stderr)
        return

    """setup cache for requests"""
    requests_cache.install_cache(
        "github_cache", backend="sqlite", expire_after=timeout
    )


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance

    instance = model(**kwargs)
    session.add(instance)
    session.commit()
    return instance


def stars_per_date(user: str, repo: str):
    repo = get_repo(user, repo)
    date_to_stars = {}

    for star in sorted(
        repo.get_stargazers_with_dates(), key=lambda x: x.starred_at
    ):
        date = star.starred_at.date()
        date_to_stars[date] = date_to_stars.get(date, 0) + 1
    return date_to_stars


def save_stars(user: str, repo: str, session: Session) -> None:
    """
    Save stars information for a repository to the database
    Parameters
    ----------
    user : str
        user or organization name on GitHub
    repo : str
        repository name on GitHub
    session : sqlalchemy.orm.Session
        database session
    """
    gh_repo, repo_model = get_repo_with_model(user, repo, session)

    count = (
        session.query(Stars).filter(Stars.repository == repo_model.id).count()
    )
    if count == gh_repo.stargazers_count:
        logging.info(
            "Already saved %s stars for %s",
            gh_repo.stargazers_count,
            gh_repo.full_name,
        )
        return

    stargazers = gh_repo.get_stargazers_with_dates()

    for star in tqdm(stargazers, total=gh_repo.stargazers_count):
        ensure_user(star.user.login, session)
        if (
            session.query(Stars)
            .filter(
                Stars.user == star.user.login,
                Stars.repository == repo_model.id,
            )
            .count()
            > 0
        ):
            continue
        session.add(
            Stars(
                user=star.user.login,
                date=star.starred_at,
                datetime=star.starred_at,
                repository=repo_model.id,
            )
        )
    session.commit()
    count_2 = (
        session.query(Stars).filter(Stars.repository == repo_model.id).count()
    )
    logging.info(
        "Saved %s stars for %s", count_2 - count, gh_repo.stargazers_count
    )


def ensure_user(user: str, session: Session) -> None:
    if (
        session.query(GithubUser).filter(GithubUser.username == user).count()
        == 0
    ):
        session.add(GithubUser(username=user))
        session.commit()


def save_pull_requests(user: str, repo: str, session: Session) -> None:
    """
    Save pull requests information for a repository to the database
    Parameters
    ----------
    user : str
        user or organization name on GitHub
    repo : str
        repository name on GitHub
    session : sqlalchemy.orm.Session
        database session
    """
    gh_repo, repo_model = get_repo_with_model(user, repo, session)

    count = (
        session.query(PullRequests)
        .filter(PullRequests.repository == repo_model.id)
        .count()
    )

    pr_iter = gh_repo.get_pulls(state="all")
    for pr in tqdm(pr_iter, total=pr_iter.totalCount):
        ensure_user(pr.user.login, session)
        # check if pull request is already saved and check if there is a need to update
        # merge status and labels
        pr_li = (
            session.query(PullRequests)
            .filter(
                PullRequests.user == pr.user.login,
                PullRequests.repository == repo_model.id,
                PullRequests.pull_request == pr.number,
            )
            .all()
        )
        if len(pr_li) > 0:
            if pr_li[0].close_time is not None:
                continue
            pr_li[0].merge_time = pr.merged_at
            pr_li[0].close_time = pr.closed_at
            pr_li[0].description = pr.body
            pr_li[0].title = pr.title
            pr_li[0].labels = [
                get_or_create(session, Labels, label=label.name)
                for label in pr.get_labels()
            ]
            continue
        labels = [
            get_or_create(session, Labels, label=label.name)
            for label in pr.get_labels()
        ]
        session.add(
            PullRequests(
                user=pr.user.login,
                merge_time=pr.merged_at,
                close_time=pr.closed_at,
                open_time=pr.created_at,
                repository=repo_model.id,
                pull_request=pr.number,
                labels=labels,
                title=pr.title,
                description=pr.body,
            )
        )
    session.commit()
    count_2 = (
        session.query(PullRequests)
        .filter(PullRequests.repository == repo_model.id)
        .count()
    )

    logging.info(
        "Saved %s pull requests for %s", count_2 - count, gh_repo.full_name
    )


def save_issues(user: str, repo: str, session: Session) -> None:
    """
    Save issues information for a repository to the database

    Parameters
    ----------
    user : str
        user or organization name on GitHub
    repo : str
        repository name on GitHub
    session : sqlalchemy.orm.Session
        database session
    """
    gh_repo, repo_model = get_repo_with_model(user, repo, session)

    count = (
        session.query(Issues)
        .filter(Issues.repository == repo_model.id)
        .count()
    )
    issue_iter = gh_repo.get_issues(state="all")
    for issue in tqdm(issue_iter, total=issue_iter.totalCount):
        ensure_user(issue.user.login, session)
        # check if issue is already saved
        issue_li = (
            session.query(Issues)
            .filter(
                Issues.user == issue.user.login,
                Issues.repository == repo_model.id,
                Issues.issue == issue.number,
            )
            .all()
        )
        if len(issue_li) > 0:
            if issue_li[0].close_time is not None:
                continue
            issue_li[0].close_time = issue.closed_at
            issue_li[0].description = issue.body
            issue_li[0].title = issue.title
            issue_li[0].labels = [
                get_or_create(session, Labels, label=label.name)
                for label in issue.get_labels()
            ]
            continue
        session.add(
            Issues(
                user=issue.user.login,
                repository=repo_model.id,
                issue=issue.number,
                title=issue.title,
                description=issue.body,
                labels=[
                    get_or_create(session, Labels, label=label.name)
                    for label in issue.get_labels()
                ],
                open_time=issue.created_at,
                close_time=issue.closed_at,
            )
        )
    session.commit()
    count_2 = (
        session.query(Issues)
        .filter(Issues.repository == repo_model.id)
        .count()
    )
    logging.info("Saved %s issues for %s", count_2 - count, gh_repo.full_name)


def update_artifact_download(user: str, repo: str, session: Session):
    gh_repo, repo_model = get_repo_with_model(user, repo, session)

    releases = gh_repo.get_releases()

    for release in tqdm(releases, total=releases.totalCount):
        if release.prerelease:
            continue
        release_model = get_or_create(
            session,
            Release,
            repository=repo_model.id,
            release_tag=release.tag_name,
        )
        for asset in release.get_assets():
            try:
                artifact = (
                    session.query(ArtifactDownloads)
                    .filter(
                        ArtifactDownloads.release == release_model.id,
                        ArtifactDownloads.artifact_name == asset.name,
                    )
                    .one()
                )
                artifact.download_count = asset.download_count
            except NoResultFound:
                if asset.name.endswith(".sh"):
                    platform = "Linux"
                elif asset.name.endswith(".exe"):
                    platform = "Windows"
                elif asset.name.endswith(".pkg"):
                    platform = "macOS"
                else:
                    continue
                session.add(
                    ArtifactDownloads(
                        release=release_model.id,
                        artifact_name=asset.name,
                        download_count=asset.download_count,
                        platform=platform,
                    )
                )
    session.commit()
