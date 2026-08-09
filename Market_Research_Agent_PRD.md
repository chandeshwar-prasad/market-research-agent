# PRD: Market Research & Trend Analysis Agent

**Author:** Chandeshwar Prasad
**Status:** Draft v1

---

## 1. Problem Statement

Founders, marketers, and analysts routinely need to answer questions like "what is this competitor doing," "what's trending in this niche," or "how is sentiment shifting" — and today that means hours of manual searching, tab-hopping, and note-stitching. There's no fast, trustworthy way to turn a single topic/competitor/niche into a structured, cited insight report.

## 2. Goal

Build an agent where you:
Give it a topic, competitor, or market niche. The agent automatically plans the research, searches the live web, extracts relevant information, synthesizes ranked insights, evaluates the evidence, and produces a cited, confidence-tagged Markdown report within a few minutes.

## 3. Target User

- Founders/marketers doing competitor or niche research
- Analysts who need a fast first-pass market scan before deeper work
- (For this project) AI Pro community members evaluating the build itself

## 4. Success Criteria

- Given a topic, the agent produces a structured report in under ~3–5 minutes
- Every claim in the report is traceable to a source (no hallucinated stats)
- Report surfaces at least 3 distinct, non-redundant insights per run
- The agent self-flags low-confidence or single-source claims rather than presenting everything with equal certainty

## 5. Scope

### In scope (MVP)
- Single research input: a topic, competitor name, or niche keyword
- Web search + page fetch for source gathering
- Structured extraction: key facts, pricing/positioning signals, sentiment, recent moves
- Synthesis into a ranked insight report with inline source citations
- Basic confidence tagging per insight (high/medium/low based on source count/agreement)
- Export to Markdown (and optionally a simple dashboard view)

### Out of scope (later phases)
- Scheduled/recurring monitoring (e.g., daily competitor alerts)
- Multi-topic batch runs
- Private/paid data source integration (e.g., paywalled industry reports)
- Slack/email delivery automation

## 6. Agent Architecture

**Type:** Single orchestrator agent with tool calls (not a full multi-agent crew — keep MVP lean)

| Component | Role |
|---|---|
| Planner step | Breaks the topic into 3–5 research sub-questions (e.g., pricing, recent news, sentiment, competitors, positioning) |
| Search tool | Runs web searches per sub-question |
| Fetch tool | Pulls full page content for top results |
| Extraction step | Pulls structured facts per source (own words, never verbatim reproduction) |
| Synthesis step | Merges facts across sources into ranked insights, tags confidence, dedupes |
| Evaluation step | Checks: every insight has ≥1 citation; flags any insight with only 1 source as "low confidence"; drops unsupported claims |
| Output step | Renders the final Markdown/HTML report |

This evaluation step is the differentiator — it's what separates a demo from something a hiring manager or community member trusts.

## 7. User Flow

1. User enters a topic/competitor/niche (plain text)
2. Agent shows its research plan (the sub-questions it will investigate) — brief transparency step
3. Agent runs searches + extraction in the background
4. Agent returns a report: **Summary → Ranked Insights (with confidence + citations) → Sources list**
5. User can ask a follow-up question against the same research (optional stretch goal)

## 8. Functional Requirements

- FR1: Accept free-text topic input
- FR2: Generate 3–5 research sub-questions automatically
- FR3: Retrieve and parse content from at least 5–8 sources per run
- FR4: Extract facts in the agent's own words (never verbatim quoting/reproducing source text)
- FR5: Rank insights by relevance/recency, not just source order
- FR6: Tag each insight with a confidence level and cite supporting source(s)
- FR7: Output a single, readable Markdown report

## 9. Non-Functional Requirements

- Reliability: if a source fetch fails, the agent continues with remaining sources rather than crashing
- Transparency: the research plan and source list are always visible, not hidden
- Cost/latency: keep total run under a reasonable token/time budget (define a hard cap, e.g., max 10 search calls per run)

## 10. Tech Stack (proposed)

- **PRD/design:** ChatGPT/Claude
- **Build environment:** Antigravity IDE
- **Orchestration:** simple sequential agent logic first (plan → search → extract → synthesize → evaluate) before reaching for a framework like LangGraph/CrewAI — don't add framework overhead until the sequential version works
- **Search/fetch:** web search API + page fetch tool
- **Output:** Markdown, rendered in a simple UI or exported file

## 11. Build Phases

- **Phase 1 (MVP):** Single-topic input → plan → search → extract → synthesize → Markdown report, with citations
- **Phase 2:** Add confidence tagging + evaluation step (drop/flag unsupported claims)
- **Phase 3:** Follow-up Q&A against the same research session
- **Phase 4 (stretch):** Simple report dashboard (HTML) instead of raw Markdown

## 12. Risks / Open Questions

- Source quality varies — need a lightweight rule for deprioritizing low-quality/SEO content
- Hallucination risk in synthesis step — mitigated by the evaluation step (FR6, confidence tagging)
- Rate limits on search API calls — define the max searches per run early
- Open question: single orchestrator agent vs. splitting into separate "researcher" and "editor" agents — start single-agent for MVP, split only if synthesis quality suffers

## 13. Definition of Done (MVP)

A user can enter any topic and receive, within a few minutes, a cited, confidence-tagged insight report with zero manual research on their part — postable as-is to the AI Pro community as a working demo.
