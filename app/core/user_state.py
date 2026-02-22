"""
User State Model – reads event history, maps onto the knowledge graph,
and computes the user's current onboarding state.

Supports both:
- Predefined graphs with key tasks and core features from config
- Dynamic graphs built from real-time browsing (coverage-based staging)
"""

import json
import os
from datetime import datetime
from typing import List

from app import database as db
from app.core import knowledge_graph as kg
from app.models import UserState

# Config is in project root config folder
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "stage_rules.json")


def _load_config() -> dict:
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Return minimal config for dynamic mode
        return {
            "stages": [
                {"name": "Retained", "order": 5, "rules": {"minCoverageScore": 0.80}},
                {"name": "Proficient", "order": 4, "rules": {"minCoverageScore": 0.60}},
                {"name": "Activating", "order": 3, "rules": {"minCoverageScore": 0.30}},
                {"name": "Exploring", "order": 2, "rules": {"minCoverageScore": 0.10}},
                {"name": "Novice", "order": 1, "rules": {}},
            ],
            "keyTasks": [],
            "coreFeatures": [],
        }


def _infer_stage_dynamic(coverage: float, visited_count: int) -> str:
    """
    Infer stage based on absolute visit count for dynamic graphs.
    Since users discover pages as they browse, we use visit counts
    rather than percentages for stage transitions.
    
    Thresholds:
    - Novice: 1-2 pages visited
    - Exploring: 3-5 pages visited
    - Activating: 6-10 pages visited
    - Proficient: 11-20 pages visited
    - Retained: 20+ pages visited
    """
    if visited_count >= 20:
        return "Retained"
    elif visited_count >= 11:
        return "Proficient"
    elif visited_count >= 6:
        return "Activating"
    elif visited_count >= 3:
        return "Exploring"
    return "Novice"


def _infer_stage(coverage: float, visited: set, completed_key_tasks: int, config: dict) -> str:
    """
    Determine the user's onboarding stage based on the rules in the JSON config.
    Stages are evaluated from highest to lowest priority so the best match wins.
    If a user's coverage exceeds a boundary but they don't meet the next stage's
    extra requirements, they stay at the highest stage they fully qualify for.
    """
    core_features = set(config.get("coreFeatures", []))
    key_tasks = set(config.get("keyTasks", []))
    
    # Use dynamic staging when:
    # 1. We're in dynamic mode (base_url is set), OR
    # 2. No predefined features exist in config
    if kg.is_dynamic_mode() or (not core_features and not key_tasks):
        return _infer_stage_dynamic(coverage, len(visited))
    
    core_visited = len(visited & core_features)

    # Evaluate stages in descending order (highest first)
    sorted_stages = sorted(config["stages"], key=lambda s: s["order"], reverse=True)

    best_qualified: str | None = None

    for stage_def in sorted_stages:
        rules = stage_def["rules"]
        min_cov = rules.get("minCoverageScore", 0.0)
        max_cov = rules.get("maxCoverageScore", 1.01)  # slightly above 1 so 1.0 can match
        min_kt = rules.get("minKeyTasksCompleted", 0)
        min_cf = rules.get("minCoreFeaturesVisited", 0)

        if coverage >= min_cov:
            if completed_key_tasks >= min_kt and core_visited >= min_cf:
                if best_qualified is None:  # first (highest) match wins
                    best_qualified = stage_def["name"]

    return best_qualified or "Novice"


def compute_user_state(user_id: str) -> UserState:
    """
    Compute and return the current UserState for a given user.
    """
    config = _load_config()
    key_tasks = set(config.get("keyTasks", []))
    all_features = kg.get_all_feature_ids()
    total_nodes = len(all_features)

    events = db.get_user_events(user_id)

    visited: set[str] = set()
    current_node: str | None = None
    completed_key_tasks = 0

    for ev in events:
        fid = ev["featureId"]
        visited.add(fid)
        current_node = fid
        if fid in key_tasks:
            # Count each key task only once
            key_tasks.discard(fid)
            completed_key_tasks += 1

    coverage = len(visited) / total_nodes if total_nodes > 0 else 0.0
    
    # Determine if we're in dynamic mode by checking if visited nodes
    # are in the predefined config features. If none match, use dynamic staging.
    predefined_features = set(config.get("keyTasks", [])) | set(config.get("coreFeatures", []))
    uses_predefined = bool(visited & predefined_features)
    
    if uses_predefined and not kg.is_dynamic_mode():
        stage = _infer_stage(coverage, visited, completed_key_tasks, config)
    else:
        # Dynamic mode: use visit count based staging
        stage = _infer_stage_dynamic(coverage, len(visited))

    return UserState(
        userId=user_id,
        visitedNodes=sorted(visited),
        currentNode=current_node,
        coverageScore=round(coverage, 4),
        stage=stage,
    )
