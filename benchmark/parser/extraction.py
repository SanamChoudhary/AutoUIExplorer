"""
Page parsing and task extraction from documentation HTML.
"""

from __future__ import annotations

import re
import logging
from urllib.parse import urlparse

from .browser import fetch_html
from .constants import (
    CORE_ACTION_VERBS,
    ALL_ACTION_VERBS,
    CATEGORY_MAP,
)

logger = logging.getLogger(__name__)


def parse_page(url: str) -> list[dict] | None:
    """Parse a single documentation page and return a list of extracted tasks.

    Fetches the page via Playwright, then feeds the HTML into BeautifulSoup
    for structured extraction.
    """
    from bs4 import BeautifulSoup

    html = fetch_html(url)
    if not html:
        return None

    try:
        soup = BeautifulSoup(html, "html.parser")

        title_tag = soup.find("h1")
        if not title_tag:
            logger.debug("No <h1> on %s", url)
            return None
        title = title_tag.get_text(strip=True)

        content = (
            soup.find("article")
            or soup.find("main")
            or soup.find("div", class_=re.compile(r"article|content|markdown", re.I))
            or soup.body
        )
        if not content:
            logger.debug("No content container on %s", url)
            return None

        category = _infer_category(url)
        tasks = []
        seen_ol_ids: set[int] = set()

        # Strategy 1: headings followed by ordered lists
        for heading in content.find_all(["h2", "h3"]):
            section_title = heading.get_text(strip=True)
            ol = _find_next_ol(heading)
            if ol is None:
                continue
            ol_id = id(ol)
            if ol_id in seen_ol_ids:
                continue
            seen_ol_ids.add(ol_id)

            task = _extract_task_from_ol(
                ol, title, section_title, url, category, is_ordered=True,
            )
            if task:
                tasks.append(task)

        # Strategy 2: standalone <ol> elements not yet captured
        for ol in content.find_all("ol"):
            ol_id = id(ol)
            if ol_id in seen_ol_ids:
                continue
            seen_ol_ids.add(ol_id)
            task = _extract_task_from_ol(
                ol, title, "General Steps", url, category, is_ordered=True,
            )
            if task:
                tasks.append(task)

        return tasks if tasks else None

    except Exception as e:
        logger.error("Error parsing %s: %s", url, e)
        return None


def _find_next_ol(heading):
    """Walk siblings until we hit the next <ol> or section heading."""
    for sibling in heading.find_next_siblings():
        if sibling.name == "ol":
            return sibling
        if sibling.name in ("h1", "h2", "h3"):
            return None
        if sibling.name in ("div", "section", "article"):
            nested = sibling.find("ol")
            if nested:
                return nested
    return None


def _extract_task_from_ol(ol, page_title, section_title, url, category, is_ordered=True):
    """Convert an ``<ol>`` element into a benchmark task dict (or None)."""
    steps = []
    step_num = 0

    for li in ol.find_all("li", recursive=False):
        text = li.get_text(separator=" ", strip=True)
        if not text or len(text) < 5:
            continue
        if not _is_procedural_step(text):
            continue

        step_num += 1
        action, target = _extract_action_and_target(li, text)
        steps.append({
            "step": step_num,
            "action": action,
            "target": target,
            "full_instruction": text,
        })

    if len(steps) < 2:
        return None

    user_intent = page_title
    if section_title and section_title != "General Steps":
        user_intent = f"{page_title} - {section_title}"

    return {
        "task_id": None,
        "category": category,
        "user_intent": user_intent,
        "expected_path": steps,
        "onboarding_hint": steps[0]["full_instruction"] if steps else "",
        "ground_truth_clicks": len(steps),
        "source": "documentation",
        "source_url": url,
    }


def _is_procedural_step(text: str) -> bool:
    """Return True if *text* looks like a UI-action instruction."""
    lower = text.lower().strip()

    if any(lower.startswith(v) for v in ALL_ACTION_VERBS):
        return True

    snippet = lower[:80]
    return any(f" {v} " in snippet for v in CORE_ACTION_VERBS)


def _extract_action_and_target(li_tag, step_text: str) -> tuple[str, str]:
    """Return ``(action, ui_target)`` extracted from a ``<li>`` element."""
    lower = step_text.lower().strip()

    action = "interact"
    for verb in CORE_ACTION_VERBS:
        if lower.startswith(verb) or f" {verb} " in lower[:60]:
            action = verb.replace(" ", "_")
            break

    action = {
        "go_to": "navigate", "tap": "click", "press": "click",
        "type": "fill", "enter": "fill", "choose": "select",
        "check": "select", "uncheck": "deselect",
    }.get(action, action)

    for tag_name in (["strong", "b"], ["code"], ["em"]):
        tags = li_tag.find_all(tag_name)
        if tags:
            return action, tags[0].get_text(strip=True)

    quoted = re.findall(r'"([^"]+)"', step_text)
    if quoted:
        return action, quoted[0]

    return action, step_text[:60].strip()


def _infer_category(url: str) -> str:
    """Map a docs URL to a task category using path segments.

    Uses ``CATEGORY_MAP`` for known GitHub docs sections but falls back
    to a cleaned-up version of the first meaningful path segment so that
    arbitrary documentation sites still get a useful category.
    """
    parts = urlparse(url).path.strip("/").split("/")
    for part in parts:
        if part in CATEGORY_MAP:
            return CATEGORY_MAP[part]
    # Fallback: use the first path segment that isn't a language code (e.g. "en")
    for part in parts:
        if len(part) > 2:
            return part.replace("-", "_")
    return "general"


def assign_task_ids(all_tasks: list[dict]) -> list[dict]:
    """Assign sequential ``GH-001`` … ``GH-NNN`` identifiers."""
    for i, task in enumerate(all_tasks, start=1):
        task["task_id"] = f"GH-{str(i).zfill(3)}"
    return all_tasks
