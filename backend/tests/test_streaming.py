import json
import unittest
import tempfile
from pathlib import Path

from app.investigation_stream import investigation_events
from app.demo_limits import DemoLimits
from app.services.adaptive_agent import AdaptiveRequest, investigate_adaptive
from test_adaptive_agent import request, finding, report
from test_investigation_agent import call, response, client_for


class TestStreaming(unittest.TestCase):
    def test_body_limit_wrapper_delivers_body_once_then_forwards_disconnect(self):
        with tempfile.TemporaryDirectory() as folder:
            received=[]
            incoming=iter([{'type':'http.request','body':b'{}','more_body':False},
                           {'type':'http.disconnect'}])
            async def receive():
                return next(incoming)
            async def send(message):
                pass
            async def downstream(scope,receive,send):
                received.append(await receive())
                received.append(await receive())
            app=DemoLimits(downstream,str(Path(folder)/'usage.db'))
            coroutine=app({'type':'http','method':'POST','path':'/api/investigate/adaptive/stream'},receive,send)
            # All fixture awaits complete immediately; no OS event loop required.
            with self.assertRaises(StopIteration):
                coroutine.send(None)
            self.assertEqual(received[0]['body'],b'{}')
            self.assertEqual(received[1]['type'],'http.disconnect')

    def test_callback_emits_actual_tools_before_final_model_response(self):
        seen=[]
        client=client_for(response([call('inspect_events',json.dumps({
            'event_ids':['AMB001'], 'purpose':'Inspect permission evidence'}))]),
            response(report=report(finding('AMB001'))))
        result=investigate_adaptive(request('ambiguous'),client=client,
            on_event=lambda kind,data: seen.append((kind,data)))
        self.assertEqual([kind for kind,data in seen],['workspace','tool'])
        self.assertEqual(seen[1][1],result['tool_history'][0])
        self.assertEqual(seen[1][1]['result']['events'][0]['event_id'],'AMB001')

    def test_stream_preserves_workspace_tool_and_final_order(self):
        def fake(request,on_event):
            on_event('workspace',{'events':[]})
            on_event('tool',{'tool':'query_events','result':{'events':[]}})
            return {'status':'completed'}
        frames=list(investigation_events(AdaptiveRequest(logs='fixture'),investigator=fake))
        self.assertEqual([f.split('\n')[0] for f in frames],['event: workspace','event: tool','event: result'])

    def test_failed_stream_retains_completed_activity_and_sanitizes_error(self):
        def fake(request,on_event):
            on_event('tool',{'tool':'query_events','result':{'events':[]}})
            raise RuntimeError('private-provider-body-and-key')
        frames=list(investigation_events(AdaptiveRequest(logs='fixture'),investigator=fake))
        self.assertEqual(len(frames),2)
        self.assertTrue(frames[-1].startswith('event: error'))
        self.assertNotIn('private-provider', ''.join(frames))
        self.assertNotIn('event: result',''.join(frames))
