import os
import re
import json
from groq import Groq
from agent.schemas import (
    EvaluationResult,
    EvaluatedInsight,
    SynthesisResult,
    SearchResult,
    Source
)
from agent.retry import with_retry


client = Groq(api_key=os.getenv("GROQ_API_KEY"))

@with_retry
def _call_groq_completions(messages, max_tokens=150, response_format=None):
    return client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=max_tokens,
        response_format=response_format,
        messages=messages
    )

STOPWORDS = {"the", "a", "an", "is", "are", "was", "were", "of", "to", "in", "on",
             "for", "and", "or", "with", "that", "this", "it", "as", "by", "at", "be"}


def _build_source_lookup(results):
    lookup = {}
    for item in results:
        if isinstance(item, SearchResult):
            sources = item.sources
        else:
            sources = item.get("sources", [])
            
        for source in sources:
            if isinstance(source, Source):
                url = source.url
                content = source.content
            else:
                url = source.get("url")
                content = source.get("content", "")
            if url:
                lookup[url] = content
    return lookup

def _extract_citations(insights_text):
    records = []
    pattern = r"^\d+\.\s*(.+?)\s*\(Source:\s*(\S+?)\)[\s\.]*$"
    for line in insights_text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        match = re.match(pattern, line)
        if match:
            records.append({"text": match.group(1), "cited_url": match.group(2)})
        elif line[0].isdigit():
            text = re.sub(r"^\d+\.\s*", "", line)
            records.append({"text": text, "cited_url": None})
    return records

def _tokenize(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}

def _chunk_content(content, chunk_size=400, overlap=100):
    chunks = []
    start = 0
    while start < len(content):
        chunks.append(content[start:start + chunk_size])
        start += chunk_size - overlap
    return chunks

def _extract_relevant_passage(content, claim_text, max_chars=1500):
    if len(content) <= max_chars:
        return content

    claim_words = _tokenize(claim_text)
    if not claim_words:
        return content[:max_chars]

    chunks = _chunk_content(content)
    scored = [(len(claim_words & _tokenize(chunk)), i, chunk) for i, chunk in enumerate(chunks)]
    scored.sort(key=lambda x: (-x[0], x[1]))

    selected, total_len = [], 0
    for score, idx, chunk in scored:
        if score == 0 or total_len >= max_chars:
            break
        selected.append((idx, chunk))
        total_len += len(chunk)

    if not selected:
        return content[:max_chars]

    selected.sort(key=lambda x: x[0])
    return "\n[...]\n".join(chunk for _, chunk in selected)

def _classify_one(topic, insight_text, url, full_content) -> EvaluatedInsight:
    if not url or not full_content:
        return EvaluatedInsight(
            text=insight_text,
            cited_url=url,
            verdict="No citation found",
            decision="REMOVE",
            confidence="Low"
        )

    source_content = _extract_relevant_passage(full_content, insight_text)

    try:
        print("\n" + "=" * 80)
        print("DEBUG — EXTRACTED PASSAGE")
        print("Insight:", insight_text)
        print("Source:", url)
        print("-" * 80)
        print(source_content)
        print("=" * 80)
    except Exception:
        # Prevent console encoding issues on Windows from crashing evaluation
        pass

    prompt = f"""You are a fact-checking editor. Below is ONE insight and the source text it cites.

Topic: {topic}
Insight: {insight_text}
Cited source ({url}):
{source_content}

Classify this insight as exactly one of: Supported, Partially supported, Unsupported, Contradicted.
Then decide: KEEP (for Supported), KEEP WITH DOWNGRADE (for Partially supported), or REMOVE (for Unsupported/Contradicted).
Finally, decide confidence: High, Medium, Low.

You must return your response as a JSON object matching this schema:
{{
  "verdict": "Supported" | "Partially supported" | "Unsupported" | "Contradicted",
  "decision": "KEEP" | "KEEP WITH DOWNGRADE" | "REMOVE",
  "confidence": "High" | "Medium" | "Low"
}}
Return ONLY valid JSON, nothing else."""

    try:
        response = _call_groq_completions(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        
        verdict = data.get("verdict", "Unsupported")
        if verdict not in ["Supported", "Partially supported", "Unsupported", "Contradicted"]:
            verdict = "Unsupported"
            
        decision = data.get("decision", "REMOVE")
        if decision not in ["KEEP", "KEEP WITH DOWNGRADE", "REMOVE"]:
            decision = "REMOVE"
            
        confidence = data.get("confidence", "Low")
        if confidence not in ["High", "Medium", "Low"]:
            confidence = "Low"

        return EvaluatedInsight(
            text=insight_text,
            cited_url=url,
            verdict=verdict,
            decision=decision,
            confidence=confidence
        )
    except Exception as e:
        print(f"Evaluation call failed: {e}")
        return EvaluatedInsight(
            text=insight_text,
            cited_url=url,
            verdict="Unsupported",
            decision="REMOVE",
            confidence="Low"
        )

def evaluate_insights(topic, insights_input, results) -> EvaluationResult:
    try:
        source_lookup = _build_source_lookup(results)
        
        citations = []
        if isinstance(insights_input, SynthesisResult):
            for insight in insights_input.insights:
                citations.append({
                    "text": insight.text,
                    "cited_url": insight.cited_url
                })
        elif isinstance(insights_input, str):
            citations = _extract_citations(insights_input)
        
        if not citations:
            if isinstance(insights_input, str):
                kept = []
                for line in insights_input.strip().split("\n"):
                    if line.strip():
                        kept.append(EvaluatedInsight(
                            text=line.strip(),
                            cited_url=None,
                            verdict="Supported",
                            decision="KEEP",
                            confidence="Medium"
                        ))
                return EvaluationResult(kept_insights=kept, evidence_gaps=[])
            return EvaluationResult(kept_insights=[], evidence_gaps=[])

        kept_insights = []
        evidence_gaps = []
        for record in citations:
            url = record["cited_url"]
            content = source_lookup.get(url)
            evaluated_insight = _classify_one(topic, record["text"], url, content)

            if evaluated_insight.decision == "REMOVE":
                evidence_gaps.append(
                    f"Claim lack of evidence or contradiction: '{record['text']}' (Source: {url or 'No citation'})"
                )
                continue
                
            kept_insights.append(evaluated_insight)
            
        return EvaluationResult(kept_insights=kept_insights, evidence_gaps=evidence_gaps)
        
    except Exception as e:
        print(f"Error in evaluate_insights: {e}")
        return EvaluationResult(kept_insights=[], evidence_gaps=[f"Evaluation failed: {e}"])
