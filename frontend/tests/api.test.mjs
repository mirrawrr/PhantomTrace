import test from 'node:test';
import assert from 'node:assert/strict';
import { investigate, filterEvents, utcTime } from '../src/api.mjs';

const completed = {status:'completed', report:{summary:'Review',findings:[],recommendations:[],limitations:[]},events:[],tool_history:[],verification:{results:[]}};

test('keeps supplied changes separate from logs and preserves fixed mode', async () => {
  const changes = [{change_id:'CHG-1'}];
  await investigate('event', {changes, fetcher:async (url,options) => {
    assert.equal(url,'/api/investigate/adaptive');
    assert.deepEqual(JSON.parse(options.body),{logs:'event',changes});
    return {ok:true,json:async()=>completed};
  }});
  await investigate('event', {mode:'fixed',changes,fetcher:async (url,options) => {
    assert.equal(url,'/api/investigate/agent');
    assert.deepEqual(JSON.parse(options.body),{logs:'event'});
    return {ok:true,json:async()=>completed};
  }});
});

test('posts logs and passes cancellation signal through to backend', async () => {
  const signal = new AbortController().signal;
  const result = await investigate('event', {signal, fetcher: async (url, options) => {
    assert.equal(url, '/api/investigate/adaptive');
    assert.equal(options.method, 'POST');
    assert.deepEqual(JSON.parse(options.body), {logs:'event', changes:[]});
    assert.equal(options.signal, signal);
    return {ok:true,json:async()=>completed};
  }});
  assert.equal(result,completed);
});

test('rejects empty and oversized input before contacting backend', async () => {
  for (const logs of ['  ', 'a'.repeat(20001)]) {
    await assert.rejects(investigate(logs,{fetcher:()=>assert.fail('must not fetch')}));
  }
});

test('shows parser validation errors', async () => {
  await assert.rejects(investigate('bad',{fetcher:async()=>({ok:false,status:422,json:async()=>({detail:{errors:['Line 1: Invalid timestamp.']}})})}),/Invalid timestamp/);
});

test('does not display provider error bodies', async () => {
  await assert.rejects(investigate('event',{fetcher:async()=>({ok:false,status:502,json:async()=>({detail:'sensitive-provider-message'})})}),error=>!error.message.includes('sensitive-provider-message') && error.message.includes('configuration'));
});

test('handles non-JSON and incomplete successful responses', async () => {
  await assert.rejects(investigate('event',{fetcher:async()=>({ok:true,json:async()=>{throw new Error();}})}),/unreadable/);
  await assert.rejects(investigate('event',{fetcher:async()=>({ok:true,json:async()=>({status:'completed'})})}),/format/);
});

test('keeps abort errors recognizable for cancellation UI', async () => {
  await assert.rejects(investigate('event',{fetcher:async()=>{throw new DOMException('Cancelled','AbortError');}}),{name:'AbortError'});
});

test('filters and orders evidence by instant rather than timestamp string', () => {
  const events = [
    {event_id:'LATE',timestamp:'2026-10-28T01:00:00Z',event_type:'LOGIN_SUCCESS',user:'admin'},
    {event_id:'EARLY',timestamp:'2026-10-28T08:00:00+08:00',event_type:'LOGIN_FAILED',user:'admin'}
  ];
  assert.deepEqual(filterEvents(events,'ADMIN','ALL').map(e=>e.event_id),['EARLY','LATE']);
  assert.deepEqual(filterEvents(events,'','LOGIN_FAILED').map(e=>e.event_id),['EARLY']);
  assert.equal(filterEvents(events,'missing','ALL').length,0);
  assert.equal(events[0].event_id,'LATE');
  assert.equal(utcTime(events[1].timestamp),'2026-10-28 00:00:00 UTC');
});
