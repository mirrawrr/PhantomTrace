import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { investigate, MAX_LOG_LENGTH } from './api.mjs';
import './styles.css';
import scenarios from './scenarios.json';
import recordedRun from './recorded-run.json';
import CaseConsole, { WitnessPanel } from './CaseConsole.jsx';

function App() {
  const [intakeOpen, setIntakeOpen] = useState(true);
  const [liveEvents, setLiveEvents] = useState([]);
  const [liveTools, setLiveTools] = useState([]);
  const [witnessChecking, setWitnessChecking] = useState(false);
  const [witnessReview, setWitnessReview] = useState(null);
  const [witnessError, setWitnessError] = useState('');
  const [witness, setWitness] = useState('');
  const [username, setUsername] = useState('demo');
  const [password, setPassword] = useState('');
  const [voiceBusy, setVoiceBusy] = useState(false);
  const [voiceNotice, setVoiceNotice] = useState('');
  const [logs, setLogs] = useState('');
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [health, setHealth] = useState('Checking backend');
  const [fileName, setFileName] = useState('');
  const [mode, setMode] = useState('adaptive');
  const [scenario, setScenario] = useState('mixed');
  const [changeText, setChangeText] = useState('[]');
  const upload = useRef(null);
  const active = useRef(null);
  const resultHeading = useRef(null);

  useEffect(() => {
    const controller = new AbortController();
    fetch('/health', { signal: controller.signal })
      .then(response => response.ok ? response.json() : Promise.reject())
      .then(data => setHealth(data.status === 'healthy' ? 'Backend connected' : 'Backend unavailable'))
      .catch(() => { if (!controller.signal.aborted) setHealth('Backend unavailable'); });
    return () => { controller.abort(); active.current?.abort(); };
  }, []);

  const authorization = password ? 'Basic ' + btoa(String.fromCharCode(...new TextEncoder().encode(`${username}:${password}`))) : '';

  function replay() {
    setWitnessReview(null); setWitnessError(''); setResult(structuredClone(recordedRun)); setLogs(recordedRun.events.map(e => e.raw).join('\n'));
    setError('');
    requestAnimationFrame(() => resultHeading.current?.focus());
  }

  async function transcribe(event) {
    const file = event.target.files?.[0]; event.target.value = '';
    if (!file) return;
    if (file.size > 3000000) { setError('Choose a WAV voice note up to 60 seconds and 3 MB.'); return; }
    setVoiceBusy(true); setError('');
    try {
      const response = await fetch('/api/testimony/transcribe', { method: 'POST', headers: { 'Content-Type': 'audio/wav', ...(authorization ? { Authorization: authorization } : {}) }, body: file });
      if (!response.ok) throw new Error(response.status === 401 ? 'Enter demo credentials before transcribing.' : response.status === 429 ? 'Live demo allowance reached. Enter testimony as text instead.' : 'Transcription unavailable. Use mono 16-bit PCM WAV at 16 or 24 kHz, up to 60 seconds, or type the statement.');
      const data = await response.json(); setWitness(data.transcript); setVoiceNotice(data.notice);
    } catch (err) { setError(err.message); } finally { setVoiceBusy(false); }
  }

  async function checkWitnessOnly() {
    if (!logs.trim() || !witness.trim()) { setWitnessError('Load security logs and add a witness statement first.'); return; }
    let changes;
    try { changes = JSON.parse(changeText); if (!Array.isArray(changes)) throw new Error(); }
    catch { setWitnessError('Change records must be a JSON array.'); return; }
    setWitnessChecking(true); setVoiceBusy(true); setWitnessError(''); setWitnessReview(null);
    try {
      const response = await fetch('/api/investigate/testimony', { method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(authorization ? { Authorization: authorization } : {}) },
        body: JSON.stringify({ logs, changes, witness_statement: witness }) });
      const data = await response.json();
      if (!response.ok) {
        const codes = new Set(['budget_unavailable','provider_timeout','provider_connection','provider_authentication','provider_rate_limit','provider_http_error','provider_error','model_schema_invalid','claim_check_failed','model_output_limit','model_incomplete','quote_source_mismatch']);
        const code = codes.has(data.detail?.code) ? data.detail.code : `HTTP ${response.status}`;
        throw new Error(`Witness-only check did not finish (${code}). Testimony remains unverified.`);
      }
      setWitnessReview(data.testimony);
    } catch (err) { setWitnessError(err instanceof TypeError ? 'Cannot reach the backend.' : err.message); }
    finally { setVoiceBusy(false); setWitnessChecking(false); }
  }

  async function run(event) {
    event.preventDefault();
    if (active.current) return;
    let changes = [];
    if (mode === 'adaptive') {
      try {
        changes = JSON.parse(changeText);
        if (!Array.isArray(changes) || changes.length > 30) throw new Error();
      } catch {
        setError('Change records must be a JSON array with up to 30 records. Use [] when no records are available.');
        return;
      }
    }
    const controller = new AbortController();
    active.current = controller;
    setBusy(true); setIntakeOpen(false); setLiveEvents([]); setLiveTools([]); setError(''); setWitnessReview(null); setWitnessError(''); setResult(null);
    try {
      const data = await investigate(logs, { signal: controller.signal, mode, changes, witnessStatement: witness, authorization, onEvent: mode === 'adaptive' ? (kind, data) => { if (controller.signal.aborted) return; if (kind === 'workspace') setLiveEvents(data.events); if (kind === 'tool') setLiveTools(items => [...items, data]); } : undefined });
      setResult(data);
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

  function loadScenario() {
    const sample = scenarios.find(item => item.id === scenario);
    setLogs(sample.logs); setChangeText(JSON.stringify(sample.changes, null, 2));
    setFileName(`Synthetic: ${sample.title}`); setError('');
  }

  function download() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' }));
    const link = document.createElement('a');
    link.href = url; link.download = 'phantomtrace-investigation.json'; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  const testimony = witnessReview || result?.testimony;
  return <div className="app case-app">
    <header className="topbar"><a className="brand" href="#main"><span className="brandmark" aria-hidden="true">P↗</span><span>PHANTOM<span className="brandlight">TRACE</span><small>CASE CONSOLE / EVIDENCE OPERATIONS</small></span></a><span className={`connection ${health === 'Backend connected' ? 'online' : ''}`}><i />{health}</span></header>
    <main id="main">
      <section className="case-heading"><div><p className="eyebrow">FOLLOW EVIDENCE. CHALLENGE THE STORY.</p><h1 ref={resultHeading} tabIndex={-1}>{busy ? 'INVESTIGATION ACTIVE' : result ? 'CASE / EVIDENCE CONNECTED' : 'YOUR NEXT CASE STARTS HERE'}</h1></div><div className="case-controls">{busy && <button type="button" className="cancel" onClick={() => active.current?.abort()}>Cancel request</button>}{result && <button type="button" className="secondary" onClick={download}>↓ Export JSON</button>}<span className="model-tag">MUSE SPARK / HUMAN REVIEW</span></div></section>
      <details className="intake-shell panel" open={intakeOpen} onToggle={e => setIntakeOpen(e.currentTarget.open)}><summary><span>01 / EVIDENCE INTAKE</span><span className="intake-meta">{busy ? 'RUNNING' : `${logs.split('\n').filter(line => line.trim()).length} INPUT LINES`} · {mode === 'adaptive' ? 'ADAPTIVE' : 'FIXED PIPELINE'} · {intakeOpen ? 'COLLAPSE −' : 'EDIT INPUTS +'}</span></summary><div className="intake-body"><div className="intake-heading"><div><h2>Bring the evidence.</h2><p>Use a synthetic case or your own permitted logs.</p></div><button type="button" className="secondary" disabled={busy || voiceBusy} onClick={() => { replay(); setIntakeOpen(false); }}>↻ Replay a recorded run</button></div><p className="helper">Replay opens an older five-event recording instantly after the page loads. No new AI call.</p>
          <form onSubmit={run}>
            <details><summary>Live demo credentials</summary><label className="field-label" htmlFor="demo-user">Username</label><input id="demo-user" value={username} autoComplete="username" onChange={e => setUsername(e.target.value)} /><label className="field-label" htmlFor="demo-password">Password</label><input id="demo-password" type="password" value={password} autoComplete="current-password" onChange={e => setPassword(e.target.value)} /><p className="format-help">Used only for this page session. Never include credentials in logs or exports.</p></details>
            <label className="field-label" htmlFor="investigation-mode">Investigation method</label>
            <select id="investigation-mode" className="intake-select" value={mode} disabled={busy} onChange={event => setMode(event.target.value)}><option value="adaptive">Adaptive investigation</option><option value="fixed">Original fixed pipeline</option></select>
            <label className="field-label" htmlFor="scenario">Synthetic practice case</label>
            <select id="scenario" className="intake-select" value={scenario} disabled={busy} onChange={event => setScenario(event.target.value)}>{scenarios.map(item => <option key={item.id} value={item.id}>{item.title}</option>)}</select>
            <p className="format-help">{scenarios.find(item => item.id === scenario).description} Select a case, then load it below.</p>
            <div className="input-actions"><button type="button" className="secondary" disabled={busy} onClick={loadScenario}>↳ Load sample</button><button type="button" className="text-button" disabled={busy} onClick={() => upload.current.click()}>↑ Upload file</button></div>
            <input ref={upload} className="sr-only" type="file" accept=".txt,.log,text/plain" onChange={readFile} disabled={busy} aria-label="Upload security logs" />
            <label className="field-label" htmlFor="logs">Security logs <span>TXT / LOG</span></label>
            <textarea id="logs" spellCheck="false" value={logs} maxLength={MAX_LOG_LENGTH} disabled={busy} onChange={event => { setLogs(event.target.value); setFileName(''); }} placeholder={'EVT001 | 2026-10-28T02:12:00Z |\nPERMISSION_CHANGE | user=admin |\nrole=administrator'} />
            <div className="editor-footer"><span>{fileName || 'Paste pipe-separated events'}</span><span>{logs.length.toLocaleString()} / 20,000</span></div>
            <p className="format-help">One event per line. Include an ID, timestamp with timezone, event type and key=value fields.</p>
            {mode === 'adaptive' && <details className="change-intake"><summary>Supplied change records · JSON</summary><p className="format-help">Optional approval context. Only exact actor, target, role and time matches count. These records are not independently authenticated.</p><label className="sr-only" htmlFor="changes">Change records JSON</label><textarea id="changes" value={changeText} maxLength={20000} disabled={busy} onChange={event => setChangeText(event.target.value)} /></details>}
            {mode === 'adaptive' && <details><summary>Witness statement · optional</summary><p className="format-help">Upload a synthetic voice note (mono PCM WAV, 16/24 kHz, up to 60 seconds) or type a statement. Audio is sent to Meta for transcription. Review its wording before starting. Testimony cannot establish identity or authorization.</p><input type="file" accept=".wav,audio/wav" disabled={busy || voiceBusy} onChange={transcribe} aria-label="Upload witness WAV" />{voiceBusy && <p role="status">{witnessChecking ? 'Checking witness claims…' : 'Transcribing voice note…'}</p>}{voiceNotice && <p className="format-help">{voiceNotice}</p>}<label className="field-label" htmlFor="witness">Review witness statement</label><textarea id="witness" maxLength={4000} value={witness} disabled={busy || voiceBusy} onChange={e => setWitness(e.target.value)} /><button type="button" className="secondary" disabled={busy || voiceBusy || !logs.trim() || !witness.trim()} onClick={checkWitnessOnly}>Check witness only</button><p className="format-help">Checks the current statement against the current logs and supplied records. Makes one AI call; does not rerun the log investigation.</p>{witnessError && <p role="alert">{witnessError}</p>}</details>}
            <button className="primary" disabled={busy || voiceBusy || !logs.trim()} type="submit">{busy ? <><span className="spinner" />Investigating evidence…</> : <>Start investigation <span>↗</span></>}</button>
            {busy && <button type="button" className="cancel" onClick={() => active.current?.abort()}>Cancel request</button>}
            <p className="privacy">Logs are sent to Meta for analysis. Use synthetic data for your demo. API keys stay in your backend.</p>
          </form>
      </div></details>
      {error && <div className="error" role="alert">{error}</div>}
      {witnessError && !intakeOpen && <div className="error" role="alert">{witnessError}</div>}
      {!witnessReview && result?.testimony_error && <p className="error" role="status">{result.testimony_error}</p>}
      <WitnessPanel testimony={testimony} separate={!!witnessReview} />
      <CaseConsole result={result} liveEvents={liveEvents} liveTools={liveTools} busy={busy} />
      <footer><span>PHANTOMTRACE / EVIDENCE INTO INSIGHT</span><span>Model assessments need human review. Records are supplied context, not authenticated authorization.</span></footer>
    </main>
  </div>;
}
createRoot(document.getElementById('root')).render(<App />);
