"""
AutoUIExplorer - Browser Navigation Tracker

Usage:
  python main.py --track [URL]   → Track a website  
  python main.py --help          → Show help
"""

import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main(url: str):
    """Launch the browser tracker to explore a website."""
    from user_trace.tracker.browser import BrowserTracker
    
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
  python main.py --track [URL]  Track a website
  python main.py --help         Show this help

Examples:
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
        main(url)
    else:
        print_help()
