import time
import requests
from checker.utils import normalize_url


def fetch_html(url: str, timeout: int = 15) -> tuple[str, str, float]:
    normalized_url = normalize_url(url)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }

    start = time.perf_counter()
    response = requests.get(normalized_url, headers=headers, timeout=timeout)
    end = time.perf_counter()

    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")
    if "text/html" not in content_type.lower():
        raise ValueError(
            f"The URL did not return an HTML page. Content-Type received: {content_type}"
        )

    return response.text, response.url, round(end - start, 3)