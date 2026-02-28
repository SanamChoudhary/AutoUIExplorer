# AutoUIExplorer

**Real-time browser navigation tracker with knowledge graph visualization**

---

## What It Does

Track how users navigate any website by:
- **Real-time logging** of page visits in the terminal
- **Building a knowledge graph** of navigation patterns
- **Calculating comprehension level** based on exploration depth
- **Visualizing the graph** with matplotlib on session end

## 2/28/2026

This code is not MVP ready for the full-scale AutoUIExplorer, but represents a core implementation for tracking where a user is traversing in a SaaS application.

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
- Your **comprehension level** (Novice → Expert)
- **Session stats** (pages visited, navigations, unique paths)
- **Interactive graph visualization** (matplotlib)

## Output Files

After a session, find these in the `data/` folder:
- `knowledge_graph.json` — Graph data (nodes & edges)
- `knowledge_graph.png` — Graph visualization image

## Comprehension Levels

| Level      | Criteria |
|------------|----------|
| Novice     | 1-2 pages |
| Exploring  | 3-5 pages |
| Proficient | 6-9 pages, 4+ paths |
| Expert     | 10+ pages, 8+ paths |

NOTE: Comprehension level is currently a placeholder until we establish a formal definition of a users comprehension.

## Project Structure

```
├── main.py                          # Entry point — parses CLI args, launches tracker
├── requirements.txt                 # Python dependencies
├── data/                            # Output (auto-generated)
│   ├── knowledge_graph.json         #   Graph data (nodes & edges)
│   └── knowledge_graph.png          #   Graph visualization image
└── user_trace/                      # Core package
    ├── __init__.py
    ├── tracker/
    │   ├── __init__.py
    │   ├── browser.py               #   Orchestrator — launches Chromium, wires events
    │   └── event_collector.py       #   Filters, deduplicates & records navigations
    ├── graph/
    │   ├── __init__.py
    │   ├── knowledge_graph.py       #   Directed graph model (NetworkX) + JSON export
    │   └── url_utils.py             #   URL normalization & feature-ID helpers
    ├── analysis/
    │   ├── __init__.py
    │   └── comprehension.py         #   Comprehension-level scoring (Novice → Expert)
    └── ui/
        ├── __init__.py
        ├── console.py               #   ANSI color helpers & flush-safe logging
        └── visualizer.py            #   Matplotlib graph rendering & PNG export
```

## Dependencies

| Package | Purpose |
|---------|---------|
| [Playwright](https://playwright.dev/python/) | Launches and controls a real Chromium browser |
| [NetworkX](https://networkx.org/) | Directed-graph data structure for the knowledge graph |
| [Matplotlib](https://matplotlib.org/) | Renders the graph visualization and saves it as PNG |
