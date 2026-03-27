# AutoUIExplorer

**Real-time browser navigation tracker with knowledge graph visualization**

---

## What It Does

AutoUIExplorer is a toolkit for studying how users (and AI agents) interact with web UIs. It has three main components:

1. **Navigation Tracker** — Track real-time browsing sessions, build a knowledge graph of navigation patterns, and visualize the result.
2. **Benchmark Generator** — Crawl documentation sites (e.g. GitHub Docs) and automatically extract structured procedural UI tasks into a benchmark JSON.
3. **WorkArena Demo** — Run AI agent benchmarks on ServiceNow enterprise tasks using BrowserGym/WorkArena.

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Track a website
```bash
python main.py --track https://example.com
```

A browser window opens. Navigate freely and your actions are logged in real-time.

### 3. Close the browser
When done, close the browser to see:
- **Session stats** (pages visited, navigations, unique paths)
- **Interactive graph visualization** (matplotlib)

---

## Benchmark Generator

Crawl a documentation URL, extract procedural UI tasks, and output a structured benchmark JSON.

### Install additional dependency
```bash
pip install beautifulsoup4
```

### Run the parser
```bash
python benchmark/doc_parser.py <DOC_URL> [--limit N] [--output FILE]
```

**Example:**
```bash
python benchmark/doc_parser.py https://docs.github.com/en/repositories --limit 20
```

### Pipeline
1. **Discover** — Breadth-first crawl of same-domain, same-path-prefix URLs (up to `--limit`).
2. **Parse** — For each page, extract procedural tasks from headings + ordered lists.
3. **Post-process** — Assign sequential IDs (`GH-001`, `GH-002`, …).
4. **Write** — Output JSON to `--output` (default: `benchmark/github_benchmark.json`).

### Output schema (per task)
| Field | Description |
|-------|-------------|
| `task_id` | Sequential ID (e.g. `GH-001`) |
| `category` | Semantic category inferred from URL (e.g. `repository`, `collaboration`) |
| `user_intent` | What the user wants to accomplish |
| `expected_path` | Ordered steps with `action`, `target`, and `instruction` |
| `onboarding_hint` | Context for first-time users |
| `ground_truth_clicks` | Number of steps |
| `source_url` | Documentation page the task was extracted from |

A pre-generated benchmark is included at `benchmark/github_benchmark.json`.

---

## WorkArena Demo

Demonstrates AI agent evaluation on **ServiceNow** enterprise tasks using the [BrowserGym/WorkArena](https://github.com/ServiceNow/BrowserGym) framework.

### WorkArena L1 overview
- **33 task types** across 6 categories: Lists, Forms, Knowledge Base, Service Catalogs, Menus, Dashboards
- **19,912 unique instances** generated at runtime (random parameter combinations prevent memorization)
- BrowserGym opens two windows: a Chat window (left) and a Browser window (right) controlled by Playwright

### Setup
1. Request access to the `ServiceNow/WorkArena-Instances` gated repo on HuggingFace.
2. Install dependencies:
   ```bash
   pip install huggingface_hub browsergym-workarena
   playwright install
   huggingface-cli login
   ```
3. Run the demo:
   ```bash
   python WorkArena_demo/demo_1.py
   ```

The demo iterates through WorkArena L1 atomic tasks, solves each using the built-in cheat function, and validates the result. Replace the cheat call with a real AI agent to benchmark your own solution.

See `WorkArena_demo/information.txt` for detailed setup instructions and task category descriptions.

---

## Output Files

After a tracker session, find these in the `data/` folder:
- `knowledge_graph.json` — Graph data (nodes & edges)
- `knowledge_graph.png` — Graph visualization image


## Project Structure

```
├── main.py                          # Entry point — CLI args, launches tracker
├── requirements.txt                 # Python dependencies
├── data/                            # Output (auto-generated)
│   ├── knowledge_graph.json         #   Graph data (nodes & edges)
│   └── knowledge_graph.png          #   Graph visualization image
├── user_trace/                      # Core navigation tracking package
│   ├── __init__.py
│   ├── tracker/
│   │   ├── browser.py               #   Orchestrator — launches Chromium, wires events
│   │   └── event_collector.py       #   Filters, deduplicates & records navigations
│   ├── graph/
│   │   ├── knowledge_graph.py       #   Directed graph model (NetworkX) + JSON export
│   │   └── url_utils.py             #   URL normalization & feature-ID helpers
│   ├── analysis/
│   │   └── comprehension.py         #   Comprehension-level scoring (Novice → Expert)
│   └── ui/
│       ├── console.py               #   ANSI color helpers & flush-safe logging
│       └── visualizer.py            #   Matplotlib graph rendering & PNG export
├── benchmark/                       # Documentation → benchmark pipeline
│   ├── doc_parser.py                #   CLI entry point for the crawl/parse pipeline
│   ├── doc_parser_guide.txt         #   Human-readable guide for the parser
│   ├── github_benchmark.json        #   Pre-generated benchmark output
│   └── parser/
│       ├── browser.py               #   Headless Chromium fetcher (expands hidden content)
│       ├── constants.py             #   Action verbs, preamble phrases, category map
│       ├── discovery.py             #   BFS URL discovery within a doc tree
│       └── extraction.py            #   Task extraction from HTML ordered lists
└── WorkArena_demo/                  # BrowserGym/WorkArena agent demo
    ├── demo_1.py                    #   Runs L1 atomic tasks with cheat validation
    └── information.txt              #   Setup guide & L1 task category reference
```

## Dependencies

| Package | Purpose |
|---------|---------|
| [Playwright](https://playwright.dev/python/) | Launches and controls Chromium (headed & headless) |
| [NetworkX](https://networkx.org/) | Directed-graph data structure for the knowledge graph |
| [Matplotlib](https://matplotlib.org/) | Renders graph visualizations and saves PNG exports |
| [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) | HTML parsing for the benchmark doc crawler |
| [browsergym-workarena](https://github.com/ServiceNow/BrowserGym) | WorkArena task environment *(WorkArena demo only)* |
| [huggingface_hub](https://huggingface.co/docs/huggingface_hub/) | Access gated WorkArena instances *(WorkArena demo only)* |
