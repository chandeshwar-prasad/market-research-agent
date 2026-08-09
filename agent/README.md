# Market Research & Trend Analysis Agent

An AI agent that takes a topic, competitor, or niche and autonomously researches it into a ranked, cited insight report — no manual searching or copy-pasting.

## What it does

Give it a topic → it plans 3-5 research sub-questions → searches the live web for each → synthesizes findings into ranked insights → **fact-checks its own output**, dropping any insight whose citation doesn't hold up or that's off-topic, and tagging the rest by confidence → saves a clean Markdown report.

That fact-checking step is the core of this build: in testing, it caught garbled source URLs, an off-topic search result mismatch, and insights padded with weak evidence — all before they reached the final report.

## Tech stack

- **Groq** (Llama 3.3 70B) — planning, synthesis, and evaluation
- **Tavily** — live web search + content extraction
- **Python**, no orchestration framework — a simple sequential pipeline (plan → search → synthesize → evaluate → report)

## Setup

1. Clone/download this project
2. Create a virtual environment and install dependencies: