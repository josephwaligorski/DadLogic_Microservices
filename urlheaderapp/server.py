from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

def fetch_headers(url, method='HEAD'):
    try:
        if method == 'HEAD':
            response = requests.head(url, allow_redirects=False, timeout=10)
        else:
            response = requests.get(url, allow_redirects=False, stream=True, timeout=10)
        return response, response.status_code
    except requests.RequestException as e:
        return None, str(e)

def get_redirect_location(url):
    response, status = fetch_headers(url, method='HEAD')
    if response is None:
        return None, f"Error fetching initial headers: {status}"

    # If HEAD returns 401/403/405, fall back to GET
    if status in (401, 403, 405):
        response, status = fetch_headers(url, method='GET')
        if response is None:
            return None, f"Error fetching initial headers via GET: {status}"

    # Only treat 3xx as "redirect"
    if 300 <= status < 400 and 'Location' in response.headers:
        location = response.headers['Location']
        if not location.startswith(("http://", "https://")):
            location = requests.compat.urljoin(url, location)
        return location, None

    # Any 200 or 401 or other status means "no redirect"
    return None, None

def get_content_type(url):
    response, status = fetch_headers(url, method='HEAD')
    if response is None:
        return None, f"Error fetching headers for {url}: {status}"

    # If HEAD returns 401/403/405, try GET
    if status in (401, 403, 405):
        response, status = fetch_headers(url, method='GET')
        if response is None:
            return None, f"Error fetching headers via GET for {url}: {status}"

    # At this point, response may be 200 or 401 or any other status.
    content_type = response.headers.get("Content-Type")
    if content_type:
        return content_type, None

    return None, "Content-Type header not found"

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/content-type", methods=["GET"])
def content_type_endpoint():
    target_url = request.args.get("url")
    if not target_url:
        return jsonify({"error": "Missing `url` query parameter"}), 400

    redirected, err = get_redirect_location(target_url)
    if err and redirected is None:
        # A real network/SSL/DNS error
        return jsonify({"error": err}), 502

    final_url = redirected if redirected else target_url
    content_type, err = get_content_type(final_url)
    if err:
        # If even GET failed, return that message
        return jsonify({"error": err}), 502

    return jsonify({"url": final_url, "content_type": content_type})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
