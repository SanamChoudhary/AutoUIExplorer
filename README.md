## AutoUIExplorer ##

Automated Web-Scraping and UI Traversal with **Adaptive SaaS Onboarding Framework**

Built for the Motorola Solutions

---

## Adaptive SaaS Onboarding Framework

A system that tracks user progression through any web application by:
- Capturing real-time browsing actions
- Building a dynamic knowledge graph of visited pages
- Inferring the user's onboarding stage (Novice → Retained)
- Logging metrics snapshots for analysis

### Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Start the API server:**
   ```bash
   python main.py
   ```

3. **Track a website (in another terminal):**
   ```bash
   python main.py --track https://example.com
   ```

   A browser will open. Navigate the website normally — your actions are tracked in real-time.

4. **Check your state anytime:**
   - API Docs: http://127.0.0.1:8000/docs
   - User State: `GET /user/{userId}/state`
   - Knowledge Graph: `GET /graph`

### Stage Progression (Dynamic Mode)

| Stage      | Pages Visited |
|------------|---------------|
| Novice     | 1-2           |
| Exploring  | 3-5           |
| Activating | 6-10          |
| Proficient | 11-19         |
| Retained   | 20+           |

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/init` | POST | Initialize graph for a URL |
| `/event` | POST | Send a user action event |
| `/user/{userId}/state` | GET | Get user's current state + metrics history |
| `/graph` | GET | View the knowledge graph (nodes & edges) |
| `/graph/stats` | GET | Get graph statistics |
| `/reset` | POST | Clear the knowledge graph |

### Project Structure

```
├── main.py                 # Entry point (API server or browser tracker)
├── requirements.txt        # Python dependencies
├── app/                    # Main application package
│   ├── api.py              # FastAPI endpoints
│   ├── database.py         # SQLite storage layer
│   ├── models.py           # Pydantic data models
│   └── core/               # Core business logic
│       ├── knowledge_graph.py  # NetworkX knowledge graph
│       ├── user_state.py       # User state computation
│       └── metrics_logger.py   # Metrics snapshot logging
├── scripts/                # Standalone scripts
│   ├── browser_tracker.py  # Browser tracking with Playwright
│   └── simulate_mock.py    # Mock simulation for testing
├── config/                 # Configuration files
│   └── stage_rules.json    # Stage transition rules
├── data/                   # Database storage
│   └── onboarding.db       # SQLite database (auto-generated)
└── legacy/                 # Original UI Explorer code
    └── website_Interact.py
```

### Modes of Operation

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
