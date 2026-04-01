"""
Playwright browser lifecycle and event wiring.

This module contains the BrowserTracker orchestrator that launches
a Chromium browser, wires Playwright events to an EventCollector,
and delegates analysis / visualisation to the appropriate modules.
"""

import sys
import os
from datetime import datetime
from urllib.parse import urlparse
from typing import Optional

from playwright.sync_api import sync_playwright

# Ensure project root is importable when this file is run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from user_trace.graph.knowledge_graph import KnowledgeGraph
from user_trace.graph.url_utils import normalize_url, is_same_domain
from user_trace.tracker.event_collector import EventCollector
from user_trace.analysis.comprehension import calculate_comprehension
from user_trace.ui.console import Colors, colored, log
from user_trace.ui.visualizer import visualize_knowledge_graph

USER_ID = "browser-user"


class BrowserTracker:
    """Launches a browser and tracks user navigation via an EventCollector."""

    def __init__(self, user_id: str = USER_ID):
        self.user_id = user_id
        self.knowledge_graph = KnowledgeGraph()
        self.collector: Optional[EventCollector] = None
        self.start_time: Optional[datetime] = None

    def _data_dir(self) -> str:
        """Return the path to the data output directory."""
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data"
        )

    def _print_summary(self):
        """Print session summary with comprehension level."""
        data_dir = self._data_dir()
        graph_path = self.knowledge_graph.save(os.path.join(data_dir, "knowledge_graph.json"))

        comp = calculate_comprehension(
            pages_visited=len(self.collector.visited_urls),
            total_navigations=len(self.collector.navigation_history),
            unique_paths=len(self.knowledge_graph.edges)
        )

        print("\n\n" + colored("=" * 60, Colors.HEADER))
        print(colored("  SESSION COMPLETE", Colors.HEADER + Colors.BOLD))
        print(colored("=" * 60, Colors.HEADER))

        # Comprehension level – prominent display
        print(f"\n  {colored('COMPREHENSION LEVEL:', Colors.YELLOW + Colors.BOLD)} {colored(comp['level'], Colors.GREEN + Colors.BOLD)}")
        print(f"  {comp['description']}")

        # Stats
        print(f"\n  {colored('SESSION STATS:', Colors.CYAN)}")
        print(f"    Pages Visited:     {comp['pages_visited']}")
        print(f"    Total Navigations: {comp['total_navigations']}")
        print(f"    Unique Paths:      {comp['unique_paths']}")

        # Where to find the full graph
        print(f"\n  {colored('KNOWLEDGE GRAPH DATA SAVED TO:', Colors.YELLOW + Colors.BOLD)}")
        print(f"    {colored(graph_path, Colors.GREEN)}")

        print("\n" + colored("=" * 60, Colors.HEADER) + "\n")

        # Visualize the graph
        print(f"  {colored('Opening knowledge graph visualization...', Colors.CYAN)}\n")
        visualize_knowledge_graph(self.knowledge_graph.graph, data_dir)

    def start(self, start_url: str):
        """Start the browser tracker with the given URL."""
        parsed = urlparse(start_url)
        base_domain = parsed.netloc
        self.start_time = datetime.now()
        self.collector = EventCollector(self.knowledge_graph, base_domain)

        log("\n" + colored("=" * 60, Colors.HEADER))
        log(colored("  AUTOUIEXPLORER - BROWSER TRACKER", Colors.HEADER + Colors.BOLD))
        log(colored("=" * 60, Colors.HEADER))
        log(f"\n  {colored('Starting URL:', Colors.CYAN)} {start_url}")
        log(f"  {colored('Domain:', Colors.CYAN)} {base_domain}")
        log(f"\n  Navigate the website normally.")
        log(f"  {colored('Close the browser when done to see your comprehension level.', Colors.YELLOW)}")
        log("\n" + colored("-" * 60, Colors.BLUE))
        log(colored("  REAL-TIME NAVIGATION LOG:", Colors.BLUE + Colors.BOLD))
        log(colored("-" * 60, Colors.BLUE))

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.new_page()

            # Track the current page reference (may change with new tabs)
            self._current_page = page

            def handle_navigation(frame):
                """Handle frame navigation events."""
                # Only track main frame navigations
                if frame == self._current_page.main_frame:
                    self.collector.on_navigation(self._current_page.url)

            # Set up multiple navigation listeners for reliability
            page.on("framenavigated", handle_navigation)
            page.on("load", lambda: self.collector.on_navigation(page.url))

            # Navigate to starting URL
            page.goto(start_url, wait_until="domcontentloaded")

            log(f"\n  {colored('[Browser is open - navigate freely]', Colors.GREEN)}")

            # Keep running while browser is open
            try:
                while True:
                    if not context.pages:
                        break
                    # Use Playwright's wait instead of time.sleep to allow event processing
                    try:
                        page.wait_for_timeout(300)
                    except:
                        break
                    # Also poll for URL changes as backup
                    try:
                        current = normalize_url(page.url)
                        if current != self.collector.current_url and is_same_domain(current, base_domain):
                            self.collector.on_navigation(page.url)
                    except:
                        break
            except KeyboardInterrupt:
                log(f"\n\n  {colored('[Tracker stopped by user]', Colors.YELLOW)}")
            finally:
                browser.close()

        self._print_summary()