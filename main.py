"""
AutoUIExplorer – Browser Navigation Tracker

Usage:
  python main.py [URL]           → Track a website
  python main.py --track [URL]   → Track a website  
  python main.py --help          → Show help
"""

import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_tracker(url: str | None = None):
    """Launch the browser tracker to explore a website."""
    from scripts.browser_tracker import BrowserTracker
    
    if not url:
        url = input("\nEnter the URL to explore: ").strip()
    
    if not url:
        print("Error: No URL provided")
        sys.exit(1)
    
    # Ensure URL has scheme
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    tracker = BrowserTracker()
    tracker.start(url)


def print_help():
    """Print usage information."""
    print("""
AutoUIExplorer - Browser Navigation Tracker & Knowledge Graph Builder
======================================================================

Usage:
  python main.py [URL]          Track a website
  python main.py --track [URL]  Track a website
  python main.py --help         Show this help

Examples:
  python main.py https://example.com
  python main.py --track https://books.toscrape.com

What happens:
  1. Browser opens - navigate the site freely
  2. Terminal shows real-time page visits
  3. Close browser to see:
     - Comprehension level
     - Session stats  
     - Knowledge graph visualization
  4. Graph saved to: data/knowledge_graph.json
""")


if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        print_help()
    elif "--track" in sys.argv:
        idx = sys.argv.index("--track")
        url = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
        run_tracker(url)
    elif len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        # Direct URL argument
        run_tracker(sys.argv[1])
    else:
        print_help()
