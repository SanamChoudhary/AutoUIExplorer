"""
AutoUIExplorer – main entry point.

Modes
-----
  python main.py                     → Start the Adaptive SaaS Onboarding API (FastAPI)
  python main.py --track [URL]       → Launch browser tracker to explore a website
  python main.py --explore           → Run the original UI Explorer flow (legacy)
"""

import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_api():
    """Launch the FastAPI Onboarding State API."""
    import uvicorn
    print("=" * 60)
    print("  ADAPTIVE SAAS ONBOARDING - API SERVER")
    print("=" * 60)
    print("\n  API:  http://127.0.0.1:8000")
    print("  Docs: http://127.0.0.1:8000/docs")
    print("\n  To track a website, run in another terminal:")
    print("    python main.py --track <URL>")
    print("\n" + "=" * 60 + "\n")
    uvicorn.run("app.api:app", host="127.0.0.1", port=8000, reload=True)


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


def run_explorer():
    """Original UI Explorer flow (preserved for legacy)."""
    from app.core import knowledge_graph as kg
    from legacy import website_Interact as wi
    from urllib.parse import urljoin

    URL = input("Enter the URL of the website: ")

    allClickables = wi.getClickables(URL)
    print(f"Found {len(allClickables)} clickable elements on {URL}")

    source_node = kg.addNode(URL, len(allClickables))

    running = True
    while running:
        for c in allClickables:
            if c.get("href") is not None:
                next_clickable = c.get("href")
            else:
                next_clickable = None

            print(f"Next clickable selected: {next_clickable}")

            if next_clickable is None:
                print("No more clickable elements with href found. Stopping navigation.")
                running = False
            else:
                next_clickable.click()
                print(f"After clicking, found clickables on next page")

                target_node = kg.addNode("next_url", 0)
                kg.addEdge(source_node, target_node, label=(c.get("text") or "click"))
                print("Graph updated: added nodes and edge for navigation.")


def print_help():
    """Print usage information."""
    print("""
AutoUIExplorer - Adaptive SaaS Onboarding Framework
====================================================

Usage:
  python main.py                Start the API server
  python main.py --track [URL]  Track browsing on a website
  python main.py --explore      Legacy UI explorer mode
  python main.py --help         Show this help message

Examples:
  # Start the API server first:
  python main.py
  
  # Then in another terminal, track a website:
  python main.py --track https://example.com
""")


if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        print_help()
    elif "--track" in sys.argv:
        # Get URL from arguments if provided
        idx = sys.argv.index("--track")
        url = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
        run_tracker(url)
    elif "--explore" in sys.argv:
        run_explorer()
    else:
        run_api()
