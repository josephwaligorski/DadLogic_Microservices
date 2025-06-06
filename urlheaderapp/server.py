from flask import Flask, request, jsonify
import requests

app = Flask(__name__)


def fetch_headers(url, method='HEAD'):
    try:
        if method == 'HEAD':
            response = requests.head(url, allow_redirects=False)
        else:
            response = requests.get(url, allow_redirects=False, stream=True)
        status = response.status_code
        return response, status
    except requests.RequestException as e:
        return None, None


def get_redirect_location(url):
    response, status = fetch_headers(url, method='HEAD')
    if not response:
        return None, f"Error fetching initial headers: failed request"
    if status in (401, 403, 405):
        response, status = fetch_headers(url, method='GET')
        if not response:
            return None, f"Error fetching initial headers via GET: failed request"
    if not (200 <= status < 400):
        return None, f"Unexpected status {status} for initial URL"

    if 'Location' in response.headers:
        location = response.headers['Location']
        if not location.startswith(('http://', 'https://')):
            location = requests.compat.urljoin(url, location)
        return location, None
    return None, None


def get_content_type(url):
    response, status = fetch_headers(url, method='HEAD')
    if not response:
        return None, f"Error fetching headers for {url}: failed request"
    if status in (401, 403, 405):
        response, status = fetch_headers(url, method='GET')
        if not response:
            return None, f"Error fetching headers via GET for {url}: failed request"
    if not (200 <= status < 400):
        return None, f"Unexpected status {status} for {url}"

    content_type = response.headers.get('Content-Type')
    if content_type:
        return content_type, None
    return None, "Content-Type header not found"


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


@app.route('/content-type', methods=['GET'])
def content_type_endpoint():
    target_url = request.args.get('url')
    if not target_url:
        return jsonify({'error': 'Missing `url` query parameter'}), 400

    redirected, err = get_redirect_location(target_url)
    if err:
        return jsonify({'error': err}), 502

    final_url = redirected if redirected else target_url
    content_type, err = get_content_type(final_url)
    if err:
        return jsonify({'error': err}), 502

    return jsonify({'url': final_url, 'content_type': content_type})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)