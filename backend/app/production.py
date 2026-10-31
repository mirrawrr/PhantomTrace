"""Single-origin, password-gated hackathon demo entry point.

Run behind HTTPS on a hosting provider. Local development continues to use
app.main:app; the provider key never belongs in the frontend build.
"""
import base64
import binascii
import os
from pathlib import Path
import secrets

from fastapi import FastAPI
from starlette.responses import FileResponse, JSONResponse
from starlette.staticfiles import StaticFiles

from app.main import app as api_app


class DemoAccess:
    def __init__(self, app, username, password):
        self.app = app
        self.username = username.encode('utf-8')
        self.password = password.encode('utf-8')

    def authorized(self, scope):
        header = dict(scope.get('headers', [])).get(b'authorization', b'')
        try:
            scheme, encoded = header.split(b' ', 1)
            if scheme.lower() != b'basic':
                return False
            decoded = base64.b64decode(encoded, validate=True).decode('utf-8')
            username, separator, password = decoded.partition(':')
            user_ok = secrets.compare_digest(username.encode('utf-8'), self.username)
            password_ok = secrets.compare_digest(password.encode('utf-8'), self.password)
            return bool(separator) and user_ok and password_ok
        except (ValueError, UnicodeError, binascii.Error):
            return False

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        async def private_send(message):
            if message['type'] == 'http.response.start':
                headers = [(key, value) for key, value in message.get('headers', [])
                           if key.lower() not in {b'cache-control', b'x-content-type-options',
                                                  b'referrer-policy', b'x-frame-options'}]
                message = {**message, 'headers': headers + [
                    (b'cache-control', b'no-store'),
                    (b'x-content-type-options', b'nosniff'),
                    (b'referrer-policy', b'no-referrer'),
                    (b'x-frame-options', b'DENY'),
                ]}
            await send(message)

        health_probe = scope['path'] == '/health' and scope['method'] in {'GET', 'HEAD'}
        if not health_probe and not self.authorized(scope):
            response = JSONResponse({'detail': 'Demo login required.'}, status_code=401,
                                    headers={'WWW-Authenticate': 'Basic realm="PhantomTrace demo", charset="UTF-8"'})
            await response(scope, receive, private_send)
            return
        await self.app(scope, receive, private_send)


def create_app(static_dir=None):
    username, password = os.getenv('DEMO_USERNAME', ''), os.getenv('DEMO_PASSWORD', '')
    if not username.strip() or ':' in username or any(c in username for c in '\r\n'):
        raise RuntimeError('Set a valid DEMO_USERNAME for the hosted demo.')
    if len(password) < 16 or any(c in password for c in '\r\n'):
        raise RuntimeError('Set DEMO_PASSWORD to at least 16 characters for the hosted demo.')
    if not os.getenv('MODEL_API_KEY', '').strip():
        raise RuntimeError('MODEL_API_KEY is required for the hosted demo.')
    default = Path(__file__).resolve().parents[2] / 'frontend' / 'dist'
    directory = Path(static_dir or os.getenv('PHANTOMTRACE_STATIC_DIR', str(default))).resolve()
    if not (directory / 'index.html').is_file() or not (directory / 'assets').is_dir():
        raise RuntimeError('Built dashboard is missing; run the frontend production build first.')

    app = FastAPI(title='PhantomTrace demo', version='0.5.0',
                  docs_url=None, redoc_url=None, openapi_url=None)

    @app.api_route('/health', methods=['GET', 'HEAD'])
    async def health():
        # Liveness only; does not make a billed model request or verify credentials.
        return {'status': 'healthy'}

    @app.get('/')
    async def dashboard():
        return FileResponse(directory / 'index.html')

    app.mount('/assets', StaticFiles(directory=directory / 'assets'), name='assets')
    app.mount('/', api_app)
    app.add_middleware(DemoAccess, username=username, password=password)
    return app
