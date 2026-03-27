"""
URL discovery - crawl a given documentation page to find article links.
"""

from __future__ import annotations

import logging
from urllib.parse import urljoin, urlparse

from .browser import fetch_html

logger = logging.getLogger(__name__)


def discover_urls(doc_url: str, limit: int = 50) -> list[str]:
    """Crawl *doc_url* and collect internal documentation links.

    Starting from the provided URL, fetches the rendered HTML via Playwright
    and extracts all ``<a href>`` links that share the same domain and a
    common path prefix.  Then performs one level of breadth-first expansion
    on the discovered pages until *limit* unique URLs have been collected.

    Parameters
    ----------
    doc_url : str
        The root documentation URL to start crawling from.
    limit : int
        Maximum number of doc pages to return.

    Returns
    -------
    list[str]
        Up to *limit* unique article URLs.
    """
    from bs4 import BeautifulSoup

    parsed = urlparse(doc_url)
    base_domain = parsed.netloc
    # Use the given path as the scope prefix so we stay within this doc tree
    base_path = parsed.path.rstrip("/")

    seen: set[str] = set()
    urls: list[str] = []
    queue: list[str] = [doc_url]

    while queue and len(urls) < limit:
        seed = queue.pop(0)
        if seed in seen:
            continue

        logger.info("Crawling page: %s", seed)
        html = fetch_html(seed)
        if not html:
            seen.add(seed)
            continue

        # The seed page itself is a valid doc page
        if seed not in seen:
            seen.add(seed)
            urls.append(seed)
            if len(urls) >= limit:
                break

        soup = BeautifulSoup(html, "html.parser")
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            full_url = urljoin(seed, href)
            full_url = full_url.split("#")[0].split("?")[0]

            if full_url in seen:
                continue
            if not _is_within_scope(full_url, base_domain, base_path):
                continue

            seen.add(full_url)
            urls.append(full_url)
            queue.append(full_url)
            if len(urls) >= limit:
                break

    logger.info("Discovered %d documentation URLs (limit %d)", len(urls), limit)
    return urls


def _is_within_scope(url: str, base_domain: str, base_path: str) -> bool:
    """Return True if *url* shares the same domain and path prefix."""
    parsed = urlparse(url)
    if parsed.netloc != base_domain:
        return False
    if not parsed.path.startswith(base_path):
        return False
    # Reject non-doc resources (images, downloads, etc.)
    if any(parsed.path.endswith(ext) for ext in (".png", ".jpg", ".svg", ".gif", ".zip", ".tar", ".pdf")):
        return False
    return True
