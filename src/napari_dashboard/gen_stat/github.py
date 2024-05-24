import datetime
from collections.abc import Sequence

from sqlalchemy import func, null
from sqlalchemy.orm import Session

from napari_dashboard.db_schema.github import (
    Issues,
    Labels,
    PullRequests,
    Repository,
    Stars,
)


def get_repo_model(user: str, repo: str, session: Session) -> Repository:
    return (
        session.query(Repository)
        .filter(Repository.user == user, Repository.name == repo)
        .one()
    )


def calc_stars_per_day_cumulative(
    user: str, repo: str, session: Session
) -> list[dict[datetime.date, int]]:
    """
    Based on the data in the database, calculate the cumulative number of stars per day

    Parameters
    ----------
    user : str
        name of user or organization on GitHub
    repo : str
        name of repository on GitHub
    session : sqlalchemy.orm.Session
        database session

    Returns
    -------
    list[dict]
        a list of dictionaries with keys 'day' and 'stars'

    """

    repo_model = get_repo_model(user, repo, session)

    count = 0
    res = []
    for el in (
        session.query(Stars.date, func.count(Stars.date))
        .filter(Stars.repository == repo_model.id)
        .group_by(Stars.date)
        .order_by(Stars.date)
        .all()
    ):
        count += el[1]
        res.append({"day": el[0], "stars": count})
    return res


def get_contributors(
    user: str, repo: str, session: Session
) -> list[tuple[str, int]]:
    # get all contributors with number of pull requests
    repo_model = get_repo_model(user, repo, session)
    return [
        (x[0], x[1])
        for x in session.query(
            PullRequests.user, func.count(PullRequests.pull_request)
        )
        .filter(PullRequests.repository == repo_model.id)
        .group_by(PullRequests.user)
        .all()
    ]


def get_recent_contributors(
    user: str, repo: str, session: Session, since: datetime.datetime
) -> list[str]:
    # get all contributors with number of pull requests
    repo_model = get_repo_model(user, repo, session)
    return [
        x[0]
        for x in session.query(PullRequests.user)
        .filter(
            PullRequests.repository == repo_model.id,
            PullRequests.merge_time > since,
        )
        .group_by(PullRequests.user)
        .all()
        if x[0] not in {"dependabot[bot]", "pre-commit-ci[bot]", "napari-bot"}
    ]


def count_recent_pull_requests(
    user: str, repo: str, session: Session, since: datetime.datetime
) -> int:
    # get all contributors with number of pull requests
    repo_model = get_repo_model(user, repo, session)
    return (
        session.query(PullRequests)
        .filter(
            PullRequests.repository == repo_model.id,
            PullRequests.merge_time > since,
        )
        .count()
    )


def count_recent_closed_issues(
    user: str, repo: str, session: Session, since: datetime.datetime
) -> int:
    # get all contributors with number of pull requests
    repo_model = get_repo_model(user, repo, session)
    return (
        session.query(Issues)
        .filter(Issues.repository == repo_model.id, Issues.close_time > since)
        .count()
    )


def count_recent_opened_issues(
    user: str, repo: str, session: Session, since: datetime.datetime
) -> int:
    # get all contributors with number of pull requests
    repo_model = get_repo_model(user, repo, session)
    return (
        session.query(Issues)
        .filter(Issues.repository == repo_model.id, Issues.open_time > since)
        .count()
    )


def count_recent_pull_requests_by_label(
    user: str,
    repo: str,
    session: Session,
    since: datetime.datetime,
    labels: Sequence[str],
) -> dict[str, int]:
    # get information how many pull requests have a specific label
    repo_model = get_repo_model(user, repo, session)
    resp = dict(
        session.query(Labels.label, func.count(PullRequests.id))
        .filter(
            PullRequests.repository == repo_model.id,
            PullRequests.merge_time > since,
        )
        .join(PullRequests.labels)
        .group_by(Labels.label)
        .all()
    )
    return {k: resp.get(k, 0) for k in labels}


def generate_pr_stats(
    user: str, repo: str, session: Session, since: datetime.datetime
) -> dict[str, int]:
    days = (datetime.datetime.now() - since).days
    repo_model = get_repo_model(user, repo, session)
    total_pull_requests = (
        session.query(PullRequests)
        .filter(PullRequests.repository == repo_model.id)
        .count()
    )
    merged_pull_requests = (
        session.query(PullRequests)
        .filter(
            PullRequests.repository == repo_model.id,
            PullRequests.merge_time.isnot(null()),
        )
        .count()
    )
    open_pull_requests = (
        session.query(PullRequests)
        .filter(
            PullRequests.repository == repo_model.id,
            PullRequests.merge_time.is_(null()),
        )
        .count()
    )
    new_merged_pull_requests = (
        session.query(PullRequests)
        .filter(
            PullRequests.repository == repo_model.id,
            PullRequests.merge_time > since,
            PullRequests.merge_time.isnot(null()),
        )
        .count()
    )
    new_opened_pull_requests = (
        session.query(PullRequests)
        .filter(
            PullRequests.repository == repo_model.id,
            PullRequests.open_time > since,
            PullRequests.merge_time.is_(null()),
        )
        .count()
    )
    return {
        "total_pull_requests": total_pull_requests,
        "merged_pull_requests": merged_pull_requests,
        "open_pull_requests": open_pull_requests,
        "new_merged_pull_requests": new_merged_pull_requests,
        "new_open_pull_requests": new_opened_pull_requests,
        "average_pull_requests_per_day": round(
            new_opened_pull_requests / days, 2
        ),
    }


def generate_basic_stats(
    user: str,
    repo: str,
    session: Session,
    since: datetime.datetime,
    labels: Sequence[str],
) -> dict[str, object]:
    pr_stats = generate_pr_stats(user, repo, session, since)
    label_stat = count_recent_pull_requests_by_label(
        user, repo, session, since, labels
    )
    active_contributors = get_recent_contributors(user, repo, session, since)

    return pr_stats | {
        "labels": label_stat,
        "active_contributors": len(active_contributors),
        "closed_issues": count_recent_closed_issues(
            user, repo, session, since
        ),
        "opened_issues": count_recent_opened_issues(
            user, repo, session, since
        ),
    }
