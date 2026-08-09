import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def evaluate_insights(topic, insights_text, results):
    all_urls = set()
    for item in results:
        for source in item['sources']:
            all_urls.add(source['url'])

    prompt = f"""You are a fact-checking editor reviewing a market research report about "{topic}".

Below is the list of insights, followed by the actual source URLs that were available from research.

Your job:
1. Check each insight's cited URL actually appears in the available sources list
2. Check each insight is genuinely relevant to the topic "{topic}" — flag anything that seems off-topic or mismatched
3. Rewrite the insights list, keeping only insights that pass both checks. Do NOT drop an insight just because it has only one source — a single credible source is fine, only drop for a failed citation match or genuine irrelevance to the topic
4. For each kept insight, add a confidence tag: [High] if 2+ sources support it, [Medium] if 1 source and clearly relevant, [Low] if the connection to the topic seems weak

Available source URLs:
{chr(10).join(all_urls)}

Insights to review:
{insights_text}

Return ONLY the cleaned, confidence-tagged, numbered list. Do not include any explanation, note, commentary, or summary before or after the list — the list itself is the entire response."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error evaluating insights: {e}")
        return "1. [Low] Error: Unable to evaluate insights due to a failed LLM API call. (Source: N/A)"
