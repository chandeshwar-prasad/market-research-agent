# Market Research & Trend Analysis Agent

Give it a topic, competitor, or market niche. The agent automatically plans the research, searches the live web, extracts relevant information, synthesizes ranked insights, evaluates the evidence, and produces a cited, confidence-tagged Markdown report within a few minutes.

## What it does

The agent takes a topic, competitor, or niche and autonomously researches it into a ranked, cited insight report — no manual searching or copy-pasting. It plans 3-5 research sub-questions, searches the live web for each, synthesizes findings into ranked insights, **fact-checks its own output** (dropping any insight whose citation doesn't hold up or that's off-topic, and tagging the rest by confidence), and saves a clean Markdown report.

That fact-checking step is the core of this build: in testing, it caught garbled source URLs, an off-topic search result mismatch, and insights padded with weak evidence — all before they reached the final report.

## Tech stack

- **Groq** (Llama 3.3 70B) — planning, synthesis, and evaluation
- **Tavily** — live web search + content extraction
- **Python**, no orchestration framework — a simple sequential pipeline (plan → search → synthesize → evaluate → report)

## Setup

1. Clone/download this project
2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your API keys:
   ```
   TAVILY_API_KEY=your-tavily-key
   GROQ_API_KEY=your-groq-key
   ```
   Get a free Tavily key at tavily.com, a free Groq key at console.groq.com

## Run it

```
python main.py
```
Enter any topic, competitor name, or market niche when prompted. The report saves to `outputs/report_<topic>_<timestamp>.md`.

## Example topics tested

- A product's feature set (e.g. "Notion's AI features")
- A named competitor (e.g. "ClickUp AI features")
- A broad market niche (e.g. "AI-powered note-taking tools market")

## What's next

- Follow-up Q&A against the same research session
- Simple HTML dashboard view instead of raw Markdown
