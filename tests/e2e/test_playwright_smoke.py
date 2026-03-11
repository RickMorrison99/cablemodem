import os


def test_homepage_loads(page):
    """Basic smoke test: page.goto should return a response with HTTP 200."""
    base_url = os.environ.get("BASE_URL", "http://app:8765")
    response = page.goto(base_url, wait_until="networkidle")
    assert response is not None and response.status == 200
