"""
Documentation Parser for GitHub Adaptive Onboarding Benchmark
==============================================================
Crawls a given GitHub documentation URL, extracts procedural task paths,
and outputs a benchmark JSON file containing the task list.

Usage:
    python doc_parser.py https://docs.github.com/en/repositories --limit 100

Implementation is split across the ``parser/`` sub-package:
    parser/constants.py   - shared constants (verbs, category map)
    parser/browser.py     - Playwright browser lifecycle & page fetching
    parser/discovery.py   - URL discovery via seed-page crawling
    parser/extraction.py  - page parsing, task extraction, confidence scoring
"""

from __future__ import annotations

import json
import os

from parser.browser import init_browser, shutdown_browser
from parser.discovery import discover_urls
from parser.extraction import parse_page, assign_task_ids


def run_parser(
    doc_url: str,
    output_file: str = "github_benchmark.json",
    limit: int = 50,
) -> list[dict]:
    """Main entry point - fetch docs, parse tasks, write benchmark JSON.

    Parameters
    ----------
    doc_url : str
        Root documentation URL to crawl (e.g.
        ``https://docs.github.com/en/repositories``).
    output_file : str
        Filename for the output JSON (written next to this script).
    limit : int
        Maximum number of documentation pages to parse.

    Returns
    -------
    list[dict]
        The list of extracted benchmark tasks.
    """
    banner = "=" * 60
    print(f"\n{banner}")
    print("  GitHub Documentation : Benchmark JSON Parser")
    print(banner)
    print(f"  URL   : {doc_url}")
    print(f"  Limit : {limit}")

    init_browser()

    try:
        # 1. Discover URLs
        print("\n[1/4] Discovering documentation URLs ...")
        urls = discover_urls(doc_url=doc_url, limit=limit)
        print(f"      Found {len(urls)} relevant pages")
        if not urls:
            print("ERROR: No URLs found. Check your network connection.")
            return []

        # 2. Parse each page
        print("\n[2/4] Parsing pages for procedural tasks ...")
        all_tasks: list[dict] = []
        for i, url in enumerate(urls, start=1):
            print(f"      [{i}/{len(urls)}] {url}")
            tasks = parse_page(url)
            if tasks:
                all_tasks.extend(tasks)
                print(f"            -> Extracted {len(tasks)} task(s)")

        if not all_tasks:
            print("\nWARNING: No tasks extracted. The site may have changed HTML structure.")
            _write_output(output_file, [])
            return []

        # 3. Post-process
        print(f"\n[3/4] Post-processing {len(all_tasks)} tasks ...")
        all_tasks = assign_task_ids(all_tasks)

        # 4. Write JSON
        print(f"\n[4/4] Writing output to {output_file} ...")
        _write_output(output_file, all_tasks)

        print(f"\n{banner}")
        print(f"  DONE - {len(all_tasks)} tasks -> {output_file}")
        print(banner)

        return all_tasks

    finally:
        shutdown_browser()


def _write_output(output_file: str, all_tasks: list[dict]) -> None:
    """Write the tasks list directly as the top-level JSON array."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, output_file)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_tasks, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        description="Parse GitHub documentation into an adaptive-onboarding benchmark JSON"
    )
    ap.add_argument("doc_url", type=str,
                    help="Root documentation URL to crawl "
                         "(e.g. https://docs.github.com/en/repositories)")
    ap.add_argument("--limit", type=int, default=50,
                    help="Maximum number of doc pages to parse (default: 50)")
    ap.add_argument("--output", type=str, default="github_benchmark.json",
                    help="Output JSON filename (default: github_benchmark.json)")
    args = ap.parse_args()

    run_parser(doc_url=args.doc_url, output_file=args.output, limit=args.limit)