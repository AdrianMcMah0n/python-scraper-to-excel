"""HTTP layer: one shared session with retries, a polite delay between requests and a clear User-Agent."""
import threading
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USER_AGENT = (
    "python-scraper-to-excel/1.0 "
    "(portfolio demo; +https://github.com/AdrianMcMah0n/python-scraper-to-excel)"
)


class PoliteSession:
    """A requests.Session that retries temporary errors and spaces out requests.

    The delay is shared by all worker threads, so adding workers never makes the
    scraper hit the site faster than one request per `delay` seconds.
    """

    def __init__(self, delay: float = 0.2, timeout: float = 20, retries: int = 4):
        self.delay = delay
        self.timeout = timeout
        self._lock = threading.Lock()
        self._last = 0.0
        self.requests_made = 0

        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT
        retry = Retry(
            total=retries,
            backoff_factor=1.0,  # waits 1 s, 2 s, 4 s ... between attempts
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        adapter = HTTPAdapter(max_retries=retry, pool_maxsize=8)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get(self, url: str) -> str:
        with self._lock:
            wait = self._last + self.delay - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            self.requests_made += 1
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        response.encoding = "utf-8"  # the site is UTF-8; without this the pound sign turns into "Â£"
        return response.text
