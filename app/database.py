"""
SQLite database setup and access layer for events and metrics snapshots.
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Optional
from app.models import Event, MetricsSnapshot

# Store database in project root data folder
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "onboarding.db")

# Ensure data directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

_initialized = False


def get_connection() -> sqlite3.Connection:
    """Get a SQLite connection with row factory enabled. Auto-initializes tables."""
    global _initialized
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if not _initialized:
        _init_tables(conn)
        _initialized = True
    return conn


def _init_tables(conn: sqlite3.Connection):
    """Create tables if they don't exist."""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userId TEXT NOT NULL,
            action TEXT NOT NULL,
            featureId TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userId TEXT NOT NULL,
            stage TEXT NOT NULL,
            coverageScore REAL NOT NULL,
            taskSuccessRate REAL NOT NULL,
            timeToActivation REAL,
            timestamp TEXT NOT NULL
        )
    """)

    conn.commit()


def init_db():
    """Initialize the database tables if they don't exist."""
    conn = get_connection()
    conn.close()


def store_event(event: Event):
    """Store a user action event in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO events (userId, action, featureId, timestamp) VALUES (?, ?, ?, ?)",
        (event.userId, event.action, event.featureId, event.timestamp.isoformat()),
    )
    conn.commit()
    conn.close()


def get_user_events(user_id: str) -> List[dict]:
    """Retrieve all events for a given user, ordered by timestamp."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT userId, action, featureId, timestamp FROM events WHERE userId = ? ORDER BY timestamp ASC",
        (user_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def store_metrics_snapshot(snapshot: MetricsSnapshot):
    """Store a metrics snapshot in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO metrics_snapshots (userId, stage, coverageScore, taskSuccessRate, timeToActivation, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (
            snapshot.userId,
            snapshot.stage,
            snapshot.coverageScore,
            snapshot.taskSuccessRate,
            snapshot.timeToActivation,
            snapshot.timestamp.isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def get_user_metrics_history(user_id: str) -> List[dict]:
    """Retrieve all metrics snapshots for a user, ordered by timestamp."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT userId, stage, coverageScore, taskSuccessRate, timeToActivation, timestamp FROM metrics_snapshots WHERE userId = ? ORDER BY timestamp ASC",
        (user_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
