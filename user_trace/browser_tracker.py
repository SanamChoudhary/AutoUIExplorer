"""
Browser Tracker – backward-compatible re-export.

The implementation has moved to the scripts.tracker package.
See scripts/tracker/browser.py for the BrowserTracker class.
"""

from user_trace.tracker.browser import BrowserTracker, main  # noqa: F401

if __name__ == "__main__":
    main()
