import asyncio
import base64
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from starlette.responses import JSONResponse
from app.production import DemoAccess, create_app


TEST_ENV={'DEMO_USERNAME':'test-judge','DEMO_PASSWORD':'unit-test-password-not-live',
          'MODEL_API_KEY':'unit-test-model-key-not-live'}


class TestDemoAccess(unittest.TestCase):
    def invoke(self, path='/', method='GET', authorization=None):
        messages=[]
        calls=[]
        async def downstream(scope, receive, send):
            calls.append(scope['path'])
            await JSONResponse({'ok':True})(scope,receive,send)
        async def receive():
            return {'type':'http.request','body':b'','more_body':False}
        async def send(message):
            messages.append(message)
        app=DemoAccess(downstream,'test-judge','unit-test-password-not-live')
        headers=[] if authorization is None else [(b'authorization',authorization)]
        scope={'type':'http','method':method,'path':path,'headers':headers}
        asyncio.run(app(scope,receive,send))
        return messages,calls

    def test_auth_blocks_api_assets_docs_and_dashboard(self):
        for path in ['/','/assets/app.js','/api/investigate/adaptive','/docs','/health/']:
            messages,calls=self.invoke(path)
            self.assertEqual(messages[0]['status'],401)
            self.assertEqual(calls,[])
            self.assertIn(b'www-authenticate',dict(messages[0]['headers']))

    def test_health_exception_applies_only_to_get_and_head(self):
        for method in ['GET','HEAD']:
            messages,calls=self.invoke('/health',method)
            self.assertEqual(messages[0]['status'],200)
            self.assertEqual(calls,['/health'])
        self.assertEqual(self.invoke('/health','POST')[0][0]['status'],401)

    def test_correct_credentials_reach_downstream_with_private_headers(self):
        header=b'Basic '+base64.b64encode(b'test-judge:unit-test-password-not-live')
        messages,calls=self.invoke('/api/evidence/analyze','POST',header)
        self.assertEqual(calls,['/api/evidence/analyze'])
        self.assertEqual(messages[0]['status'],200)
        headers=dict(messages[0]['headers'])
        self.assertEqual(headers[b'cache-control'],b'no-store')
        self.assertEqual(headers[b'x-content-type-options'],b'nosniff')

    def test_malformed_and_wrong_credentials_do_not_escape_or_leak(self):
        for header in [b'Bearer private-token',b'Basic ???',b'Basic '+base64.b64encode(b'\xff'),
                       b'Basic '+base64.b64encode(b'test-judge:wrong-password')]:
            messages,calls=self.invoke(authorization=header)
            self.assertEqual(messages[0]['status'],401)
            self.assertFalse(calls)
            self.assertNotIn(b'private-token',messages[-1].get('body',b''))


class TestProductionConfig(unittest.TestCase):
    def test_missing_or_weak_credentials_fail_closed_without_printing_them(self):
        for overrides in [{'DEMO_USERNAME':''},{'DEMO_USERNAME':'bad:name'},
                          {'DEMO_PASSWORD':'weak-private'},{'MODEL_API_KEY':''}]:
            with patch.dict(os.environ,{**TEST_ENV,**overrides}):
                with self.assertRaises(RuntimeError) as caught:
                    create_app()
                self.assertNotIn('weak-private',str(caught.exception))

    def test_missing_dashboard_build_fails_closed(self):
        with patch.dict(os.environ,TEST_ENV):
            with self.assertRaisesRegex(RuntimeError,'Built dashboard is missing'):
                create_app(Path(__file__).resolve().parent / 'missing-dashboard-fixture')


class TestProductionHTTP(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        root=Path(self.directory.name)
        (root/'index.html').write_text('<html><title>PhantomTrace</title><script src="/assets/app.js"></script></html>',encoding='utf-8')
        (root/'assets').mkdir()
        (root/'assets'/'app.js').write_text('console.log("test fixture")',encoding='utf-8')
        self.env=patch.dict(os.environ,TEST_ENV)
        self.env.start()
        self.client=TestClient(create_app(root))
        self.auth=('test-judge','unit-test-password-not-live')

    def tearDown(self):
        self.env.stop()
        self.directory.cleanup()

    def test_api_same_origin_dashboard_assets_and_health(self):
        self.assertEqual(self.client.get('/health').status_code,200)
        self.assertEqual(self.client.get('/').status_code,401)
        page=self.client.get('/',auth=self.auth)
        self.assertIn('PhantomTrace',page.text)
        self.assertEqual(page.headers['cache-control'],'no-store')
        self.assertEqual(self.client.get('/assets/app.js',auth=self.auth).status_code,200)
        self.assertEqual(self.client.get('/assets/app.js').status_code,401)
        payload={'logs':'D1 | 2026-10-28T02:05:00Z | PERMISSION_CHANGE | user=admin'}
        self.assertEqual(self.client.post('/api/evidence/analyze',json=payload).status_code,401)
        result=self.client.post('/api/evidence/analyze',json=payload,auth=self.auth)
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.json()['total_events'],1)

    def test_api_unknown_paths_are_not_misreported_as_dashboard_success(self):
        self.assertEqual(self.client.get('/api/unknown',auth=self.auth).status_code,404)
        self.assertEqual(self.client.get('/assets/%2e%2e/production.py',auth=self.auth).status_code,404)

    def test_api_health_does_not_contact_model(self):
        with patch('app.services.meta_ai.get_meta_client',side_effect=AssertionError('No model calls')):
            self.assertEqual(self.client.get('/health').json(),{'status':'healthy'})
