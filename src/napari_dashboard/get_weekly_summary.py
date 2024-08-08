import argparse
import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from napari_dashboard.gen_stat.github import (
    get_last_week,
    get_last_week_closed_issues,
    get_last_week_closed_pr,
    get_last_week_merged_pr,
    get_last_week_new_issues,
    get_last_week_new_pr,
    get_updated_pr,
)
from napari_dashboard.get_webpage.gdrive import fetch_database


def generate_weekly_summary() -> list[str]:
    start, end = get_last_week()
    logging.basicConfig(level=logging.INFO)
    fetch_database()
    engine = create_engine("sqlite:///dashboard.db")
    res = [f"# Weekly Summary {start.date()}-{end.date()}\n"]
    with Session(engine) as session:
        res.append("## New Pull Requests\n")
        res.extend(f" - {text}" for text in get_last_week_new_pr(session))
        res.append("\n## Updated Pull Requests (state unchanged)\n")
        res.extend(f" - {text}" for text in get_updated_pr(session))
        res.append("\n## Merged Pull Requests\n")
        res.extend(f" - {text}" for text in get_last_week_merged_pr(session))
        res.append("\n## Closed Pull Requests (not merged)\n")
        res.extend(f" - {text}" for text in get_last_week_closed_pr(session))
        res.append("\n## New Issues\n")
        res.extend(f" - {text}" for text in get_last_week_new_issues(session))
        res.append("\n## Closed Issues\n")
        res.extend(
            f" - {text}" for text in get_last_week_closed_issues(session)
        )

    return res


def main():
    parse = argparse.ArgumentParser()
    parse.add_argument("--send_zulip", action="store_true")

    args = parse.parse_args()

    message = generate_weekly_summary()
    if args.send_zulip:
        import zulip

        client = zulip.Client(
            email="dashboard-bot@napari.zulipchat.com",
            api_key=os.environ.get("ZULIP_API_KEY"),
            site="https://napari.zulipchat.com",
        )
        result = client.register(event_types=["message", "realm"])
        max_length = result["max_message_length"]
        split_message = [[]]
        count = 0
        for line in message:
            line_length = len(line) + 1  # add 1 for newline
            if count + line_length > max_length:
                count = 0
                split_message.append([])
            split_message[-1].append(line)
            count += line_length
        for message_li in split_message:
            content = "\n".join(message_li)
            client.send_message(
                {
                    "type": "stream",
                    "to": "metrics and analytics",
                    "subject": "Weekly Summary",
                    "content": content,
                }
            )

    print("\n".join(message))


if __name__ == "__main__":
    main()
