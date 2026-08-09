import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def synthesize_insights(topic, results):
    context = ""
    for item in results:
        context += f"\nResearch question: {item['question']}\n"
        for source in item['sources']:
            content = source.get("content", "")[:500]
            context += f"- Source: {source['title']} ({source['url']})\n  {content}\n"

    prompt = f"""You are a market research analyst. Based on the research below about "{topic}", write a ranked list of the 5-8 most important insights.

Rules:
- Write every insight in your own words, never copy source text directly
- Each insight must cite which source(s) support it, using the source URL
- Rank insights by importance/relevance, most important first
- Be specific and concrete, not generic

Research data:
{context}

Return the insights as a numbered list, each with a one-line citation at the end like: (Source: url)"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error synthesizing insights: {e}")
        return "1. Error: Unable to synthesize insights due to a failed LLM API call. (Source: N/A)"
