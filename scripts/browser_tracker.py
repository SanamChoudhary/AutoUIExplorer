"""
Browser Tracker – Opens a browser and tracks user navigation in real-time.

This script launches a Playwright browser, watches for page navigations,
and logs clicks in real-time while building a knowledge graph.

Usage:
    python main.py --track [URL]
    python scripts/browser_tracker.py [URL]
    
On browser close, outputs:
    - Comprehension level (based on navigation patterns)
    - Full knowledge graph (saved to data/knowledge_graph.json)
"""

import sys
import os
import json
import time
from datetime import datetime
from urllib.parse import urlparse
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright, Page
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

USER_ID = "browser-user"

# ANSI colors for terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def colored(text: str, color: str) -> str:
    """Wrap text in ANSI color codes."""
    return f"{color}{text}{Colors.END}"


def log(message: str = ""):
    """Print with immediate flush for real-time output."""
    print(message, flush=True)


class BrowserTracker:
    """Tracks user navigation and builds a knowledge graph in real-time."""
    
    def __init__(self, user_id: str = USER_ID):
        self.user_id = user_id
        self.current_url: Optional[str] = None
        self.previous_url: Optional[str] = None
        self.base_domain: Optional[str] = None
        self.visited_urls: set[str] = set()
        self.navigation_history: list[dict] = []
        self.start_time: Optional[datetime] = None
        
        # Local knowledge graph
        self.graph = nx.DiGraph()
        
    def _normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and trailing slashes."""
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        return normalized.rstrip("/") or normalized
    
    def _is_same_domain(self, url: str) -> bool:
        """Check if URL is on the same domain as the base URL."""
        if not self.base_domain:
            return True
        parsed = urlparse(url)
        return parsed.netloc == self.base_domain or parsed.netloc.endswith(f".{self.base_domain}")
    
    def _url_to_feature_id(self, url: str) -> str:
        """Convert URL to a simple feature ID."""
        parsed = urlparse(url)
        path = parsed.path.strip("/") or "home"
        
        # Remove common file extensions
        for ext in [".html", ".htm", ".php", ".asp", ".aspx"]:
            if path.endswith(ext):
                path = path[:-len(ext)]
        
        # Get the meaningful part of the path (last 2 segments max)
        parts = [p for p in path.split("/") if p and p != "index"]
        if not parts:
            return "home"
        
        # Take the last meaningful segment
        feature_id = parts[-1].replace("-", "_").lower()
        return feature_id or "home"
    
    def _url_to_name(self, url: str) -> str:
        """Convert a URL path to a human-readable name."""
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        
        if not path:
            return "Home"
        
        # Remove file extensions
        for ext in [".html", ".htm", ".php", ".asp", ".aspx"]:
            if path.endswith(ext):
                path = path[:-len(ext)]
        
        # Get path segments, excluding "index"
        parts = [p for p in path.split("/") if p and p.lower() != "index"]
        
        if not parts:
            return "Home"
        
        # Use the last meaningful segment as the name
        name = parts[-1].replace("-", " ").replace("_", " ").title()
        return name or "Home"
    
    def _add_to_graph(self, url: str) -> str:
        """Add a URL node to the knowledge graph."""
        feature_id = self._url_to_feature_id(url)
        
        if feature_id not in self.graph.nodes:
            self.graph.add_node(
                feature_id,
                id=feature_id,
                name=self._url_to_name(url),
                url=url,
                visit_count=1
            )
        else:
            # Increment visit count
            self.graph.nodes[feature_id]["visit_count"] += 1
            
        return feature_id
    
    def _add_edge(self, from_url: str, to_url: str):
        """Add an edge between two URL nodes."""
        from_id = self._url_to_feature_id(from_url)
        to_id = self._url_to_feature_id(to_url)
        
        if from_id != to_id:
            if self.graph.has_edge(from_id, to_id):
                self.graph.edges[from_id, to_id]["count"] += 1
            else:
                self.graph.add_edge(from_id, to_id, relationship="navigated_to", count=1)
    
    def _log_navigation(self, url: str, is_new: bool):
        """Log navigation to terminal in real-time."""
        feature_id = self._url_to_feature_id(url)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Colorful real-time logging
        action = "NEW" if is_new else "REVISIT"
        action_color = Colors.GREEN if is_new else Colors.YELLOW
        
        log(f"\n  {colored(f'[{timestamp}]', Colors.CYAN)} {colored(action, action_color)} -> {colored(feature_id, Colors.BOLD)}")
        log(f"           {self._url_to_name(url)}")
        log(f"           {colored(f'[{len(self.graph.nodes)} pages tracked]', Colors.BLUE)}")
    
    def on_navigation(self, page: Page):
        """Handle page navigation events."""
        url = self._normalize_url(page.url)
        
        # Skip if same URL or external domain
        if url == self.current_url:
            return
        if not self._is_same_domain(url):
            log(f"  {colored('[SKIP]', Colors.RED)} External: {url[:50]}...")
            return
        
        # Track navigation
        is_new = url not in self.visited_urls
        self.previous_url = self.current_url
        self.current_url = url
        self.visited_urls.add(url)
        
        # Add to graph
        self._add_to_graph(url)
        if self.previous_url:
            self._add_edge(self.previous_url, url)
        
        # Record in history
        self.navigation_history.append({
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "feature_id": self._url_to_feature_id(url),
            "is_new": is_new
        })
        
        # Log to terminal
        self._log_navigation(url, is_new)
    
    def _calculate_comprehension(self) -> dict:
        """Calculate comprehension level based on navigation patterns."""
        total_pages = len(self.visited_urls)
        total_navigations = len(self.navigation_history)
        unique_paths = len(self.graph.edges)
        
        # Determine comprehension level
        if total_pages >= 10 and unique_paths >= 8:
            level = "Expert"
            description = "Thorough exploration with deep navigation"
        elif total_pages >= 6 and unique_paths >= 4:
            level = "Proficient"
            description = "Good coverage of key areas"
        elif total_pages >= 3:
            level = "Exploring"
            description = "Basic familiarity with the site"
        elif total_pages >= 1:
            level = "Novice"
            description = "Just getting started"
        else:
            level = "None"
            description = "No pages visited"
        
        return {
            "level": level,
            "description": description,
            "pages_visited": total_pages,
            "total_navigations": total_navigations,
            "unique_paths": unique_paths
        }
    
    def _save_knowledge_graph(self) -> str:
        """Save the knowledge graph to a JSON file."""
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, "knowledge_graph.json")
        
        # Convert graph to JSON-serializable format
        graph_data = {
            "nodes": [
                {
                    "id": n,
                    "name": self.graph.nodes[n].get("name", n),
                    "url": self.graph.nodes[n].get("url", ""),
                    "visits": self.graph.nodes[n].get("visit_count", 1)
                }
                for n in self.graph.nodes
            ],
            "edges": [
                {"from": u, "to": v, "count": self.graph.edges[u, v].get("count", 1)}
                for u, v in self.graph.edges
            ]
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, indent=2)
        
        return output_path
    
    def _visualize_knowledge_graph(self):
        """Display the knowledge graph using matplotlib."""
        if len(self.graph.nodes) == 0:
            return
        
        # Create figure
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        fig.suptitle('Knowledge Graph - Navigation Map', fontsize=16, fontweight='bold')
        
        # Choose layout based on graph size
        if len(self.graph.nodes) <= 5:
            pos = nx.spring_layout(self.graph, k=2, iterations=50, seed=42)
        else:
            pos = nx.kamada_kawai_layout(self.graph)
        
        # Color nodes by visit count
        visit_counts = [self.graph.nodes[n].get('visit_count', 1) for n in self.graph.nodes]
        max_visits = max(visit_counts) if visit_counts else 1
        node_colors = [plt.cm.Blues(0.3 + 0.7 * (v / max_visits)) for v in visit_counts]
        
        # Size nodes by visit count
        node_sizes = [800 + 400 * (v / max_visits) for v in visit_counts]
        
        # Draw edges with arrows
        edge_counts = [self.graph.edges[u, v].get('count', 1) for u, v in self.graph.edges]
        max_edge_count = max(edge_counts) if edge_counts else 1
        edge_widths = [1 + 2 * (c / max_edge_count) for c in edge_counts]
        
        nx.draw_networkx_edges(
            self.graph, pos, ax=ax,
            edge_color='#888888',
            width=edge_widths,
            alpha=0.6,
            arrows=True,
            arrowsize=20,
            arrowstyle='-|>',
            connectionstyle='arc3,rad=0.1'
        )
        
        # Draw nodes
        nx.draw_networkx_nodes(
            self.graph, pos, ax=ax,
            node_color=node_colors,
            node_size=node_sizes,
            edgecolors='#333333',
            linewidths=2
        )
        
        # Draw labels
        labels = {n: self.graph.nodes[n].get('name', n) for n in self.graph.nodes}
        nx.draw_networkx_labels(
            self.graph, pos, labels, ax=ax,
            font_size=9,
            font_weight='bold'
        )
        
        # Add legend
        legend_elements = [
            mpatches.Patch(facecolor=plt.cm.Blues(0.3), edgecolor='#333', label='Few visits'),
            mpatches.Patch(facecolor=plt.cm.Blues(1.0), edgecolor='#333', label='Many visits'),
        ]
        ax.legend(handles=legend_elements, loc='upper left', fontsize=9)
        
        # Add stats text
        stats_text = f"Pages: {len(self.graph.nodes)} | Paths: {len(self.graph.edges)}"
        ax.text(0.5, -0.05, stats_text, transform=ax.transAxes, 
                ha='center', fontsize=10, color='#666666')
        
        ax.set_axis_off()
        plt.tight_layout()
        
        # Save the figure
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        graph_image_path = os.path.join(output_dir, "knowledge_graph.png")
        plt.savefig(graph_image_path, dpi=150, bbox_inches='tight', facecolor='white')
        
        print(f"  {colored('KNOWLEDGE GRAPH IMAGE SAVED TO:', Colors.YELLOW + Colors.BOLD)}")
        print(f"    {colored(graph_image_path, Colors.GREEN)}")
        
        # Show the graph
        plt.show()
    
    def _print_summary(self):
        """Print session summary with comprehension level."""
        comp = self._calculate_comprehension()
        graph_path = self._save_knowledge_graph()
        
        print("\n\n" + colored("=" * 60, Colors.HEADER))
        print(colored("  SESSION COMPLETE", Colors.HEADER + Colors.BOLD))
        print(colored("=" * 60, Colors.HEADER))
        
        # Comprehension level - prominent display
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
        self._visualize_knowledge_graph()
    
    def start(self, start_url: str):
        """Start the browser tracker with the given URL."""
        parsed = urlparse(start_url)
        self.base_domain = parsed.netloc
        self.start_time = datetime.now()
        
        log("\n" + colored("=" * 60, Colors.HEADER))
        log(colored("  AUTOUIEXPLORER - BROWSER TRACKER", Colors.HEADER + Colors.BOLD))
        log(colored("=" * 60, Colors.HEADER))
        log(f"\n  {colored('Starting URL:', Colors.CYAN)} {start_url}")
        log(f"  {colored('Domain:', Colors.CYAN)} {self.base_domain}")
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
                    self.on_navigation(self._current_page)
            
            # Set up multiple navigation listeners for reliability
            page.on("framenavigated", handle_navigation)
            page.on("load", lambda: self.on_navigation(page))
            
            # Navigate to starting URL
            page.goto(start_url, wait_until="domcontentloaded")
            # Note: The load/framenavigated event handlers will log the initial page
            
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
                        current = self._normalize_url(page.url)
                        if current != self.current_url and self._is_same_domain(current):
                            self.on_navigation(page)
                    except:
                        break
            except KeyboardInterrupt:
                log(f"\n\n  {colored('[Tracker stopped by user]', Colors.YELLOW)}")
            finally:
                browser.close()
        
        self._print_summary()


def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("\nEnter the URL to explore: ").strip()
    
    if not url:
        print("Error: No URL provided")
        sys.exit(1)
    
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    user_id = sys.argv[2] if len(sys.argv) > 2 else USER_ID
    
    tracker = BrowserTracker(user_id=user_id)
    tracker.start(url)


if __name__ == "__main__":
    main()
