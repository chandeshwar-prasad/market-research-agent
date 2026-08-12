import os
import json
from groq import Groq
from dotenv import load_dotenv
from agent.schemas import SearchResult, Source, SynthesisResult, Insight

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def synthesize_insights(topic: str, results: list) -> SynthesisResult:
    context = ""
    for item in results:
        if isinstance(item, SearchResult):
            question = item.question
            sources = item.sources
        else:
            question = item.get("question", "")
            sources = item.get("sources", [])
            
        context += f"\nResearch question: {question}\n"
        for source in sources:
            if isinstance(source, Source):
                title = source.title
                url = source.url
                content = source.content[:500]
            else:
                title = source.get("title", "Untitled")
                url = source.get("url", "")
                content = source.get("content", "")[:500]
            context += f"- Source: {title} ({url})\n  {content}\n"

    prompt = f"""You are a market research analyst. Based on the research below about "{topic}", write a ranked list of the 5-8 most important insights.

Rules:
- Write every insight in your own words, never copy source text directly
- Each insight must cite which source(s) support it, using the source URL
- Rank insights by importance/relevance, most important first
- Be specific and concrete, not generic

Research data:
{context}

You must return your response as a JSON object matching this schema:
{{
  "insights": [
    {{
      "text": "insight description...",
      "cited_url": "source_url"
    }}
  ]
}}
Return ONLY valid JSON, nothing else."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1500,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}]
        )
        data = json.loads(response.choices[0].message.content)
        return SynthesisResult.model_validate(data)
    except Exception as e:
        print(f"Error synthesizing insights: {e}")
        # Keep existing fallback logic, but wrapped in SynthesisResult Pydantic object
        return SynthesisResult(insights=[
            Insight(
                text=f"Error: Unable to synthesize insights due to a failed LLM API call: {e}",
                cited_url=None
            )
        ])
