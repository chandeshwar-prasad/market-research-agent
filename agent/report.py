import os
import re
from datetime import datetime

def save_report(topic, evaluated_insights, results):
    os.makedirs("outputs", exist_ok=True)

    slug = re.sub(r"[^a-zA-Z0-9]+", "-", topic).strip("-").lower()
    slug = slug[:50]

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"outputs/report_{slug}_{timestamp}.md"

    all_urls = []
    for item in results:
        for source in item['sources']:
            all_urls.append(f"- [{source['title']}]({source['url']})")

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