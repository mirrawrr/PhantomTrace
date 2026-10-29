import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { filterEvents, investigate, MAX_LOG_LENGTH, SAMPLE_LOGS, utcTime } from './api.mjs';
import './styles.css';

const label = value => String(value).replaceAll('_', ' ').toLowerCase();

function App() {
  const [logs, setLogs] = useState('');
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [health, setHealth] = useState('Checking backend');
  const [tab, setTab] = useState('report');
  const [query, setQuery] = useState('');
  const [type, setType] = useState('ALL');
  const [selected, setSelected] = useState(null);
  const [fileName, setFileName] = useState('');
  const upload = useRef(null);
  const active = useRef(null);
  const resultHeading = useRef(null);
  const eventDetail = useRef(null);

  useEffect(() => {
    if (tab === 'timeline' && selected) eventDetail.current?.focus();
  }, [tab, selected]);

  useEffect(() => {
    const controller = new AbortController();
    fetch('/health', { signal: controller.signal })
      .then(response => response.ok ? response.json() : Promise.reject())
      .then(data => setHealth(data.status === 'healthy' ? 'Backend connected' : 'Backend unavailable'))
      .catch(() => { if (!controller.signal.aborted) setHealth('Backend unavailable'); });
    return () => { controller.abort(); active.current?.abort(); };
  }, []);

  async function run(event) {
    event.preventDefault();
    if (active.current) return;
    const controller = new AbortController();
    active.current = controller;
    setBusy(true); setError(''); setResult(null); setSelected(null);
    try {
      const data = await investigate(logs, { signal: controller.signal });
      setResult(data); setTab('report'); setQuery(''); setType('ALL');
      setHealth('Backend connected');
      requestAnimationFrame(() => resultHeading.current?.focus());
    } catch (err) {
      setError(err.name === 'AbortError' ? 'Request cancelled. The backend may still finish processing it.'
        : err instanceof TypeError ? 'Cannot reach the backend. Start FastAPI on port 8000 and retry.' : err.message);
    } finally { active.current = null; setBusy(false); }
  }

  async function readFile(event) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    if (file.size > MAX_LOG_LENGTH * 4) { setError('This file is too large. Upload up to 20,000 characters.'); return; }
    try {
      const text = await file.text();
      if (text.length > MAX_LOG_LENGTH) throw new Error('This file exceeds the 20,000 character limit.');
      setLogs(text); setFileName(file.name); setError('');
    } catch (err) { setError(err.message || 'Unable to read this file.'); }
  }

  function showEvent(id) {
    setSelected(id); setQuery(''); setType('ALL'); setTab('timeline');
  }

  function handleTabs(event) {
    const tabs = ['report', 'timeline', 'tools'];
    const index = tabs.indexOf(tab);
    const next = { ArrowRight: (index + 1) % 3, ArrowLeft: (index + 2) % 3,
      Home: 0, End: 2 }[event.key];
    if (next === undefined) return;
    event.preventDefault();
    setTab(tabs[next]);
    document.getElementById(`tab-${tabs[next]}`)?.focus();
  }

  function download() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' }));
    const link = document.createElement('a');
    link.href = url; link.download = 'phantomtrace-investigation.json'; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  const events = result ? filterEvents(result.events, query, type) : [];
  const selectedEvent = result?.events.find(event => event.event_id === selected);
  const verified = result?.verification.verified_references ?? 0;

  return <div className="app">
    <header className="topbar">
      <a className="brand" href="#main"><span className="brandmark" aria-hidden="true">P<span>↗</span></span><span>Phantom<span className="brandlight">Trace</span><small>FORENSIC INTELLIGENCE</small></span></a>
      <div className="topright"><span className={`connection ${health === 'Backend connected' ? 'online' : ''}`}><i />{health}</span><span className="workspace-tag">INVESTIGATION WORKSPACE</span></div>
    </header>

    <main id="main">
      <section className="page-heading"><div><p className="eyebrow">FOLLOW THE EVIDENCE</p><h1>Every event tells a story.</h1><p className="intro">Turn security logs into an investigation you can trace.</p></div><div className="model-tag"><span className="spark">✧</span><div>Powered by Muse Spark<small>Agentic analysis · Evidence references</small></div></div></section>
      <div className="workspace">
        <aside className="input-panel panel">
          <div className="panel-title"><span className="section-number">01</span><h2>Evidence intake</h2><span className="badge">LOGS</span></div>
          <p className="muted">Start with a log sample or bring your own evidence.</p>
          <form onSubmit={run}>
            <div className="input-actions"><button type="button" className="secondary" disabled={busy} onClick={() => { setLogs(SAMPLE_LOGS); setFileName('Synthetic authentication sample'); setError(''); }}>↳ Load sample</button><button type="button" className="text-button" disabled={busy} onClick={() => upload.current.click()}>↑ Upload file</button></div>
            <input ref={upload} className="sr-only" type="file" accept=".txt,.log,text/plain" onChange={readFile} disabled={busy} aria-label="Upload security logs" />
            <label className="field-label" htmlFor="logs">Security logs <span>TXT / LOG</span></label>
            <textarea id="logs" spellCheck="false" value={logs} maxLength={MAX_LOG_LENGTH} disabled={busy} onChange={event => { setLogs(event.target.value); setFileName(''); }} placeholder={'EVT001 | 2026-10-28T02:12:00Z |\nPERMISSION_CHANGE | user=admin |\nrole=administrator'} />
            <div className="editor-footer"><span>{fileName || 'Paste pipe-separated events'}</span><span>{logs.length.toLocaleString()} / 20,000</span></div>
            <p className="format-help">One event per line. Include an ID, timestamp with timezone, event type and key=value fields.</p>
            <button className="primary" disabled={busy || !logs.trim()} type="submit">{busy ? <><span className="spinner" />Investigating evidence…</> : <>Start investigation <span>↗</span></>}</button>
            {busy && <button type="button" className="cancel" onClick={() => active.current?.abort()}>Cancel request</button>}
            <p className="privacy">Logs are sent to Meta for analysis. Use synthetic data for your demo. API keys stay in your backend.</p>
          </form>
          {error && <div className="error" role="alert">{error}</div>}
          <div className="pipeline"><p className="eyebrow">THE INVESTIGATION PATH</p>{[['01', 'Parse', 'Structure and validate events'], ['02', 'Correlate', 'Connect activity across evidence'], ['03', 'Verify', 'Check cited event references']].map(([n, title, desc]) => <div className="pipeline-step" key={n}><span>{n}</span><div><strong>{title}</strong><small>{desc}</small></div></div>)}</div>
        </aside>

        <section className="results" aria-busy={busy}>
          <div className="result-title"><div><p className="eyebrow">INVESTIGATION OVERVIEW</p><h2 ref={resultHeading} tabIndex={-1}>{result ? 'The evidence, connected.' : busy ? 'Following the evidence…' : 'Your investigation starts here.'}</h2></div>{result && <button className="secondary" onClick={download}>↓ Export JSON</button>}</div>
          <div className="stats"><Stat title="Events parsed" value={result ? result.events.length : '—'} note="Source evidence" /><Stat title="Report findings" value={result ? result.report.findings.length : '—'} note="For analyst review" /><Stat title="References valid" value={result ? `${verified}/${result.verification.total_findings}` : '—'} note="Finding ID checks" /><Stat title="Tool calls" value={result ? result.tool_history.length : '—'} note="Recorded executions" /></div>
          {!result ? <div className="empty-state panel" role="status"><div className={`radar ${busy ? 'scanning' : ''}`} aria-hidden="true"><span /><i /><b>⌖</b></div><p className="eyebrow">{busy ? 'MUSE SPARK IS INVESTIGATING' : 'READY WHEN YOU ARE'}</p><h3>{busy ? 'Building a traceable investigation' : 'From raw logs to a clearer picture.'}</h3><p>{busy ? 'The agent is working with the evidence tools. Actual tool results will appear when the request completes.' : 'Add evidence on the left. PhantomTrace will connect events, surface findings and check the report’s references.'}</p><div className="empty-tags"><span>Evidence first</span><span>Traceable tool calls</span><span>Human review</span></div></div> : <>
            <div className="tabbar" onKeyDown={handleTabs} role="tablist" aria-label="Investigation views">{[['report', 'Findings'], ['timeline', 'Event timeline'], ['tools', 'Tool activity']].map(([id, text]) => <button key={id} id={`tab-${id}`} type="button" role="tab" tabIndex={tab === id ? 0 : -1} aria-selected={tab === id} aria-controls={`view-${id}`} onClick={() => setTab(id)}>{text}<span>{id === 'report' ? result.report.findings.length : id === 'timeline' ? result.events.length : result.tool_history.length}</span></button>)}</div>
            <div role="tabpanel" id={`view-${tab}`} aria-labelledby={`tab-${tab}`}>
              {tab === 'report' && <div className="report-content"><article className="summary panel"><p className="eyebrow">EXECUTIVE SUMMARY</p><p>{result.report.summary}</p><span className="small-tag">{result.model}</span></article><div className="subheading"><h3>Key findings</h3><span>Review each claim against its evidence</span></div>{result.report.findings.length === 0 && <p className="panel no-findings">No findings were reported. This does not establish that the activity is safe.</p>}{result.report.findings.map((finding, index) => <article className="finding panel" key={index}><div className="finding-top"><span className="finding-number">{String(index + 1).padStart(2, '0')}</span><h3>{label(finding.type)}</h3><span className="review-tag">REVIEW</span></div><p>{finding.description}</p><div className="evidence-links"><span>Evidence</span>{finding.event_ids.map(id => <button key={id} onClick={() => showEvent(id)}>{id} ↗</button>)}</div></article>)}<div className="report-bottom"><article className="panel"><h3>Recommended next steps</h3><ul>{result.report.recommendations.map((item, index) => <li key={index}>{item}</li>)}</ul></article><article className="panel limitations"><h3>Investigation limitations</h3><ul>{result.report.limitations.map((item, index) => <li key={index}>{item}</li>)}</ul></article></div><p className="verification-note">Reference checks confirm that cited event IDs exist. They do not prove a conclusion is correct.</p></div>}
              {tab === 'timeline' && <div className="timeline-view"><div className="filters"><label><span className="sr-only">Search events</span><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search ID, user, IP or event…" /></label><label><span className="sr-only">Filter event type</span><select value={type} onChange={event => setType(event.target.value)}><option value="ALL">All event types</option>{[...new Set(result.events.map(event => event.event_type))].map(value => <option key={value} value={value}>{label(value)}</option>)}</select></label></div><p className="timeline-count">{events.length} events · Chronological order · UTC</p><div className="timeline">{events.map(event => <button className={`timeline-event panel ${selected === event.event_id ? 'selected' : ''}`} key={event.event_id} onClick={() => setSelected(event.event_id)}><time>{utcTime(event.timestamp)}</time><div><span className={`event-dot ${event.event_type === 'LOGIN_FAILED' ? 'warn' : ''}`} /><strong>{label(event.event_type)}</strong><span className="event-id">{event.event_id}</span></div><p>{event.user || 'Unknown user'} <span>·</span> {event.ip || 'No IP recorded'}</p></button>)}</div>{events.length === 0 && <p className="panel no-findings">No events match these filters.</p>}{selectedEvent && <article className="panel event-detail" ref={eventDetail} tabIndex={-1}><div className="subheading"><h3>Evidence / {selectedEvent.event_id}</h3><button className="text-button" onClick={() => setSelected(null)}>Close</button></div><p className="muted">Original source entry</p><pre>{selectedEvent.raw}</pre><dl>{Object.entries(selectedEvent.fields).map(([key, value]) => <React.Fragment key={key}><dt>{key}</dt><dd>{value}</dd></React.Fragment>)}</dl></article>}</div>}
              {tab === 'tools' && <div className="tool-view"><p className="muted">Actual tool executions returned by this investigation, in execution order.</p>{result.tool_history.map((entry, index) => <details className="panel tool-entry" key={`${entry.call_id}-${index}`}><summary><span className="section-number">{String(index + 1).padStart(2, '0')}</span><strong>{entry.tool}</strong><span className={entry.result?.error ? 'tool-error' : 'tool-ok'}>{entry.result?.error ? 'Tool error' : 'Returned'}</span></summary><p className="call-id">Call ID: {entry.call_id}</p><pre>{JSON.stringify(entry.result, null, 2)}</pre></details>)}</div>}
            </div>
          </>}
        </section>
      </div>
      <footer><span>PHANTOMTRACE <span className="footer-slash">/</span> Evidence into insight.</span><span>Built for investigation. Guided by human judgment.</span></footer>
    </main>
  </div>;
}

function Stat({ title, value, note }) { return <article className="stat panel"><p>{title}</p><strong>{value}</strong><small>{note}</small></article>; }

createRoot(document.getElementById('root')).render(<App />);
