"""
FastAPI application – State API for the Adaptive SaaS Onboarding Framework.

Endpoints
---------
POST /init           – initialize dynamic knowledge graph for a URL
POST /event          – accept a user event, store it, recompute state, log metrics
GET  /user/{userId}/state – return current user state + full metrics history
GET  /graph          – return the SaaS knowledge graph (for debugging / visualization)
GET  /graph/stats    – return knowledge graph statistics
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Optional
from pydantic import BaseModel

from app import database as db
from app.core import knowledge_graph as kg
from app.models import Event, UserState, MetricsSnapshot, UserStateResponse
from app.core.user_state import compute_user_state
from app.core.metrics_logger import log_metrics


class InitRequest(BaseModel):
    """Request body for initializing a dynamic knowledge graph."""
    url: str
    userId: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB (but don't pre-build graph - let it be dynamic)."""
    db.init_db()
    # Don't build mock graph - start empty for dynamic tracking
    yield


app = FastAPI(
    title="Adaptive SaaS Onboarding – State API",
    version="0.2.0",
    lifespan=lifespan,
)

# Allow CORS for browser-based tools
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── POST /init ────────────────────────────────────────────────────────────────

@app.post("/init")
async def init_graph(request: InitRequest):
    """
    Initialize a fresh dynamic knowledge graph for exploring a website.
    Call this before starting a new browsing session.
    """
    kg.init_dynamic_graph(request.url)
    return {
        "status": "ok",
        "message": f"Knowledge graph initialized for {request.url}",
        "stats": kg.get_graph_stats(),
    }


# ── POST /event ───────────────────────────────────────────────────────────────

@app.post("/event", response_model=dict)
async def post_event(event: Event):
    """
    Accept a user action event.
    1. If featureId doesn't exist, create it dynamically.
    2. Store the raw event in SQLite.
    3. Recompute the user's state.
    4. Log a metrics snapshot.
    """
    # Dynamically create the feature if it doesn't exist
    if kg.get_node(event.featureId) is None:
        kg.get_node_or_create(event.featureId)

    db.store_event(event)

    state = compute_user_state(event.userId)
    snapshot = log_metrics(state)

    return {
        "status": "ok",
        "state": state.model_dump(),
        "metricsSnapshot": snapshot.model_dump(),
    }


# ── GET /user/{userId}/state ──────────────────────────────────────────────────

@app.get("/user/{userId}/state", response_model=UserStateResponse)
async def get_user_state(userId: str):
    """
    Return the user's current state object and full metrics history.
    """
    events = db.get_user_events(userId)
    if not events:
        raise HTTPException(status_code=404, detail=f"No events found for user '{userId}'.")

    state = compute_user_state(userId)
    raw_history = db.get_user_metrics_history(userId)

    history = [
        MetricsSnapshot(
            userId=h["userId"],
            stage=h["stage"],
            coverageScore=h["coverageScore"],
            taskSuccessRate=h["taskSuccessRate"],
            timeToActivation=h["timeToActivation"],
            timestamp=h["timestamp"],
        )
        for h in raw_history
    ]

    return UserStateResponse(state=state, metricsHistory=history)


# ── GET /graph ────────────────────────────────────────────────────────────────

@app.get("/graph")
async def get_graph():
    """Return the knowledge graph nodes and edges (for debugging/visualization)."""
    g = kg.get_saas_graph()
    nodes = [{"id": n, **g.nodes[n]} for n in g.nodes]
    edges = [{"source": u, "target": v, **d} for u, v, d in g.edges(data=True)]
    return {"nodes": nodes, "edges": edges}


# ── GET /graph/stats ──────────────────────────────────────────────────────────

@app.get("/graph/stats")
async def get_graph_stats():
    """Return statistics about the current knowledge graph."""
    return kg.get_graph_stats()


# ── POST /reset ───────────────────────────────────────────────────────────────

@app.post("/reset")
async def reset_session():
    """
    Reset the session: clear the knowledge graph and optionally clear events.
    Use this to start fresh with a new website.
    """
    kg.saasGraph.clear()
    return {"status": "ok", "message": "Knowledge graph cleared"}
