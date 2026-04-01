"""
URL normalization and feature-ID extraction utilities.

These pure functions convert raw URLs into normalized forms, feature
identifiers, and human-readable names used throughout the project.
"""

from urllib.parse import urlparse


def normalize_url(url: str) -> str:
    """Normalize URL by removing fragments and trailing slashes."""
    parsed = urlparse(url)
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    return normalized.rstrip("/") or normalized


def is_same_domain(url: str, base_domain: str) -> bool:
    """Check if URL is on the same domain as the base domain."""
    if not base_domain:
        return True
    parsed = urlparse(url)
    return parsed.netloc == base_domain or parsed.netloc.endswith(f".{base_domain}")


def url_to_feature_id(url: str) -> str:
    """Convert URL to a simple feature ID.

    Extracts the last meaningful path segment and normalises it to a
    lowercase, underscore-separated identifier.
    """
    parsed = urlparse(url)
    path = parsed.path.strip("/") or "home"

    # Remove common file extensions
    for ext in [".html", ".htm", ".php", ".asp", ".aspx"]:
        if path.endswith(ext):
            path = path[:-len(ext)]

    # Get the meaningful part of the path (last segment, skip "index")
    parts = [p for p in path.split("/") if p and p != "index"]
    if not parts:
        return "home"

    # Take the last meaningful segment
    feature_id = parts[-1].replace("-", "_").lower()
    return feature_id or "home"


def url_to_area(url: str) -> str:
    """Extract the top-level area / section from a URL path.

    For ``https://example.com/settings/notifications/email`` this
    returns ``"settings"``.  Used by the recommendation engine to
    group pages into logical areas.
    """
    parsed = urlparse(url)
    path = parsed.path.strip("/")

    if not path:
        return "home"

    # Split and drop trivial segments
    parts = [p for p in path.split("/") if p and p.lower() not in ("index",)]

    # Remove file extensions from each part
    cleaned: list[str] = []
    for part in parts:
        for ext in [".html", ".htm", ".php", ".asp", ".aspx"]:
            if part.endswith(ext):
                part = part[: -len(ext)]
        if part:
            cleaned.append(part)

    if not cleaned:
        return "home"

    return cleaned[0].replace("-", "_").lower()


def url_to_name(url: str) -> str:
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
