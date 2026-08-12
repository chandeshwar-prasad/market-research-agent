import os
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed
from tavily import TavilyClient
from dotenv import load_dotenv
from agent.schemas import ResearchQuestions, SearchResult, Source
from agent.retry import with_retry

load_dotenv()

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "ref", "fbclid"}

MAX_CONCURRENT_SEARCHES = 3

def _normalize_url(url: str) -> str:
    try:
        parsed = urlparse(url.strip())
        # Lowercase scheme and netloc (host)
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        # Strip trailing slash from path
        path = parsed.path
        if path.endswith('/') and len(path) > 1:
            path = path[:-1]
        
        # Clean tracking query parameters
        query = parse_qs(parsed.query)
        clean_query = {k: v for k, v in query.items() if k.lower() not in TRACKING_PARAMS}
        
        # Re-encode query
        query_str = urlencode(clean_query, doseq=True)
        
        return urlunparse((scheme, netloc, path, parsed.params, query_str, parsed.fragment))
    except Exception as e:
        print(f"Error normalizing URL '{url}': {e}")
        return url.strip()

def deduplicate_sources(results: list[SearchResult]) -> list[SearchResult]:
    seen_globally = set()
    for result in results:
        deduped_sources = []
        for source in result.sources:
            norm_url = _normalize_url(source.url)
            if norm_url not in seen_globally:
                seen_globally.add(norm_url)
                deduped_sources.append(source)
        result.sources = deduped_sources
    return results

@with_retry
def _execute_tavily_search(query: str, max_results: int = 3):
    return client.search(query=query, max_results=max_results)

def _search_one(question: str) -> SearchResult:
    print(f"Starting search: {question[:60]}...")
    try:
        response = _execute_tavily_search(question, max_results=3)
        raw_sources = response.get("results", [])
    except Exception as e:
        print(f"Error searching for '{question[:60]}': {e}")
        raw_sources = []
        
    sources = []
    for src in raw_sources:
        try:
            sources.append(Source(
                title=src.get("title") or "Untitled",
                url=src.get("url") or "",
                content=src.get("content") or ""
            ))
        except Exception as val_err:
            print(f"Error validating source: {val_err}")
            
    print(f"Completed search: {question[:60]}...")
    return SearchResult(
        question=question,
        sources=sources
    )

def search_questions(questions_input) -> list[SearchResult]:
    # Extract questions list robustly
    if isinstance(questions_input, ResearchQuestions):
        questions = questions_input.questions
    elif isinstance(questions_input, list):
        questions = [q for q in questions_input if isinstance(q, str)]
    elif isinstance(questions_input, str):
        # Fallback parsing string
        questions = []
        for line in questions_input.split("\n"):
            line = line.strip()
            if line and line[0].isdigit():
                try:
                    question = line.split(".", 1)[1].strip()
                    questions.append(question)
                except IndexError:
                    pass
            elif line:
                questions.append(line)
    else:
        questions = []

    results = [None] * len(questions)
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_SEARCHES) as executor:
        future_to_idx = {executor.submit(_search_one, question): i for i, question in enumerate(questions)}
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as exc:
                print(f"Search future generated an exception: {exc}")
                results[idx] = SearchResult(question=questions[idx], sources=[])

    return deduplicate_sources(results)