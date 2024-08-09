# noqa: INP001
from pathlib import Path

from napari_dashboard.db_schema.github import PullRequestCommits
from napari_dashboard.db_update.github import ensure_user, get_repo_with_model
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from tqdm import tqdm

db_path = Path(__file__).parent.parent / "dashboard.db"


def main():
    engine = create_engine(f"sqlite:///{db_path.absolute()}")

    with Session(engine) as session:
        session.query(PullRequestCommits).delete()
        session.commit()
        for user, repo in (
            ("napari", "napari"),
            ("napari", "docs"),
            ("napari", "npe2"),
        ):
            gh_repo, repo_model = get_repo_with_model(user, repo, session)
            pr_iter = gh_repo.get_pulls(state="all")
            for pr in tqdm(
                pr_iter,
                total=pr_iter.totalCount,
                desc=f"Pull Requests {user}/{repo}",
            ):
                commits = list(pr.get_commits())
                dates = {
                    x.raw_data["commit"]["author"]["date"] for x in commits
                }
                dates2 = {x.last_modified_datetime for x in commits}
                assert len(commits) == 1 or (
                    len(dates) > 1 and len(dates2) > 1
                )

                for commit in pr.get_commits():
                    # if session.query(PullRequestCommits).get(commit.sha):
                    #     continue
                    user_login = (
                        commit.author.login if commit.author else pr.user.login
                    )
                    ensure_user(user_login, session)
                    session.merge(
                        PullRequestCommits(
                            sha=commit.sha,
                            user=user_login,
                            date=commit.last_modified_datetime.replace(
                                tzinfo=None
                            ),
                            pr_num=pr.number,
                            repository_name=repo_model.name,
                            repository_user=repo_model.user,
                        )
                    )
            session.commit()


if __name__ == "__main__":
    main()
