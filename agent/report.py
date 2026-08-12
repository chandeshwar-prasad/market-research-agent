import os
import re
from datetime import datetime
from agent.schemas import EvaluationResult, SearchResult, Source

def save_report(topic, evaluation_result: EvaluationResult, results):
    os.makedirs("outputs", exist_ok=True)

    slug = re.sub(r"[^a-zA-Z0-9]+", "-", topic).strip("-").lower()
    slug = slug[:50]

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"outputs/report_{slug}_{timestamp}.md"

    all_urls = []
    for item in results:
        if isinstance(item, SearchResult):
            sources = item.sources
        else:
            sources = item.get("sources", [])
            
        for source in sources:
            if isinstance(source, Source):
                title = source.title
                url = source.url
            else:
                title = source.get("title", "Untitled")
                url = source.get("url", "")
            all_urls.append(f"- [{title}]({url})")

    # Format insights from evaluation_result
    insights_lines = []
    if isinstance(evaluation_result, EvaluationResult):
        for i, ins in enumerate(evaluation_result.kept_insights, 1):
            source_part = f" *(Source: {ins.cited_url})*" if ins.cited_url else ""
            insights_lines.append(f"{i}. {ins.text} **[{ins.confidence}]**{source_part}")
    elif isinstance(evaluation_result, str):
        insights_lines.append(evaluation_result)
    else:
        insights_lines.append(str(evaluation_result))

    evaluated_insights = "\n".join(insights_lines)

    content = f"""# Market Research Report: {topic}

*Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}*

## Insights

{evaluated_insights}

## Sources

{chr(10).join(sorted(set(all_urls)))}
"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    return filename