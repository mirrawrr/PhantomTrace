import test from 'node:test';
import assert from 'node:assert/strict';
import { disposition, eventVerdict, nextSteps, returnedEventIds, toolSummary, verdictCounts } from '../src/console.mjs';
import { investigate, readInvestigationStream } from '../src/api.mjs';

test('dispositions and event markers prioritize unresolved over record matches',()=>{
  const findings=[{disposition:'explained_by_record',event_ids:['A']},{disposition:'unresolved',event_ids:['A','B']},{event_ids:['C']}];
  assert.deepEqual(verdictCounts(findings),{explained:1,review:1,unresolved:1});
  assert.equal(eventVerdict('A',findings),'unresolved');
  assert.equal(eventVerdict('D',findings),'neutral');
  assert.equal(disposition({}),'review');
});
test('feed summaries use returned values and one next-actions source',()=>{
  assert.equal(toolSummary({result:{matching_records:[{change_id:'CHG-1042'}]}}),'CHG-1042 MATCH · supplied');
  assert.equal(toolSummary({result:{all_valid:false}}),'CHECK FAILED');
  assert.deepEqual([...returnedEventIds([{result:{events:[{event_id:'A'}]}}])],['A']);
  assert.deepEqual(nextSteps({handoff:{next_actions:['Ask owner.','Ask owner.']},recommendations:['Duplicate version.']}),['Ask owner.']);
});
function sse(chunks) {
  return new Response(new ReadableStream({start(controller){ chunks.forEach(chunk=>controller.enqueue(new TextEncoder().encode(chunk)));controller.close(); }}),{headers:{'Content-Type':'text/event-stream'}});
}
test('SSE parser handles split frames, UTF-8 and returns only actual events',async()=>{
  const seen=[];
  const output=await readInvestigationStream(sse(['event: work','space\ndata: {"events":[]}\n','\nevent: tool\ndata: {"tool":"inspect_events","purpose":"Check café"}\n\n','event: result\ndata: {"status":"completed"}\n\n']), (kind,data)=>seen.push([kind,data]));
  assert.deepEqual(seen.map(x=>x[0]),['workspace','tool']);
  assert.equal(seen[1][1].purpose,'Check café');
  assert.equal(output.status,'completed');
});
test('SSE does not turn a truncated or failed stream into a report',async()=>{
  await assert.rejects(readInvestigationStream(sse(['event: tool\ndata: {"tool":"query_events"}\n\n']),()=>{}),/before the final report/);
  await assert.rejects(readInvestigationStream(sse(['event: error\ndata: {"code":"private-body","message":"secret"}\n\n']),()=>{}),/stream_failed/);
});
test('provider error shows only allowlisted status and labels',async()=>{
  await assert.rejects(readInvestigationStream(sse(['event: error\ndata: '+JSON.stringify({code:'provider_http_error',provider:{http_status:400,provider_code:'context_length_exceeded',parameter:'input',message:'private-key'}})+'\n\n']),()=>{}),error=>{
    assert.match(error.message,/HTTP 400/);assert.match(error.message,/context_length_exceeded/);
    assert.match(error.message,/field: input/);assert.doesNotMatch(error.message,/private-key/);return true;
  });
});
test('adaptive stream retains authentication and cancellation on same request',async()=>{
  const final={status:'completed',report:{summary:'Review',findings:[],recommendations:[],limitations:[]},events:[],tool_history:[],verification:{results:[]}};
  const controller=new AbortController();
  await investigate('event',{authorization:'Basic fixture',signal:controller.signal,onEvent:()=>{},fetcher:async(url,options)=>{
    assert.equal(url,'/api/investigate/adaptive/stream');
    assert.equal(options.signal,controller.signal);
    assert.equal(options.headers.Authorization,'Basic fixture');
    return sse(['event: result\ndata: '+JSON.stringify(final)+'\n\n']);
  }});
});
