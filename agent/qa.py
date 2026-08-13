import os
import json
from groq import Groq
from dotenv import load_dotenv
from agent.schemas import QAAnswer, SearchResult, Source
from agent.retry import with_retry

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

@with_retry
def _call_groq_completions(messages, max_tokens=1000, response_format=None):
    return client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=max_tokens,
        response_format=response_format,
        messages=messages
    )

def answer_question(topic: str, question: str, results: list) -> QAAnswer:
    if not results:
        return QAAnswer(
            answer="No research results or source documents are available for this topic to answer your question.",
            citations=[]
        )

    context = ""
    for item in results:
        if isinstance(item, SearchResult):
            sources = item.sources
        elif isinstance(item, dict):
            sources = item.get("sources", [])
        else:
            sources = []

        for source in sources:
            if isinstance(source, Source):
                title = source.title
                url = source.url
                content = source.content
            elif isinstance(source, dict):
                title = source.get("title") or "Untitled"
                url = source.get("url") or ""
                content = source.get("content") or ""
            else:
                continue

            if not content.strip():
                continue

            context += f"\nSource: {title} ({url})\nContent: {content[:1500]}\n"

    if not context.strip():
        return QAAnswer(
            answer="No source text content is available in the research results to answer your question.",
            citations=[]
        )

    prompt = f"""You are a market research assistant. You have conducted research on the topic: "{topic}".
The user has a follow-up question about this topic: "{question}".

Answer the follow-up question using only the research sources provided below.
Rules:
1. Write the answer in your own words.
2. Only make claims that are supported by the provided sources.
3. Include inline source URLs in the answer where appropriate.
4. If the provided sources do not contain the answer, state that the research does not cover this and leave the 'citations' list empty.
5. You must return your response as a JSON object matching this schema:
{{
  "answer": "Your detailed answer to the follow-up question with citations...",
  "citations": ["url1", "url2", ...]
}}
Return ONLY valid JSON, nothing else.

Research Sources:
{context}
"""

    try:
        response = _call_groq_completions(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        
        answer = data.get("answer", "")
        citations = data.get("citations", [])
        if not isinstance(citations, list):
            citations = []
            
        return QAAnswer(answer=answer, citations=citations)
    except Exception as e:
        print(f"Error in answer_question: {e}")
        return QAAnswer(
            answer=f"Error: Unable to generate answer due to an exception: {e}",
            citations=[]
        )
