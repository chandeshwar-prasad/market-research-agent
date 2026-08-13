import os
import time
from unittest.mock import patch
import pytest
import agent.cache
from agent.cache import get_cached, set_cached, _is_freshness_sensitive

@pytest.fixture(autouse=True)
def setup_temp_cache(tmp_path, monkeypatch):
    # Dynamically point CACHE_DIR to a temporary folder to prevent workspace pollution
    temp_cache_dir = tmp_path / "temp_cache"
    monkeypatch.setattr(agent.cache, "CACHE_DIR", str(temp_cache_dir))
    return temp_cache_dir

def test_cache_roundtrip():
    topic = "machine learning introduction"
    data = {"summary": "A basic introduction to ML."}
    
    # 1. Initially it should be None
    assert get_cached(topic) is None
    
    # 2. Write to cache
    set_cached(topic, data)
    
    # 3. Read from cache and assert equality
    assert get_cached(topic) == data

def test_freshness_keyword_classification():
    # Topics that should be freshness sensitive
    assert _is_freshness_sensitive("latest AI trends") is True
    assert _is_freshness_sensitive("What is the current state of Nvidia?") is True
    assert _is_freshness_sensitive("breaking news on tech stocks") is True
    
    # Standard topics
    assert _is_freshness_sensitive("history of computers") is False
    assert _is_freshness_sensitive("algebra tutorial") is False

def test_force_fresh_bypass():
    topic = "cloud storage pricing"
    data = {"prices": "$10/TB"}
    
    set_cached(topic, data)
    
    # Retrieve with force_fresh=True should bypass the cache and return None
    assert get_cached(topic, force_fresh=True) is None
    # Normal retrieve should still work
    assert get_cached(topic) == data

def test_ttl_expiry_mock_time():
    topic_fresh = "latest quantum computer specs"
    topic_std = "quantum physics basics"
    data = {"result": "val"}
    
    base_time = 1700000000.0
    
    # 1. Set caches with mock time
    with patch("time.time", return_value=base_time):
        set_cached(topic_fresh, data)
        set_cached(topic_std, data)
        
    # 2. Retrieve after 3590 seconds (under 1 hour) -> both should be returned
    with patch("time.time", return_value=base_time + 3590):
        assert get_cached(topic_fresh) == data
        assert get_cached(topic_std) == data
        
    # 3. Retrieve after 3610 seconds (over 1 hour) -> fresh should expire (return None), std remains
    with patch("time.time", return_value=base_time + 3610):
        assert get_cached(topic_fresh) is None
        assert get_cached(topic_std) == data
        
    # 4. Retrieve after 86410 seconds (over 24 hours) -> std should also expire
    with patch("time.time", return_value=base_time + 86410):
        assert get_cached(topic_std) is None
