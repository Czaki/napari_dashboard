from __future__ import annotations

import datetime
import itertools
from typing import TYPE_CHECKING, Callable

from sqlalchemy import desc, func, null

from napari_dashboard.db_schema.github import (
    BOT_SET,
    ArtifactDownloads,
    GithubUser,
    Issues,
    Labels,
    PullRequests,
    Release,
    Repository,
    Stars,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.orm import Session


CORE_DEVS = {
    "andy-sweet",
    "DragaDoncila",
    "GenevieveBuckley",
    "Czaki",
    "jni",
    "kevinyamauchi",
    "kne42",
    "kephale",
    "brisvag",
    "melissawm",
    "melonora",
    "psobolewskiPhD",
    "AhmetCanSolak",
    "alisterburt",
    "justinelarsen",
    "royerloic",
    "sofroniewn",
    "shanaxel42",
    "tlambert03",
    "potating-potato",
    "lucyleeow",
}


def get_repo_model(user: str, repo: str, session: Session) -> Repository:
    return (
        session.query(Repository)
        .filter(Repository.user == user, Repository.name == repo)
        .one()
    )


def calc_stars_per_day_cumulative(
    user: str, repo: str, session: Session
) -> dict:
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
    dict
        a list of dictionaries with keys 'day' and 'stars'

    """

    repo_model = get_repo_model(user, repo, session)

    count = 0
    res = {"day": [], "stars": []}
    for el in (
        session.query(Stars.date, func.count(Stars.date))
        .filter(Stars.repository == repo_model.id)
        .group_by(Stars.date)
        .order_by(Stars.date)
        .all()
    ):
        count += el[1]
        res["day"].append(el[0])
        res["stars"].append(count)
    return res


def get_pull_request_creators(
    user: str,
    repo: str,
    session: Session,
    since: datetime.datetime | None = None,
) -> list[tuple[str, int]]:
    # get all contributors with number of pull requests
    repo_model = get_repo_model(user, repo, session)
    basic_querry = session.query(
        PullRequests.user, func.count(PullRequests.pull_request).label("count")
    ).filter(PullRequests.repository == repo_model.id)

    if since is not None:
        basic_querry = basic_querry.filter(PullRequests.open_time > since)

    return [
        (x[0], x[1])
        for x in basic_querry.group_by(PullRequests.user)
        .order_by(desc("count"))
        .all()
        if x[0] not in BOT_SET
    ]


def get_pull_request_reviewers(
    user: str,
    repo: str,
    session: Session,
    since: datetime.datetime | None = None,
) -> list[tuple[str, int]]:
    # get all contributors with number of pull requests based on
    # PullRequests.coauthors
    repo_model = get_repo_model(user, repo, session)

    basic_query = (
        session.query(
            GithubUser.username,
            func.count(PullRequests.pull_request).label("count"),
        )
        .join(PullRequests, GithubUser.pull_requests_reviewer)
        .filter(PullRequests.repository == repo_model.id)
    )

    if since is not None:
        basic_query = basic_query.filter(PullRequests.open_time > since)

    return [
        (x[0], x[1])
        for x in basic_query.group_by(GithubUser.username)
        .order_by(desc("count"))
        .all()
        if x[0] not in BOT_SET
    ]


def get_pull_request_coauthors(
    user: str,
    repo: str,
    session: Session,
    since: datetime.datetime | None = None,
) -> list[tuple[str, int]]:
    # get all contributors with number of pull requests based on
    # PullRequests.coauthors
    repo_model = get_repo_model(user, repo, session)

    basic_query = (
        session.query(
            GithubUser.username,
            func.count(PullRequests.pull_request).label("count"),
        )
        .join(PullRequests, GithubUser.pull_requests_coauthor)
        .filter(PullRequests.repository == repo_model.id)
    )

    if since is not None:
        basic_query = basic_query.filter(PullRequests.open_time > since)

    return [
        (x[0], x[1])
        for x in basic_query.group_by(GithubUser.username)
        .order_by(desc("count"))
        .all()
        if x[0] not in BOT_SET
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
        if x[0] not in BOT_SET
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
            PullRequests.close_time.is_(null()),
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
    pr_closed_without_merge = (
        session.query(PullRequests)
        .filter(
            PullRequests.repository == repo_model.id,
            PullRequests.close_time.is_not(null()),
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
        "pr_closed_without_merge": pr_closed_without_merge,
        "average_pull_requests_per_day": round(
            new_opened_pull_requests / days, 2
        ),
    }


def bundle_downloads_count(user: str, repo: str, session: Session):
    repo_model = get_repo_model(user, repo, session)
    return dict(
        session.query(
            ArtifactDownloads.platform,
            func.sum(ArtifactDownloads.download_count),
        )
        .join(Release, Release.id == ArtifactDownloads.release)
        .filter(Release.repository == repo_model.id)
        .group_by(ArtifactDownloads.platform)
        .all()
    )


def _generate_contributors_stats(
    repo_li: list[tuple[str, str]],
    session: Session,
    since: datetime.datetime | None,
    fun: Callable[
        [str, str, Session, datetime.datetime | None], list[tuple[str, int]]
    ],
) -> dict[str, object]:
    per_repo_stats = {
        f"{user}/{repo}": dict(fun(user, repo, session, since))
        for user, repo in repo_li
    }
    all_persons = set()
    for persons in per_repo_stats.values():
        all_persons.update(persons.keys())
    res = {}
    for person in all_persons:
        res[person] = {}
        total = 0
        for repo, stats in per_repo_stats.items():
            res[person][repo] = stats.get(person, 0)
            total += res[person][repo]
        res[person]["total"] = total
    return sorted(res.items(), key=lambda x: x[1]["total"], reverse=True)


def generate_contributors_stats(
    repo_li: list[tuple[str, str]], session: Session, since: datetime.datetime
) -> dict[str, object]:
    pr_creators = _generate_contributors_stats(
        repo_li, session, None, get_pull_request_creators
    )
    pr_coauthors = _generate_contributors_stats(
        repo_li, session, None, get_pull_request_coauthors
    )
    pr_creators_since = _generate_contributors_stats(
        repo_li, session, since, get_pull_request_creators
    )
    pr_coauthors_since = _generate_contributors_stats(
        repo_li, session, since, get_pull_request_coauthors
    )
    pr_reviewers = _generate_contributors_stats(
        repo_li, session, None, get_pull_request_reviewers
    )
    pr_reviewers_since = _generate_contributors_stats(
        repo_li, session, since, get_pull_request_reviewers
    )
    return {
        "pr_creators": pr_creators[:10],
        "pr_coauthors": pr_coauthors[:10],
        "pr_creators_since": pr_creators_since[:10],
        "pr_coauthors_since": pr_coauthors_since[:10],
        "pr_creators_non_core": [
            x for x in pr_creators if x[0] not in CORE_DEVS
        ][:10],
        "pr_creators_non_core_since": [
            x for x in pr_creators_since if x[0] not in CORE_DEVS
        ][:10],
        "pr_reviewers": pr_reviewers[:10],
        "pr_reviewers_since": pr_reviewers_since[:10],
    }


def aggregate_weekly_stats(stat, weeks):
    return [
        sum(stat[j * 7 + i] for i in range(7) if j * 7 + i < len(stat))
        for j in range(len(weeks))
    ]


def generate_pr_and_issue_time_stats(user: str, repo: str, session: Session):
    repo_model = get_repo_model(user, repo, session)
    initial_date = min(
        session.query(Issues.open_time).order_by(Issues.open_time).first()[0],
        session.query(PullRequests.open_time)
        .order_by(PullRequests.open_time)
        .first()[0],
    ).date()
    # generate date array since initial_date
    days_array = [
        initial_date + datetime.timedelta(days=i)
        for i in range(
            (datetime.datetime.now().date() - initial_date).days + 1
        )
    ]
    index_dict = {day: i for i, day in enumerate(days_array)}
    issues_open = [0] * len(days_array)
    issues_closed = [0] * len(days_array)
    pr_open = [0] * len(days_array)
    pr_closed = [0] * len(days_array)
    pr_merged = [0] * len(days_array)
    pr_merged_feature = [0] * len(days_array)
    pr_merged_bugfix = [0] * len(days_array)
    pr_merged_maintenance = [0] * len(days_array)
    pr_merged_enhancement = [0] * len(days_array)
    feature_label = (
        session.query(Labels).filter(Labels.label == "feature").one()
    )
    bugfix_label = session.query(Labels).filter(Labels.label == "bugfix").one()
    maintenance_label = (
        session.query(Labels).filter(Labels.label == "maintenance").one()
    )
    enhancement_label = (
        session.query(Labels).filter(Labels.label == "enhancement").one()
    )

    for issue in (
        session.query(Issues).filter(Issues.repository == repo_model.id).all()
    ):
        issues_open[index_dict[issue.open_time.date()]] += 1
        if issue.close_time is not None:
            issues_closed[index_dict[issue.close_time.date()]] += 1

    for pull_request in (
        session.query(PullRequests)
        .filter(PullRequests.repository == repo_model.id)
        .all()
    ):
        pr_open[index_dict[pull_request.open_time.date()]] += 1
        if pull_request.close_time is not None:
            pr_closed[index_dict[pull_request.close_time.date()]] += 1
        if pull_request.merge_time is None:
            continue

        pr_merged[index_dict[pull_request.merge_time.date()]] += 1

        if feature_label in pull_request.labels:
            pr_merged_feature[index_dict[pull_request.merge_time.date()]] += 1
        if bugfix_label in pull_request.labels:
            pr_merged_bugfix[index_dict[pull_request.merge_time.date()]] += 1
        if maintenance_label in pull_request.labels:
            pr_merged_maintenance[
                index_dict[pull_request.merge_time.date()]
            ] += 1
        if enhancement_label in pull_request.labels:
            pr_merged_enhancement[
                index_dict[pull_request.merge_time.date()]
            ] += 1

    weeks = days_array[::7]
    issues_open_weekly = aggregate_weekly_stats(issues_open, weeks)
    issues_closed_weekly = aggregate_weekly_stats(issues_closed, weeks)
    pr_open_weekly = aggregate_weekly_stats(pr_open, weeks)
    pr_closed_weekly = aggregate_weekly_stats(pr_closed, weeks)
    pr_merged_weekly = aggregate_weekly_stats(pr_merged, weeks)
    pr_merged_feature_weekly = aggregate_weekly_stats(pr_merged_feature, weeks)
    pr_merged_bugfix_weekly = aggregate_weekly_stats(pr_merged_bugfix, weeks)
    pr_merged_maintenance_weekly = aggregate_weekly_stats(
        pr_merged_maintenance, weeks
    )
    pr_merged_enhancement_weekly = aggregate_weekly_stats(
        pr_merged_enhancement, weeks
    )

    return {
        "days": [x.strftime("%Y-%m-%d") for x in days_array],
        "issues_open": issues_open,
        "issues_open_cumulative": list(itertools.accumulate(issues_open)),
        "issues_closed": issues_closed,
        "issues_closed_cumulative": list(itertools.accumulate(issues_closed)),
        "pr_open": pr_open,
        "pr_open_cumulative": list(itertools.accumulate(pr_open)),
        "pr_closed": pr_closed,
        "pr_closed_cumulative": list(itertools.accumulate(pr_closed)),
        "pr_merged": pr_merged,
        "pr_merged_cumulative": list(itertools.accumulate(pr_merged)),
        "weeks": [x.strftime("%Y-%m-%d") for x in weeks],
        "issues_open_weekly": issues_open_weekly,
        "issues_closed_weekly": issues_closed_weekly,
        "pr_open_weekly": pr_open_weekly,
        "pr_closed_weekly": pr_closed_weekly,
        "pr_merged_weekly": pr_merged_weekly,
        "pr_merged_feature_weekly": pr_merged_feature_weekly,
        "pr_merged_bugfix_weekly": pr_merged_bugfix_weekly,
        "pr_merged_maintenance_weekly": pr_merged_maintenance_weekly,
        "pr_merged_enhancement_weekly": pr_merged_enhancement_weekly,
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
        "bundle_download": bundle_downloads_count(user, repo, session),
        "pr_issue_time_stats": generate_pr_and_issue_time_stats(
            user, repo, session
        ),
    }
