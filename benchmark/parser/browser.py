"""
Playwright browser management - launch, fetch pages, shutdown.
"""

from __future__ import annotations

import time
import logging
from typing import TYPE_CHECKING

from .constants import USER_AGENT

if TYPE_CHECKING:
    from playwright.sync_api import Browser, BrowserContext, Page

logger = logging.getLogger(__name__)

_PLAYWRIGHT_INSTANCE = None
_BROWSER: "Browser | None" = None
_BROWSER_CTX: "BrowserContext | None" = None


def init_browser() -> None:
    """Launch headless Chromium via Playwright."""
    global _PLAYWRIGHT_INSTANCE, _BROWSER, _BROWSER_CTX

    from playwright.sync_api import sync_playwright
    _PLAYWRIGHT_INSTANCE = sync_playwright().start()
    _BROWSER = _PLAYWRIGHT_INSTANCE.chromium.launch(headless=True)
    _BROWSER_CTX = _BROWSER.new_context(
        user_agent=USER_AGENT,
        viewport={"width": 1280, "height": 900},
    )
    logger.info("Playwright browser launched (headless Chromium)")


def shutdown_browser() -> None:
    """Cleanly close the browser / Playwright instance."""
    global _PLAYWRIGHT_INSTANCE, _BROWSER, _BROWSER_CTX
    if _BROWSER_CTX:
        _BROWSER_CTX.close()
        _BROWSER_CTX = None
    if _BROWSER:
        _BROWSER.close()
        _BROWSER = None
    if _PLAYWRIGHT_INSTANCE:
        _PLAYWRIGHT_INSTANCE.stop()
        _PLAYWRIGHT_INSTANCE = None


def fetch_html(url: str, timeout_ms: int = 30_000) -> str | None:
    """Fetch the fully-rendered HTML of *url* via Playwright."""
    page: "Page | None" = None
    try:
        page = _BROWSER_CTX.new_page()
        page.goto(url, wait_until="networkidle", timeout=timeout_ms)
        _expand_hidden_content(page)
        html = page.content()
        return html
    except Exception as e:
        logger.warning("Playwright error on %s: %s", url, e)
        return None
    finally:
        if page:
            page.close()


def _expand_hidden_content(page: "Page") -> None:
    """Click common 'show more' / tab elements so hidden steps are visible."""
    try:
        for tab in page.query_selector_all('[role="tab"]'):
            try:
                tab.click(timeout=500)
                time.sleep(0.15)
            except Exception:
                pass
        page.evaluate(
            "document.querySelectorAll('details:not([open])')"
            ".forEach(d => d.setAttribute('open', ''))"
        )
    except Exception:
        pass
