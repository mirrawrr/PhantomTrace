"""Unbilled deployment check: login, dashboard assets, deterministic evidence API.

Credentials come only from DEMO_USERNAME/DEMO_PASSWORD environment variables.
This does not call Meta and does not establish live-model readiness.
"""
import argparse
import base64
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler
import re


def smoke(base_url):
    parsed = urlparse(base_url)
    if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {'', '/'}:
        raise ValueError('Use a service origin without embedded credentials or a path.')
    if parsed.scheme != 'https' and not (parsed.scheme == 'http' and parsed.hostname in {'127.0.0.1', 'localhost', '::1'}):
        raise ValueError('Use HTTPS except for a localhost check.')
    username, password = os.environ.get('DEMO_USERNAME', ''), os.environ.get('DEMO_PASSWORD', '')
    if not username or not password:
        raise ValueError('Set DEMO_USERNAME and DEMO_PASSWORD in the terminal environment.')
    base_url = base_url.rstrip('/')
    basic = 'Basic ' + base64.b64encode(f'{username}:{password}'.encode()).decode()

    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, request, fp, code, msg, headers, newurl):
            # Never forward demo credentials to another destination.
            return None

    opener = build_opener(NoRedirect())

    def fetch(path, *, authenticated=False, payload=None):
        headers = {'Authorization': basic} if authenticated else {}
        body = None
        if payload is not None:
            body = json.dumps(payload).encode()
            headers['Content-Type'] = 'application/json'
        request = Request(base_url + path, data=body, headers=headers)
        try:
            with opener.open(request, timeout=90) as response:
                return response.status, {key.lower(): value for key, value in response.headers.items()}, response.read()
        except HTTPError as response:
            return response.code, {key.lower(): value for key, value in response.headers.items()}, response.read()

    status, _, body = fetch('/health')
    if status != 200 or json.loads(body).get('status') != 'healthy':
        raise RuntimeError('Health check failed.')
    if fetch('/')[0] != 401 or fetch('/api/evidence/analyze', payload={'logs': 'bad'})[0] != 401:
        raise RuntimeError('Demo login protection failed.')
    status, headers, body = fetch('/', authenticated=True)
    if status != 200 or b'PhantomTrace' not in body or headers.get('cache-control') != 'no-store':
        raise RuntimeError('Authenticated dashboard check failed.')
    assets = re.findall(rb'(?:src|href)="(/assets/[^"]+)"', body)
    if not assets:
        raise RuntimeError('Dashboard assets are missing.')
    for asset in assets:
        if fetch(asset.decode(), authenticated=True)[0] != 200:
            raise RuntimeError('Dashboard asset check failed.')
    payload = {'logs': 'SMOKE001 | 2026-10-28T02:05:00Z | PERMISSION_CHANGE | user=operator | target=backup | role=administrator'}
    status, _, body = fetch('/api/evidence/analyze', authenticated=True, payload=payload)
    if status != 200 or json.loads(body).get('total_events') != 1:
        raise RuntimeError('Deterministic API check failed.')
    print('PASS: health, demo login, dashboard, assets and deterministic API. No Meta calls made.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url', help='Service origin, e.g. https://your-service.onrender.com')
    args = parser.parse_args()
    try:
        smoke(args.url)
    except (ValueError, RuntimeError, URLError):
        # Avoid printing credential-bearing request objects or remote response bodies.
        parser.exit(1, 'Deployment smoke check failed. Check origin, login, service logs and configuration.\n')


if __name__ == '__main__':
    main()
