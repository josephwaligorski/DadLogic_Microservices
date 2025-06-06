import sys
import requests


def fetch_headers(url, method='HEAD'):
    """
    Attempt to fetch headers using the specified HTTP method (HEAD or GET).
    If HEAD is not allowed (401, 403, or 405), fall back to GET (stream=False).
    """
    try:
        if method == 'HEAD':
            response = requests.head(url, allow_redirects=False)
        else:
            # Use GET but do not download the body
            response = requests.get(url, allow_redirects=False, stream=True)
        status = response.status_code
        return response, status
    except requests.RequestException as e:
        print(f"Error during {method} request to {url}: {e}")
        return None, None


def get_redirect_location(url):
    # First attempt: HEAD request
    response, status = fetch_headers(url, method='HEAD')
    if response is None:
        sys.exit(1)
    # If unauthorized or method not allowed, try GET
    if status in (401, 403, 405):
        print(f"HEAD returned status {status}, retrying with GET...")
        response, status = fetch_headers(url, method='GET')
        if response is None:
            sys.exit(1)
    # Check for successful status codes (2xx or 3xx)
    if not (200 <= status < 400):
        print(f"Unexpected status {status} when fetching headers from initial URL.")
        sys.exit(1)

    # Check for 'Location' header
    if 'Location' in response.headers:
        location = response.headers['Location']
        # Build absolute URL if relative
        if not location.startswith(('http://', 'https://')):
            location = requests.compat.urljoin(url, location)
        print(f"Redirected URL: {location}")
        return location
    else:
        return None


def get_content_type(url):
    # First attempt: HEAD request (allow redirects)
    response, status = fetch_headers(url, method='HEAD')
    if response is None:
        sys.exit(1)
    # If HEAD returns 401/403/405, retry with GET
    if status in (401, 403, 405):
        print(f"HEAD returned status {status} for {url}, retrying with GET...")
        response, status = fetch_headers(url, method='GET')
        if response is None:
            sys.exit(1)
    # Check for successful status codes
    if not (200 <= status < 400):
        print(f"Unexpected status {status} when fetching Content-Type from {url}.")
        sys.exit(1)

    content_type = response.headers.get('Content-Type')
    if content_type:
        print(f"Content-Type: {content_type}")
    else:
        print("Content-Type header not found.")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python app.py <url>")
        sys.exit(1)

    initial_url = sys.argv[1]
    redirected_url = get_redirect_location(initial_url)
    if redirected_url:
        get_content_type(redirected_url)
    else:
        print("No redirect found. Fetching Content-Type from initial URL...")
        get_content_type(initial_url)