# AutoUIExplorer

**Real-time browser navigation tracker with knowledge graph visualization**

Built for the Motorola Solutions

---

## What It Does

Track how users navigate any website by:
- **Real-time logging** of page visits in the terminal
- **Building a knowledge graph** of navigation patterns
- **Calculating comprehension level** based on exploration depth
- **Visualizing the graph** with matplotlib on session end

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

A browser window opens. Navigate freely — your actions are logged in real-time.

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

## Project Structure

```
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
├── scripts/
│   └── browser_tracker.py  # Core tracking logic
└── data/                   # Output (auto-generated)
    ├── knowledge_graph.json
    └── knowledge_graph.png
```

## Dependencies

**1. Dynamic Mode (Browser Tracking)**
Track any website in real-time. The knowledge graph is built dynamically as you browse.
```bash
python main.py --track https://your-app.com
```

**2. Mock Mode (for testing)**
Use a predefined knowledge graph with the `simulate_mock.py` script.
```bash
python scripts/simulate_mock.py
``` 
