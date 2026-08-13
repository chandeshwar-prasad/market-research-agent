# Market Research & Trend Analysis Agent

Give it a topic, competitor, or market niche. The agent plans the research, searches the live web, extracts relevant information, synthesizes insights, evaluates the evidence, and produces a cited, confidence-tagged Markdown report.

---

## Features & Implementation Details

The agent is designed around a single-session pipeline with the following architectural components:

### 1. Content-Grounded Evaluation & Fact-Checking
- **Keyword-Overlap Passage Extraction**: Restricts the evaluator's context to a high-density, keyword-matching passage from the retrieved source text. This avoids blind truncation or high-overhead embeddings, keeping context sizes small and accurate.
- **Verdict Classification**: Insights are evaluated by Groq (`llama-3.3-70b-versatile`) and classified as `Supported`, `Partially supported`, `Unsupported`, `Contradicted`, or `No citation found`.
- **Factual Audit Trail**: Any insight marked as `Unsupported` or `Contradicted` is dropped from the final report. The `evidence_gaps` field lists only the text of these dropped claims (rather than a general analysis of what angles are missing from the research).

### 2. Structured Outputs
All pipeline stages (planning questions, search results, synthesis, evaluation, and reporting) use strict, validated Pydantic models ([agent/schemas.py](file:///d:/AI%20Agents/market-research-agent/agent/schemas.py)) to prevent formatting bugs and guarantee valid JSON structures.

### 3. Source Deduplication
Ensures that duplicate URLs appearing across multiple research sub-questions are only processed and cited once. URL normalization collapses schemes, host casing, trailing slashes, and removes common tracking query parameters (such as `utm_*`, `ref`, and `fbclid`).

### 4. Parallel Search
Executes up to 3 web searches concurrently via a `ThreadPoolExecutor` to speed up live web retrieval, while correctly aligning results to match the original question order.

### 5. Retry with Exponential Backoff
Uses a custom `tenacity` retry policy ([agent/retry.py](file:///d:/AI%20Agents/market-research-agent/agent/retry.py)) applied to all API call sites (Groq completions and Tavily searches). It retries transient connection errors, timeouts, and API rate-limit errors up to 3 times before failing.

### 6. Caching & Freshness Detection
- **Cache-First Lookup**: Repeating the exact same topic within the expiration window returns the cached report path instantly.
- **Freshness-Aware TTL**: The cache dynamically scans topics for time-sensitive words (like "latest", "current", "today"). Freshness-sensitive topics use a **1-hour** Time-To-Live (TTL), whereas standard topics use a **24-hour** TTL.
- **Bypass Control**: A "Force fresh research (skip cache)" checkbox is available in the Streamlit app to bypass the cache and force a live run.

### 7. Conditional Re-Search Loop
If the first research round produces fewer than 4 well-supported insights, the orchestrator ([agent/orchestrator.py](file:///d:/AI%20Agents/market-research-agent/agent/orchestrator.py)) automatically triggers one additional iteration. The second iteration planning query is augmented with metadata from the first round to focus on different angles. The loop is strictly bounded to a maximum of 2 iterations and 10 total web searches.

*(Note: The agent is stateless and has no memory across different sessions or runs).*

---

## Tech Stack

- **Groq** (`llama-3.3-70b-versatile`) — Planning, Synthesis, and Evaluation.
- **Tavily** — Live web search + content extraction.
- **Streamlit** — Web-based user dashboard featuring interactive options and report rendering.
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
- **Command Line**:
  ```bash
  python main.py
  ```
- **Streamlit Dashboard**:
  ```bash
  streamlit run app.py
  ```

---

## Automated Tests

Run the full mocked test suite (26 tests verifying cache TTLs, search parallelism, retry behavior, Pydantic schemas, URL deduplication, and the orchestrator loop):
```bash
venv\Scripts\python -m pytest tests/ -v
```
All API interactions are fully mocked. The test suite runs entirely offline and does not require active API keys.
