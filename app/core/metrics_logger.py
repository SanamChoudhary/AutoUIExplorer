"""
Metrics Logger – logs a MetricsSnapshot every time user state is computed.
"""

import json
import os
from datetime import datetime

from app import database as db
from app.models import MetricsSnapshot, UserState

# Config is in project root config folder
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "stage_rules.json")


def _load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def _compute_time_to_activation(user_id: str, current_stage: str) -> float | None:
    """
    Returns seconds between the user's first event and the first time they
    reached the 'Activating' stage (or higher).  Returns None if they haven't
    reached Activating yet.
    """
    activating_stages = {"Activating", "Proficient", "Retained"}

    # Check history for a previously recorded activation time
    history = db.get_user_metrics_history(user_id)
    for snap in history:
        if snap["stage"] in activating_stages and snap["timeToActivation"] is not None:
            return snap["timeToActivation"]

    if current_stage not in activating_stages:
        return None

    # First time reaching activation – compute from event timestamps
    events = db.get_user_events(user_id)
    if not events:
        return None

    first_ts = datetime.fromisoformat(events[0]["timestamp"])
    last_ts = datetime.fromisoformat(events[-1]["timestamp"])
    return (last_ts - first_ts).total_seconds()


def _compute_task_success_rate(user_id: str) -> float:
    """Percentage of key tasks the user has completed."""
    config = _load_config()
    key_tasks = set(config.get("keyTasks", []))
    if not key_tasks:
        return 0.0

    events = db.get_user_events(user_id)
    completed = {ev["featureId"] for ev in events if ev["featureId"] in key_tasks}
    return round(len(completed) / len(key_tasks), 4)


def log_metrics(state: UserState) -> MetricsSnapshot:
    """Build a MetricsSnapshot from the current state and persist it."""
    tta = _compute_time_to_activation(state.userId, state.stage)
    tsr = _compute_task_success_rate(state.userId)

    snapshot = MetricsSnapshot(
        userId=state.userId,
        stage=state.stage,
        coverageScore=state.coverageScore,
        taskSuccessRate=tsr,
        timeToActivation=tta,
        timestamp=datetime.utcnow(),
    )

    db.store_metrics_snapshot(snapshot)
    return snapshot
