import os
import json
import time
import hashlib

CACHE_DIR = ".cache"
TTL_STANDARD = 86400  # 24 hours in seconds
TTL_FRESHNESS_SENSITIVE = 3600  # 1 hour in seconds

FRESHNESS_KEYWORDS = {
    "latest", "current", "today", "recent", "this week", "this month",
    "now", "new", "just announced", "breaking", "up to date",
    "what changed", "what's new", "since yesterday", "right now"
}

def _is_freshness_sensitive(topic: str) -> bool:
    cleaned = topic.lower()
    return any(kw in cleaned for kw in FRESHNESS_KEYWORDS)

def _get_cache_key(topic: str) -> str:
    cleaned = topic.strip().lower()
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()[:16]

def get_cached(topic: str, force_fresh: bool = False) -> dict | None:
    if force_fresh:
        return None

    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_key = _get_cache_key(topic)
    cache_path = os.path.join(CACHE_DIR, f"{cache_key}.json")

    if not os.path.exists(cache_path):
        return None

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            entry = json.load(f)
        
        cached_at = entry.get("cached_at")
        if cached_at is None:
            return None

        freshness_sensitive = entry.get("freshness_sensitive", False)
        ttl = TTL_FRESHNESS_SENSITIVE if freshness_sensitive else TTL_STANDARD
        
        if time.time() - cached_at > ttl:
            return None

        return entry.get("data")
    except Exception:
        return None

def set_cached(topic: str, data: dict) -> None:
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        cache_key = _get_cache_key(topic)
        cache_path = os.path.join(CACHE_DIR, f"{cache_key}.json")

        freshness_sensitive = _is_freshness_sensitive(topic)
        entry = {
            "cached_at": time.time(),
            "freshness_sensitive": freshness_sensitive,
            "data": data
        }

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(entry, f, indent=2)
    except Exception as e:
        print(f"Warning: Failed to write to cache for topic '{topic}': {e}")
