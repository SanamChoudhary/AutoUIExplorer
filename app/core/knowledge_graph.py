import networkx as nx
from urllib.parse import urlparse, urljoin
import hashlib

knowledgeGraph = nx.DiGraph()


# ---------------------------------------------------------------------------
# Original UI-Explorer helpers (preserved)
# ---------------------------------------------------------------------------

def addNode(url, clickablesCount, graph: nx.DiGraph = knowledgeGraph):
    nodeID = len(graph.nodes) + 1
    graph.add_node(nodeID, url=url, clickablesCount=clickablesCount)
    return nodeID


def addEdge(sourceNodeID, targetNodeID, label=None, graph: nx.DiGraph = knowledgeGraph):
    graph.add_edge(sourceNodeID, targetNodeID, label=label or "click")


# ---------------------------------------------------------------------------
# Adaptive SaaS Onboarding – Dynamic Knowledge Graph
# ---------------------------------------------------------------------------

saasGraph = nx.DiGraph()
_base_url: str | None = None  # Tracks the starting URL for the session


def _url_to_feature_id(url: str) -> str:
    """Convert a URL to a consistent feature ID based on its path."""
    parsed = urlparse(url)
    # Use path as the feature ID, defaulting to 'home' for root
    path = parsed.path.strip("/") or "home"
    # Replace slashes with underscores and clean up
    feature_id = path.replace("/", "_").replace("-", "_").lower()
    # Remove common file extensions
    for ext in [".html", ".htm", ".php", ".asp", ".aspx"]:
        if feature_id.endswith(ext.replace(".", "_")):
            feature_id = feature_id[:-len(ext)+1]
    return feature_id or "home"


def _url_to_name(url: str) -> str:
    """Convert a URL path to a human-readable name."""
    parsed = urlparse(url)
    path = parsed.path.strip("/") or "Home"
    # Convert path to title case
    name = path.split("/")[-1].replace("-", " ").replace("_", " ").title()
    return name or "Home"


def _infer_complexity(url: str) -> str:
    """Infer complexity based on URL depth and patterns."""
    parsed = urlparse(url)
    depth = len([p for p in parsed.path.split("/") if p])
    if depth <= 1:
        return "low"
    elif depth <= 2:
        return "medium"
    return "high"


def _infer_category(url: str, name: str) -> str:
    """Infer category based on URL patterns and page name."""
    url_lower = url.lower()
    name_lower = name.lower()
    
    # Check for common patterns
    if any(kw in url_lower or kw in name_lower for kw in ["setting", "config", "admin", "account"]):
        return "admin"
    elif any(kw in url_lower or kw in name_lower for kw in ["dashboard", "home", "overview"]):
        return "core"
    elif any(kw in url_lower or kw in name_lower for kw in ["signup", "login", "register", "onboard"]):
        return "onboarding"
    elif any(kw in url_lower or kw in name_lower for kw in ["create", "add", "new", "edit", "delete"]):
        return "task"
    return "feature"


def init_dynamic_graph(base_url: str) -> nx.DiGraph:
    """
    Initialize a fresh dynamic knowledge graph for exploring a website.
    Call this when starting a new browsing session.
    """
    global saasGraph, _base_url
    saasGraph.clear()
    _base_url = base_url
    
    # Add the starting page as the first node
    add_or_get_node(base_url)
    
    return saasGraph


def add_or_get_node(url: str, element_text: str | None = None) -> str:
    """
    Add a node for a URL if it doesn't exist, or return existing node ID.
    Dynamically infers node properties from the URL.
    """
    global saasGraph
    
    feature_id = _url_to_feature_id(url)
    
    if feature_id not in saasGraph.nodes:
        name = element_text or _url_to_name(url)
        complexity = _infer_complexity(url)
        category = _infer_category(url, name)
        
        # Infer stage based on how many nodes exist (discovery order)
        node_count = len(saasGraph.nodes)
        if node_count < 3:
            stage = "Novice"
        elif node_count < 6:
            stage = "Exploring"
        elif node_count < 10:
            stage = "Activating"
        elif node_count < 15:
            stage = "Proficient"
        else:
            stage = "Retained"
        
        saasGraph.add_node(
            feature_id,
            id=feature_id,
            name=name,
            url=url,
            complexity=complexity,
            category=category,
            stage=stage
        )
    
    return feature_id


def add_navigation_edge(from_url: str, to_url: str, action: str = "click") -> tuple[str, str]:
    """
    Add an edge representing navigation from one page to another.
    Returns (from_feature_id, to_feature_id).
    """
    global saasGraph
    
    from_id = add_or_get_node(from_url)
    to_id = add_or_get_node(to_url)
    
    if from_id != to_id and not saasGraph.has_edge(from_id, to_id):
        saasGraph.add_edge(from_id, to_id, relationship="leads_to", action=action)
    
    return from_id, to_id


def build_saas_graph() -> nx.DiGraph:
    """
    Seed the SaaS feature knowledge graph with a mock application.
    Returns the populated DiGraph.

    Node properties : id, name, complexity, category, stage
    Edge properties : relationship  ("requires" | "unlocks" | "leads_to")
    """
    global saasGraph
    saasGraph.clear()

    # ── Nodes (10+ features / tasks) ──────────────────────────────────────
    nodes = [
        {"id": "signup",              "name": "Sign Up",                "complexity": "low",    "category": "onboarding", "stage": "Novice"},
        {"id": "dashboard",           "name": "Dashboard",             "complexity": "low",    "category": "core",       "stage": "Novice"},
        {"id": "profile_setup",       "name": "Profile Setup",         "complexity": "low",    "category": "onboarding", "stage": "Novice"},
        {"id": "project_management",  "name": "Project Management",    "complexity": "medium", "category": "core",       "stage": "Exploring"},
        {"id": "create_project",      "name": "Create Project",        "complexity": "medium", "category": "task",       "stage": "Exploring"},
        {"id": "team_collaboration",  "name": "Team Collaboration",    "complexity": "medium", "category": "core",       "stage": "Exploring"},
        {"id": "invite_team_member",  "name": "Invite Team Member",    "complexity": "medium", "category": "task",       "stage": "Activating"},
        {"id": "configure_integration","name": "Configure Integration","complexity": "high",   "category": "task",       "stage": "Activating"},
        {"id": "analytics",           "name": "Analytics",             "complexity": "medium", "category": "core",       "stage": "Proficient"},
        {"id": "create_report",       "name": "Create Report",         "complexity": "high",   "category": "task",       "stage": "Proficient"},
        {"id": "set_up_automation",   "name": "Set Up Automation",     "complexity": "high",   "category": "task",       "stage": "Proficient"},
        {"id": "billing",             "name": "Billing & Plans",       "complexity": "low",    "category": "admin",      "stage": "Retained"},
        {"id": "advanced_settings",   "name": "Advanced Settings",     "complexity": "high",   "category": "admin",      "stage": "Retained"},
    ]

    for n in nodes:
        saasGraph.add_node(n["id"], **n)

    # ── Edges (15+ relationships) ─────────────────────────────────────────
    edges = [
        ("signup",             "dashboard",            "unlocks"),
        ("signup",             "profile_setup",        "leads_to"),
        ("dashboard",          "project_management",   "leads_to"),
        ("dashboard",          "analytics",            "leads_to"),
        ("dashboard",          "team_collaboration",   "leads_to"),
        ("profile_setup",      "dashboard",            "leads_to"),
        ("project_management", "create_project",       "unlocks"),
        ("create_project",     "team_collaboration",   "leads_to"),
        ("team_collaboration", "invite_team_member",   "unlocks"),
        ("invite_team_member", "configure_integration","leads_to"),
        ("configure_integration","analytics",          "unlocks"),
        ("analytics",          "create_report",        "unlocks"),
        ("create_report",      "set_up_automation",    "leads_to"),
        ("set_up_automation",  "advanced_settings",    "leads_to"),
        ("advanced_settings",  "billing",              "leads_to"),
        ("dashboard",          "billing",              "leads_to"),
        ("project_management", "analytics",            "requires"),
    ]

    for src, dst, rel in edges:
        saasGraph.add_edge(src, dst, relationship=rel)

    return saasGraph


def get_saas_graph() -> nx.DiGraph:
    """Return the global SaaS graph (may be empty if using dynamic mode)."""
    return saasGraph


def get_all_feature_ids() -> list[str]:
    """Return a list of all feature/task node IDs in the SaaS graph."""
    return list(saasGraph.nodes)


def get_node(feature_id: str) -> dict | None:
    """Return node data for a given feature ID, or None."""
    if feature_id in saasGraph.nodes:
        return dict(saasGraph.nodes[feature_id])
    return None


def get_node_or_create(feature_id: str, url: str | None = None) -> dict:
    """
    Return node data for a feature ID, creating it if it doesn't exist.
    Used for dynamic graph building.
    """
    if feature_id not in saasGraph.nodes:
        if url:
            add_or_get_node(url)
        else:
            # Create a placeholder node
            saasGraph.add_node(
                feature_id,
                id=feature_id,
                name=feature_id.replace("_", " ").title(),
                complexity="medium",
                category="feature",
                stage="Exploring"
            )
    return dict(saasGraph.nodes[feature_id])


def is_dynamic_mode() -> bool:
    """Check if we're in dynamic graph building mode."""
    return _base_url is not None


def get_graph_stats() -> dict:
    """Return statistics about the current knowledge graph."""
    g = saasGraph
    return {
        "total_nodes": len(g.nodes),
        "total_edges": len(g.edges),
        "base_url": _base_url,
        "categories": list(set(g.nodes[n].get("category", "unknown") for n in g.nodes)),
    }