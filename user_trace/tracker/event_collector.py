"""
Raw event capture for browser navigation.

The EventCollector sits between the browser automation layer and the
knowledge graph.  It receives raw page URLs, deduplicates / filters
them, updates the graph, and logs each event to the terminal.
"""

from datetime import datetime
from typing import Optional

from user_trace.graph.url_utils import normalize_url, is_same_domain, url_to_feature_id, url_to_name
from user_trace.graph.knowledge_graph import KnowledgeGraph
from user_trace.ui.console import Colors, colored, log


class EventCollector:
    """Captures navigation events and feeds them into a KnowledgeGraph."""

    def __init__(self, knowledge_graph: KnowledgeGraph, base_domain: str):
        self.knowledge_graph = knowledge_graph
        self.base_domain = base_domain
        self.current_url: Optional[str] = None
        self.previous_url: Optional[str] = None
        self.visited_urls: set[str] = set()
        self.navigation_history: list[dict] = []

    def on_navigation(self, raw_url: str) -> bool:
        """Process a navigation event for the given URL.

        Normalizes the URL, skips duplicates and external domains, then
        records the visit in the knowledge graph and navigation history.

        Returns:
            ``True`` if the navigation was recorded, ``False`` if it
            was skipped (duplicate or external domain).
        """
        url = normalize_url(raw_url)

        # Skip if same URL
        if url == self.current_url:
            return False

        # Skip external domains
        if not is_same_domain(url, self.base_domain):
            log(f"  {colored('[SKIP]', Colors.RED)} External: {url[:50]}...")
            return False

        # Track navigation
        is_new = url not in self.visited_urls
        self.previous_url = self.current_url
        self.current_url = url
        self.visited_urls.add(url)

        # Update graph
        self.knowledge_graph.add_page(url)
        if self.previous_url:
            self.knowledge_graph.add_edge(self.previous_url, url)

        # Record in history
        self.navigation_history.append({
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "feature_id": url_to_feature_id(url),
            "is_new": is_new
        })

        # Log to terminal
        self._log_navigation(url, is_new)

        return True

    def _log_navigation(self, url: str, is_new: bool):
        """Log navigation to terminal in real-time."""
        feature_id = url_to_feature_id(url)
        timestamp = datetime.now().strftime("%H:%M:%S")

        action = "NEW" if is_new else "REVISIT"
        action_color = Colors.GREEN if is_new else Colors.YELLOW

        log(f"\n  {colored(f'[{timestamp}]', Colors.CYAN)} {colored(action, action_color)} -> {colored(feature_id, Colors.BOLD)}")
        log(f"           {url_to_name(url)}")
        log(f"           {colored(f'[{len(self.knowledge_graph.nodes)} pages tracked]', Colors.BLUE)}")
