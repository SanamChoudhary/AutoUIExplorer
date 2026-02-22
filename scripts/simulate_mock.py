"""
Simulation script – sends 15 sequential events for a test user and then
prints the final state + full metrics history.

Usage:
  1. Start the API:       python main.py
  2. In another terminal:  python simulate.py
"""

import requests
import time
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000"
USER_ID = "test-user-001"

# 15 events that walk a user from Novice → Retained
EVENTS = [
    # ── Novice stage ──
    {"action": "visit",    "featureId": "signup"},
    # ── Still Novice (1/13 ≈ 7.7%) ──
    {"action": "visit",    "featureId": "dashboard"},
    # ── Exploring (2/13 ≈ 15.4%, visited core feature 'dashboard') ──
    {"action": "visit",    "featureId": "profile_setup"},
    {"action": "visit",    "featureId": "project_management"},
    # ── Exploring → Activating boundary (4/13 ≈ 30.8%) ──
    {"action": "complete", "featureId": "create_project"},
    # ── Activating (5/13 ≈ 38.5%, 1 key task done) ──
    {"action": "visit",    "featureId": "team_collaboration"},
    {"action": "complete", "featureId": "invite_team_member"},
    # ── Activating (7/13 ≈ 53.8%, 2 key tasks) ──
    {"action": "complete", "featureId": "configure_integration"},
    # ── Proficient (8/13 ≈ 61.5%, 3 key tasks) ──
    {"action": "visit",    "featureId": "analytics"},
    {"action": "complete", "featureId": "create_report"},
    # ── Proficient (10/13 ≈ 76.9%, 4 key tasks) ──
    {"action": "complete", "featureId": "set_up_automation"},
    # ── Retained (11/13 ≈ 84.6%) ──
    {"action": "visit",    "featureId": "billing"},
    {"action": "visit",    "featureId": "advanced_settings"},
    # 13/13 = 100%
    {"action": "revisit",  "featureId": "dashboard"},
    {"action": "revisit",  "featureId": "analytics"},
]


def main():
    print(f"=== Simulating {len(EVENTS)} events for user '{USER_ID}' ===\n")

    base_time = datetime.utcnow()

    for i, ev in enumerate(EVENTS, start=1):
        payload = {
            "userId": USER_ID,
            "action": ev["action"],
            "featureId": ev["featureId"],
            "timestamp": (base_time + timedelta(seconds=i * 10)).isoformat(),
        }

        resp = requests.post(f"{BASE_URL}/event", json=payload)
        if resp.status_code != 200:
            print(f"  [{i}] ERROR: {resp.status_code} – {resp.text}")
            continue

        data = resp.json()
        state = data["state"]
        snap = data["metricsSnapshot"]
        print(
            f"  [{i:>2}] {ev['action']:>8} {ev['featureId']:<25} "
            f"→ stage={state['stage']:<12} coverage={state['coverageScore']:.2%}  "
            f"taskSuccess={snap['taskSuccessRate']:.0%}"
        )

        time.sleep(0.1)  # small delay to keep timestamps distinct

    # ── Fetch final state ─────────────────────────────────────────────────
    print(f"\n=== Final state for '{USER_ID}' ===\n")
    resp = requests.get(f"{BASE_URL}/user/{USER_ID}/state")
    if resp.status_code != 200:
        print(f"ERROR: {resp.status_code} – {resp.text}")
        return

    result = resp.json()
    state = result["state"]
    print(f"  userId       : {state['userId']}")
    print(f"  stage        : {state['stage']}")
    print(f"  coverageScore: {state['coverageScore']:.2%}")
    print(f"  currentNode  : {state['currentNode']}")
    print(f"  visitedNodes : {state['visitedNodes']}")

    print(f"\n=== Metrics History ({len(result['metricsHistory'])} snapshots) ===\n")
    for h in result["metricsHistory"]:
        print(
            f"  {h['timestamp']}  stage={h['stage']:<12} "
            f"coverage={h['coverageScore']:.2%}  taskSuccess={h['taskSuccessRate']:.0%}  "
            f"tta={h['timeToActivation']}"
        )


if __name__ == "__main__":
    main()
