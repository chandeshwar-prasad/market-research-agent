# Market Research & Trend Analysis Agent

Give it a topic, competitor, or market niche. The agent plans the research, searches the live web, extracts relevant information, synthesizes insights, evaluates the evidence, produces a cited, confidence-tagged Markdown report, and lets you ask follow-up questions against the same research session.

---

## Features & Implementation Details

The agent is designed around a single-session pipeline with the following architectural components:

### 1. Content-Grounded Evaluation & Fact-Checking
- **Keyword-Overlap Passage Extraction**: Restricts the evaluator's context to a high-density, keyword-matching passage from the retrieved source text. This avoids blind truncation or high-overhead embeddings, keeping context sizes small and accurate.
- **Verdict Classification**: Insights are evaluated by Groq (`llama-3.3-70b-versatile`) and classified as `Supported`, `Partially supported`, `Unsupported`, `Contradicted`, or `No citation found`.
- **Factual Audit Trail**: Any insight marked as `Unsupported` or `Contradicted` is dropped from the final report. The `evidence_gaps` field lists only the text of these dropped claims (rather than a general analysis of what angles are missing from the research).

### 2. Structured Outputs
All pipeline stages (planning questions, search results, synthesis, evaluation, reporting, and Q&A) use strict, validated Pydantic models ([agent/schemas.py](agent/schemas.py)) to prevent formatting bugs and guarantee valid JSON structures.

### 3. Source Deduplication
Ensures that duplicate URLs appearing across multiple research sub-questions are only processed and cited once. URL normalization collapses schemes, host casing, trailing slashes, and removes common tracking query parameters (such as `utm_*`, `ref`, and `fbclid`).

### 4. Parallel Search
Executes up to 3 web searches concurrently via a `ThreadPoolExecutor` to speed up live web retrieval, while correctly aligning results to match the original question order.

### 5. Retry with Exponential Backoff
Uses a custom `tenacity` retry policy ([agent/retry.py](agent/retry.py)) applied to all API call sites (Groq completions and Tavily searches). It retries transient connection errors, timeouts, and API rate-limit errors up to 3 times before failing.

### 6. Caching & Freshness Detection
- **Cache-First Lookup**: Repeating the exact same topic within the expiration window returns the cached report path instantly.
- **Freshness-Aware TTL**: The cache dynamically scans topics for time-sensitive words (like "latest", "current", "today"). Freshness-sensitive topics use a **1-hour** Time-To-Live (TTL), whereas standard topics use a **24-hour** TTL.
- **Bypass Control**: A "Force fresh research (skip cache)" checkbox is available in the Streamlit app to bypass the cache and force a live run.

### 7. Conditional Re-Search Loop
If the first research round produces fewer than 4 well-supported insights, the orchestrator ([agent/orchestrator.py](agent/orchestrator.py)) automatically triggers one additional iteration. The second iteration planning query is augmented with metadata from the first round to focus on different angles. The loop is strictly bounded to a maximum of 2 iterations and 10 total web searches.

### 8. Follow-up Q&A (Phase 3)
After a report is generated, you can ask follow-up questions grounded in the same research session:
- **Source-Grounded Answers**: The Q&A engine ([agent/qa.py](agent/qa.py)) constructs answers using only the retrieved source documents — no hallucinated facts.
- **Inline Citations**: Every answer includes the supporting source URLs.
- **Available in both interfaces**: The CLI loops interactively, and the Streamlit dashboard maintains a full conversation history per session.

*(Note: The agent is stateless and has no memory across different sessions or runs. Follow-up Q&A is available only within the same session.)*

---

## Agent Architecture

```
User Input
    │
    ▼
Planner (Groq LLM)
  └─ Generates 3–5 research sub-questions
    │
    ▼
Search (Tavily — parallel, deduplicated)
  └─ Retrieves source content per sub-question
    │
    ▼
Synthesizer (Groq LLM)
  └─ Ranks and merges findings into insights with citations
    │
    ▼
Evaluator (Groq LLM — per-insight fact-checking)
  └─ Drops unsupported claims, tags confidence levels
    │
    ├─ [< 4 insights] ──► Re-Search Loop (max 2 iterations, 10 searches)
    │
    ▼
Report Writer
  └─ Saves cited Markdown report to outputs/
    │
    ▼
Follow-up Q&A (Groq LLM — grounded to session sources)
  └─ Answers questions using retrieved source content only
```

---

## Tech Stack

- **Groq** (`llama-3.3-70b-versatile`) — Planning, Synthesis, Evaluation, and Q&A.
- **Tavily** — Live web search + content extraction.
- **Streamlit** — Web-based user dashboard featuring interactive options, report rendering, and stateful Q&A chat.
- **Pydantic** — Structured output validation at every pipeline stage.
- **Tenacity** — Exponential backoff retry for all API calls.
- **Python / Pytest** — Offline test suite using mocked API responses.

---

## Setup & Run

### 1. Installation
Create a virtual environment and install dependencies:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Setup
Create a `.env` file with your API keys:
```env
TAVILY_API_KEY=your-tavily-key
GROQ_API_KEY=your-groq-key
```

### 3. Running the Agent
- **Command Line** (with interactive follow-up Q&A):
  ```bash
  python main.py
  ```
- **Streamlit Dashboard** (with stateful Q&A chat):
  ```bash
  streamlit run app.py
  ```

---

## Automated Tests

Run the full mocked test suite (30 tests verifying cache TTLs, search parallelism, retry behavior, Pydantic schemas, URL deduplication, orchestrator loop, and Q&A engine):
```bash
venv\Scripts\python -m pytest tests/ -v
```
All API interactions are fully mocked. The test suite runs entirely offline and does not require active API keys.

---

## Build Phases Completed

| Phase | Description | Status |
|---|---|---|
| Phase 1 | Core pipeline: plan → search → synthesize → Markdown report | ✅ Done |
| Phase 2 | Confidence tagging, fact-checking evaluation step, re-search loop | ✅ Done |
| Phase 3 | Follow-up Q&A grounded to session research sources | ✅ Done |
| Phase 4 | Interactive Streamlit dashboard with premium UI | ✅ Done |
