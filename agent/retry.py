import requests
import groq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Stop after 3 attempts, exponential backoff starting at 1 second, capped at 8 seconds,
# retrying ONLY on requests.exceptions.ConnectionError, requests.exceptions.Timeout,
# and groq.RateLimitError.
with_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type((
        groq.RateLimitError,
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout
    )),
    reraise=True
)
