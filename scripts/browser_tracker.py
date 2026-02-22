"""
Browser Tracker – Opens a browser and tracks user navigation in real-time.

This script launches a Playwright browser, watches for page navigations and clicks,
and sends events to the Adaptive SaaS Onboarding API to build a knowledge graph
dynamically as the user browses.

Usage:
    python browser_tracker.py [URL]
    
If no URL is provided, you'll be prompted to enter one.
"""

import sys
import requests
import time
from datetime import datetime
from urllib.parse import urlparse, urljoin
from playwright.sync_api import sync_playwright, Page, BrowserContext

API_BASE_URL = "http://127.0.0.1:8000"
USER_ID = "browser-user"


class BrowserTracker:
    def __init__(self, user_id: str = USER_ID):
        self.user_id = user_id
        self.current_url: str | None = None
        self.previous_url: str | None = None
        self.base_domain: str | None = None
        self.event_count = 0
        self.visited_urls: set[str] = set()
        
    def _normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and trailing slashes."""
        parsed = urlparse(url)
        # Rebuild without fragment
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        return normalized.rstrip("/") or normalized
    
    def _is_same_domain(self, url: str) -> bool:
        """Check if URL is on the same domain as the base URL."""
        if not self.base_domain:
            return True
        parsed = urlparse(url)
        return parsed.netloc == self.base_domain or parsed.netloc.endswith(f".{self.base_domain}")
    
    def _url_to_feature_id(self, url: str) -> str:
        """Convert URL to a feature ID (matching knowledge_Graph.py logic)."""
        parsed = urlparse(url)
        path = parsed.path.strip("/") or "home"
        feature_id = path.replace("/", "_").replace("-", "_").lower()
        for ext in [".html", ".htm", ".php", ".asp", ".aspx"]:
            if feature_id.endswith(ext.replace(".", "_")):
                feature_id = feature_id[:-len(ext)+1]
        return feature_id or "home"
    
    def send_event(self, action: str, url: str) -> dict | None:
        """Send a navigation event to the API."""
        feature_id = self._url_to_feature_id(url)
        
        payload = {
            "userId": self.user_id,
            "action": action,
            "featureId": feature_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        try:
            resp = requests.post(f"{API_BASE_URL}/event", json=payload, timeout=5)
            if resp.status_code == 200:
                self.event_count += 1
                data = resp.json()
                state = data.get("state", {})
                print(f"\n  [{self.event_count:>3}] {action:<10} → {feature_id}")
                print(f"        Stage: {state.get('stage', 'Unknown'):<12} Coverage: {state.get('coverageScore', 0):.1%}")
                print(f"        Visited: {len(state.get('visitedNodes', []))} nodes")
                return data
            elif resp.status_code == 400:
                # Feature not found - this is expected, API will create it dynamically
                print(f"  [!] New feature discovered: {feature_id}")
                return None
            else:
                print(f"  [!] API error: {resp.status_code}")
                return None
        except requests.exceptions.ConnectionError:
            print("  [!] Cannot connect to API. Is the server running?")
            return None
        except Exception as e:
            print(f"  [!] Error sending event: {e}")
            return None
    
    def on_navigation(self, page: Page):
        """Handle page navigation events."""
        url = self._normalize_url(page.url)
        
        # Skip if same URL or external domain
        if url == self.current_url:
            return
        if not self._is_same_domain(url):
            print(f"  [skip] External domain: {url[:60]}...")
            return
        
        # Track the navigation
        self.previous_url = self.current_url
        self.current_url = url
        
        # Determine action type
        if url in self.visited_urls:
            action = "revisit"
        else:
            action = "visit"
            self.visited_urls.add(url)
        
        # Send event to API
        self.send_event(action, url)
    
    def on_click(self, page: Page, element_info: dict):
        """Handle click events on interactive elements."""
        # This can be extended to track specific element clicks
        # For now, navigation is the primary tracking mechanism
        pass
    
    def start(self, start_url: str):
        """Start the browser tracker with the given URL."""
        parsed = urlparse(start_url)
        self.base_domain = parsed.netloc
        
        print("\n" + "=" * 60)
        print("  ADAPTIVE SAAS ONBOARDING - BROWSER TRACKER")
        print("=" * 60)
        print(f"\n  Starting URL: {start_url}")
        print(f"  User ID: {self.user_id}")
        print(f"  API: {API_BASE_URL}")
        print("\n  Navigate the website normally. Your actions are being tracked.")
        print("  Close the browser window when done.")
        print("-" * 60)
        
        # Initialize the graph via API
        try:
            resp = requests.post(f"{API_BASE_URL}/init", json={"url": start_url}, timeout=5)
            if resp.status_code == 200:
                print("  [✓] Knowledge graph initialized")
        except:
            print("  [!] Could not initialize graph (API may handle this automatically)")
        
        with sync_playwright() as p:
            # Launch browser (visible window)
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()
            
            # Set up navigation listener
            page.on("load", lambda: self.on_navigation(page))
            
            # Navigate to starting URL
            print(f"\n  Opening browser...")
            page.goto(start_url, wait_until="domcontentloaded")
            self.current_url = self._normalize_url(start_url)
            self.visited_urls.add(self.current_url)
            
            # Send initial visit event
            self.send_event("visit", start_url)
            
            print("\n  [Browser is open - navigate freely]")
            print("  Press Ctrl+C in this terminal or close the browser to stop.\n")
            
            # Keep the script running while browser is open
            try:
                while True:
                    # Check if browser is still open
                    if not context.pages:
                        break
                    # Poll for URL changes (backup to load event)
                    current = self._normalize_url(page.url)
                    if current != self.current_url and self._is_same_domain(current):
                        self.on_navigation(page)
                    time.sleep(0.5)
            except KeyboardInterrupt:
                print("\n\n  [Stopping tracker...]")
            finally:
                browser.close()
        
        self._print_summary()
    
    def _print_summary(self):
        """Print a summary of the browsing session."""
        print("\n" + "=" * 60)
        print("  SESSION SUMMARY")
        print("=" * 60)
        print(f"  Total events sent: {self.event_count}")
        print(f"  Unique pages visited: {len(self.visited_urls)}")
        
        # Fetch final state from API
        try:
            resp = requests.get(f"{API_BASE_URL}/user/{self.user_id}/state", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                state = data.get("state", {})
                print(f"\n  Final Stage: {state.get('stage', 'Unknown')}")
                print(f"  Coverage Score: {state.get('coverageScore', 0):.1%}")
                print(f"  Visited Nodes: {state.get('visitedNodes', [])}")
                
                history = data.get("metricsHistory", [])
                if history:
                    print(f"\n  Metrics Snapshots: {len(history)}")
                    latest = history[-1]
                    print(f"  Latest Task Success Rate: {latest.get('taskSuccessRate', 0):.0%}")
                    if latest.get("timeToActivation"):
                        print(f"  Time to Activation: {latest['timeToActivation']:.1f}s")
        except Exception as e:
            print(f"  [!] Could not fetch final state: {e}")
        
        print("\n" + "=" * 60 + "\n")


def main():
    # Get URL from command line or prompt
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("\nEnter the URL to explore: ").strip()
    
    if not url:
        print("Error: No URL provided")
        sys.exit(1)
    
    # Ensure URL has scheme
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    # Optional: Custom user ID
    user_id = USER_ID
    if len(sys.argv) > 2:
        user_id = sys.argv[2]
    
    # Start tracking
    tracker = BrowserTracker(user_id=user_id)
    tracker.start(url)


if __name__ == "__main__":
    main()
