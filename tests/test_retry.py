from unittest.mock import Mock
import pytest
import requests
from agent.retry import with_retry

def test_retry_on_connection_error():
    mock_func = Mock(side_effect=[requests.exceptions.ConnectionError("Connection lost"), "success"])
    
    decorated = with_retry(mock_func)
    result = decorated()
    
    assert result == "success"
    assert mock_func.call_count == 2

def test_no_retry_on_value_error():
    mock_func = Mock(side_effect=ValueError("Plain value error"))
    
    decorated = with_retry(mock_func)
    
    with pytest.raises(ValueError, match="Plain value error"):
        decorated()
        
    assert mock_func.call_count == 1
