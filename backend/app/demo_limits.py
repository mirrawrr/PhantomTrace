"""Fail-closed SQLite reservations for the hosted demo's billed endpoints.

Counts attempts, including failed requests. No evidence or credentials stored.
Use a persistent disk for limits to survive Render restarts/redeploys.
"""
from contextlib import closing
import os
import sqlite3
import tempfile
import time

from starlette.responses import JSONResponse


class DemoLimits:
    def __init__(self, app, path, total=30, hourly=6):
        self.app, self.path = app, path
        self.total, self.hourly = total, hourly
        if total < 1 or hourly < 1:
            raise RuntimeError('Demo request limits must be positive.')
        with closing(sqlite3.connect(path)) as db:
            db.execute('CREATE TABLE IF NOT EXISTS attempts (at REAL NOT NULL)')

    def reserve(self, now=None):
        now = time.time() if now is None else now
        with closing(sqlite3.connect(self.path, timeout=5)) as db:
            db.execute('BEGIN IMMEDIATE')
            total = db.execute('SELECT COUNT(*) FROM attempts').fetchone()[0]
            recent = db.execute('SELECT COUNT(*) FROM attempts WHERE at > ?', (now - 3600,)).fetchone()[0]
            if total >= self.total:
                return 'Live demo allowance exhausted. Recorded replay remains available.'
            if recent >= self.hourly:
                return 'Live demo hourly limit reached. Try the recorded replay or return later.'
            db.execute('INSERT INTO attempts VALUES (?)', (now,))
            db.commit()
        return None

    async def __call__(self, scope, receive, send):
        path = scope.get('path', '').rstrip('/')
        billed = (path == '/api/investigate' or path.startswith('/api/investigate/')
                  or path == '/api/testimony/transcribe')
        if scope['type'] == 'http' and scope['method'] == 'POST' and billed:
            # Clients cannot use chunked input to bypass the size check.
            body = bytearray()
            maximum = 3_000_000 if path == '/api/testimony/transcribe' else 100_000
            while True:
                message = await receive()
                if message['type'] == 'http.disconnect':
                    return
                body.extend(message.get('body', b''))
                if len(body) > maximum:
                    await JSONResponse({'detail': 'Demo upload too large.'}, status_code=413)(scope, receive, send)
                    return
                if not message.get('more_body', False):
                    break
            try:
                error = self.reserve()
            except sqlite3.Error:
                error = 'Live demo usage control unavailable. Try the recorded replay.'
            if error:
                await JSONResponse({'detail': error}, status_code=429,
                                   headers={'Retry-After': '3600'})(scope, receive, send)
                return
            delivered = False
            async def buffered_receive():
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {'type': 'http.request', 'body': bytes(body), 'more_body': False}
                # Streaming responses must still be able to observe disconnects.
                return await receive()
            await self.app(scope, buffered_receive, send)
            return
        await self.app(scope, receive, send)


def configured_limits():
    try:
        return dict(path=os.getenv('DEMO_USAGE_DB', os.path.join(tempfile.gettempdir(), 'phantomtrace-usage.sqlite3')),
                    total=int(os.getenv('DEMO_MAX_REQUESTS', '30')),
                    hourly=int(os.getenv('DEMO_HOURLY_REQUESTS', '6')))
    except ValueError as exc:
        raise RuntimeError('Demo request limits must be integers.') from exc
