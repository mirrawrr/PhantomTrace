import React, { useEffect, useState } from 'react';
import { filterEvents, utcTime } from './api.mjs';
import { disposition, eventVerdict, nextSteps, returnedEventIds, toolSummary, verdictCounts } from './console.mjs';

const label = value => String(value).replaceAll('_', ' ').toLowerCase();

export function WitnessPanel({ testimony, separate }) {
  if (!testimony) return null;
  return <section className="witness-console panel"><p className="eyebrow">{separate ? 'SEPARATE WITNESS CHECK · SUBMITTED INPUTS' : 'WITNESS CLAIM CHECK'}</p><blockquote>{testimony.statement}</blockquote><p>{testimony.notice}</p><div className="witness-claims">{testimony.claims.length === 0 && <p>No checkable claims extracted.</p>}{testimony.claims.map((claim, i) => <article className={`witness-claim ${claim.verdict === 'differs_from_log_field' ? 'unresolved' : claim.verdict === 'matches_log_field' ? 'verified' : 'review'}`} key={i}><h3>“{claim.quote}”</h3><strong>{claim.verdict === 'matches_log_field' ? 'Mapped field matches' : claim.verdict === 'differs_from_log_field' ? 'Mapped field differs' : 'Not checkable from logs'}</strong>{claim.field && <p className="mono">{claim.event_id} / {claim.field}<br />Statement: {claim.value}<br />Source: {claim.observed ?? 'not recorded'}</p>}{claim.matching_change_ids.length > 0 && <p>Source event matches supplied {claim.matching_change_ids.join(', ')}. This does not authenticate the record or support a conflicting claim.</p>}</article>)}</div></section>;
}

export default function CaseConsole({ result, liveEvents, liveTools, busy }) {
  const [activeFinding, setActiveFinding] = useState(null);
  const [activeEvent, setActiveEvent] = useState(null);
  const [query, setQuery] = useState('');
  const [eventType, setEventType] = useState('ALL');
  useEffect(() => { setActiveFinding(null); setActiveEvent(null); setQuery(''); setEventType('ALL'); }, [result]);
  const findings = result?.report.findings || [];
  const events = [...(result?.events || liveEvents)].sort((a,b) => Date.parse(a.timestamp) - Date.parse(b.timestamp));
  const visibleEvents = filterEvents(events, query, eventType);
  const history = result?.tool_history || liveTools;
  const returned = returnedEventIds(history);
  const suppliedMatches = new Set(history.filter(entry => entry.tool === 'lookup_change' && entry.result?.matching_records?.length).map(entry => entry.result.event_id));
  const counts = verdictCounts(findings);
  const selectedIds = new Set(activeFinding === null ? [] : findings[activeFinding]?.event_ids || []);
  const source = events.find(e => e.event_id === activeEvent);
  const references = result?.verification;
  const steps = result ? nextSteps(result.report) : [];
  return <div className="case-console">
    {result?.replay && <div className="replay-banner panel"><strong>RECORDED REPLAY / NOT LIVE</strong><p>{result.replay.label}. {result.replay.notice}</p></div>}
    <section className="verdict-strip" aria-label="Report dispositions">
      {[['explained', 'RECORD MATCH'], ['review', 'NEEDS REVIEW'], ['unresolved', 'UNRESOLVED']].map(([key, text]) => <div className={`score ${key}`} key={key}><strong>{result ? String(counts[key]).padStart(2, '0') : '—'}</strong><span>{text}</span></div>)}
      <div key={result ? 'checked' : 'pending'} className="score verified"><strong>{result ? `${references.verified_references}/${references.total_findings}` : '—'}</strong><span>REFERENCES VERIFIED</span><small>ID existence only</small></div>
    </section>
    <div className="console-columns"><div className="case-main">
      <section className="timeline-hero panel" aria-labelledby="timeline-heading"><div className="section-head"><div><p className="eyebrow">01 / EVIDENCE CHRONOLOGY</p><h2 id="timeline-heading">Follow the sequence.</h2></div><span className="mono">{events.length} EVENTS / UTC</span></div>
        <p className="helper">Select a finding to highlight its events. Select an event to inspect the original source.</p>
        <details className="timeline-filters"><summary>Search &amp; filter timeline</summary><label>Search events<input value={query} onChange={e => setQuery(e.target.value)} placeholder="Event ID, user, IP or source text" /></label><label>Event type<select value={eventType} onChange={e => setEventType(e.target.value)}><option value="ALL">All event types</option>{[...new Set(events.map(e => e.event_type))].map(type => <option key={type} value={type}>{label(type)}</option>)}</select></label><p>{visibleEvents.length} of {events.length} events shown</p></details>
        <div className="horizontal-timeline" role="group" aria-label="Chronological evidence events">{visibleEvents.map(event => {
          const tone = result ? eventVerdict(event.event_id, findings) : suppliedMatches.has(event.event_id) ? 'explained' : returned.has(event.event_id) ? 'review' : 'neutral';
          const seen = returned.has(event.event_id) || !!result;
          return <button type="button" key={event.event_id} className={`timeline-node ${tone} ${seen ? 'seen' : 'pending'} ${selectedIds.has(event.event_id) ? 'linked' : ''} ${activeEvent === event.event_id ? 'selected' : ''}`} aria-pressed={activeEvent === event.event_id} onClick={() => setActiveEvent(event.event_id)}>
            <time>{utcTime(event.timestamp).slice(11,19)}</time><span className="node-track"><i className="event-marker" /></span><strong>{event.event_id}</strong><span>{label(event.event_type)}</span><small>{event.user || 'Unknown user'}</small><span className="node-state">{result ? tone === 'neutral' ? 'No finding' : tone === 'explained' ? 'Record match' : tone : suppliedMatches.has(event.event_id) ? 'Supplied match' : seen ? 'Tool returned' : 'Parsed / pending'}</span>
          </button>;
        })}</div>
        {!events.length && <p className="waiting" role="status">{busy ? 'Waiting for the parser. Events appear when the server returns them.' : 'Load a case and start an investigation, or replay the recorded run.'}</p>}
        {source && <article className="source-drawer"><div className="section-head"><h3>Original source / {source.event_id}</h3><button type="button" onClick={() => setActiveEvent(null)}>Close source</button></div><pre>{source.raw}</pre><dl>{Object.entries(source.fields).map(([k,v]) => <React.Fragment key={k}><dt>{k}</dt><dd>{v}</dd></React.Fragment>)}</dl></article>}
        <p className="timeline-legend"><span className="explained">● Supplied record match</span><span className="review">● Review</span><span className="unresolved">● Unresolved</span><span className="verified">◇ Source returned</span></p>{busy && <p className="helper">During the run, colors show returned evidence and supplied-record lookups. Final dispositions are pending. A record match is not authenticated approval.</p>}
      </section>
      {result && <>
        <details className="assessment panel"><summary>Case brief / model assessment</summary><p>{result.report.summary}</p><p className="helper">Interpretation requires human review. Model: {result.model}</p></details>
        <section className="findings-section" aria-labelledby="findings-heading"><div className="section-head"><h2 id="findings-heading">02 / Findings</h2><span className="mono">{findings.length} LEADS</span></div><div className="finding-grid">{findings.map((finding,index) => <article className={`console-finding panel ${disposition(finding)} ${activeFinding === index || finding.event_ids.includes(activeEvent) ? 'active-finding' : ''}`} key={index}>
          <button type="button" className="finding-selector" aria-pressed={activeFinding === index} onClick={() => { setActiveFinding(activeFinding === index ? null : index); setQuery(''); setEventType('ALL'); }}><span className="finding-index">{String(index + 1).padStart(2,'0')}</span><h3>{label(finding.type)}</h3><span className={`verdict-badge ${disposition(finding)}`}>{disposition(finding) === 'explained' ? 'RECORD MATCH' : disposition(finding) === 'unresolved' ? 'UNRESOLVED' : 'REVIEW'}</span></button>
          {finding.source_observations ? <ul className="observations">{finding.source_observations.map((o,i) => <li key={i}>{o.text}</li>)}</ul> : <p>{finding.description}</p>}
          {finding.disposition === 'explained_by_record' && <p className="record-caveat">Supplied {finding.change_ids.join(', ')} matches this event only. Authenticity unverified.</p>}
          <div className="evidence-buttons">{finding.event_ids.map(id => <button type="button" key={id} onClick={() => { setActiveFinding(index); setActiveEvent(id); document.getElementById('timeline-heading')?.scrollIntoView({ block:'nearest' }); }}>{id} ↗</button>)}</div>
          <details><summary>Assessment, alternatives &amp; next evidence</summary><p>{finding.description}</p>{finding.alternative_explanation && <><h4>Another explanation</h4><p>{finding.alternative_explanation}</p><h4>Next evidence</h4><p>{finding.next_check}</p></>}{finding.facts && <><h4>Structured checks</h4><ul>{finding.facts.map((f,i) => <li key={i} className="mono">{f.event_id} / {f.field} = {f.value}</li>)}{finding.sequences.map((s,i) => <li key={`s${i}`}>{s.earlier_id} precedes {s.later_id} within {s.max_seconds}s</li>)}</ul></>}</details>
        </article>)}</div>{!findings.length && <p>No findings reported. This does not establish safety.</p>}</section>
        <section className="next-steps panel"><p className="eyebrow">03 / ANALYST HANDOFF · DRAFT</p><h2>Next steps</h2>{result.report.handoff?.situation && <p>{result.report.handoff.situation}</p>}<ol>{steps.map((step,i) => <li key={i}>{step}</li>)}</ol>{result.report.handoff?.open_questions?.length > 0 && <details><summary>Open questions &amp; evidence scope</summary><p>{result.report.handoff.evidence_scope}</p><ul>{result.report.handoff.open_questions.map((q,i) => <li key={i}>{q}</li>)}</ul></details>}</section>
        <details className="limitations-footer"><summary>Limitations / {result.claim_verification ? 'Structured checks passed; interpretation unverified' : 'References checked; conclusions unverified'}</summary><ul>{result.report.limitations.map((item,i) => <li key={i}>{item}</li>)}</ul></details>
      </>}
      {!result && <p className="run-state" role="status">{busy ? 'INVESTIGATION ACTIVE / Waiting for real tool executions. Final dispositions appear only after report validation.' : history.length ? 'NO FINAL REPORT / Completed executions below remain available.' : 'AWAITING CASE / No model execution yet.'}</p>}
    </div><aside className="activity-rail panel" aria-labelledby="activity-heading"><div className="section-head"><div><p className="eyebrow">EXECUTION FEED</p><h2 id="activity-heading">Tool activity</h2></div><span className={`status-led ${busy ? 'is-active' : ''}`} aria-label={busy ? 'Investigation active' : 'Investigation idle'} /></div><p className="helper">{result?.replay ? 'Recorded executions from the labelled replay.' : busy ? 'Completed executions arrive from the server. No simulated progress.' : 'Actual returned executions, in order.'}</p>
      <div className="activity-feed" role="log" aria-live="polite" aria-relevant="additions">{history.map((entry,i) => <details key={`${entry.call_id}-${i}`} className={`feed-entry ${entry.result?.error ? 'unresolved' : 'verified'}`}><summary><span className="feed-index">{String(i+1).padStart(2,'0')}</span><strong>{entry.tool}</strong><span>→ {toolSummary(entry)}</span></summary><p>{entry.purpose}</p><small className="mono">Call: {entry.call_id}</small><pre>{JSON.stringify(entry.result,null,2)}</pre></details>)}</div>{!history.length && <p className="waiting">{busy ? 'Awaiting first completed tool call…' : 'No tool calls yet.'}</p>}<p className="feed-footnote">Purpose questions explain tool use. Private model reasoning is never shown. A tool PASS checks its submitted facts, not the entire narrative.</p>
    </aside></div>
  </div>;
}
