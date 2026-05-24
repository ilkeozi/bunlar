from __future__ import annotations

import json
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import RawWebRobotsPolicy


def evaluate_robots_allow(robots_txt: str, target_url: str, *, user_agent: str = "*") -> bool:
    parser = RobotFileParser()
    parser.parse((robots_txt or "").splitlines())
    return parser.can_fetch(user_agent, target_url)


def persist_robots_policy(
    *,
    host_id: int,
    robots_txt: str,
    fetch_status: str,
    evaluation_summary: dict[str, object],
) -> int:
    session_factory = create_session_factory()
    with session_factory() as session:
        row = RawWebRobotsPolicy(
            host_id=host_id,
            fetch_status=fetch_status,
            policy_blob=robots_txt,
            evaluation_summary_json=json.dumps(evaluation_summary, sort_keys=True),
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return int(row.id)


def evaluate_and_persist_robots(
    *,
    host_id: int,
    robots_txt: str,
    target_url: str,
    user_agent: str = "*",
    fetch_status: str = "success",
) -> bool:
    allowed = evaluate_robots_allow(robots_txt, target_url, user_agent=user_agent)
    persist_robots_policy(
        host_id=host_id,
        robots_txt=robots_txt,
        fetch_status=fetch_status,
        evaluation_summary={
            "target_url": target_url,
            "user_agent": user_agent,
            "allowed": allowed,
            "host": urlsplit(target_url).netloc,
        },
    )
    return allowed
