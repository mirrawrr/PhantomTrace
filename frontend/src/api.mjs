export const MAX_LOG_LENGTH = 20000;
export const SAMPLE_LOGS = `EVT001 | 2026-10-28T02:10:00Z | LOGIN_FAILED | user=admin | ip=203.0.113.45
EVT002 | 2026-10-28T02:10:08Z | LOGIN_FAILED | user=admin | ip=203.0.113.45
EVT003 | 2026-10-28T02:10:15Z | LOGIN_FAILED | user=admin | ip=203.0.113.45
EVT004 | 2026-10-28T02:11:00Z | LOGIN_SUCCESS | user=admin | ip=203.0.113.45
EVT005 | 2026-10-28T02:12:00Z | PERMISSION_CHANGE | user=admin | target=backup_service | role=administrator`;

export function validateLogs(logs) {
  if (!logs.trim()) throw new Error('Add security logs before starting an investigation.');
  if (logs.length > MAX_LOG_LENGTH) throw new Error('Logs must contain 20,000 characters or fewer.');
}

export async function readJsonResponse(response) {
  try { return await response.json(); }
  catch (error) {
    if (error.name === 'AbortError') throw error;
    const status = Number.isInteger(response.status) ? ` (HTTP ${response.status})` : '';
    throw new Error(`The backend returned an empty or unreadable response${status}. Check that the backend is running and inspect its terminal before retrying.`);
  }
}

export async function investigate(logs, { signal, fetcher = fetch, mode = 'adaptive', changes = [], witnessStatement = '', authorization = '', onEvent } = {}) {
  validateLogs(logs);
  const streaming = mode === 'adaptive' && typeof onEvent === 'function';
  const response = await fetcher(mode === 'adaptive' ? `/api/investigate/adaptive${streaming ? '/stream' : ''}` : '/api/investigate/agent', {
    method: 'POST', headers: { 'Content-Type': 'application/json', ...(authorization ? { Authorization: authorization } : {}) },
    body: JSON.stringify(mode === 'adaptive' ? { logs, changes, ...(witnessStatement.trim() ? { witness_statement: witnessStatement } : {}) } : { logs }), signal,
  });
  const data = streaming && response.ok ? await readInvestigationStream(response, onEvent) : await readJsonResponse(response);
  if (!response.ok) {
    if (response.status === 401) throw new Error('Live investigation requires demo credentials. Enter the testing credentials or use recorded replay.');
    if (response.status === 429) throw new Error('Live demo allowance reached. Use recorded replay or return later.');
    if (response.status === 422) {
      const errors = data?.detail?.errors;
      throw new Error(Array.isArray(errors) ? errors.join('\n') : 'The backend rejected these logs. Check the event format and timestamps.');
    }
    throw new Error(response.status === 502
      ? 'The AI investigation could not finish (HTTP 502). Inspect the backend terminal before retrying.'
      : `Investigation failed (HTTP ${response.status}). Inspect the backend terminal before retrying.`);
  }
  if (!data || data.status !== 'completed' || !data.report ||
      typeof data.report.summary !== 'string' ||
      !Array.isArray(data.report.findings) || !Array.isArray(data.report.recommendations) ||
      !Array.isArray(data.report.limitations) || !Array.isArray(data.events) ||
      !Array.isArray(data.tool_history) || !Array.isArray(data.verification?.results)) {
    throw new Error('The backend response does not match the investigation format. Update the backend and retry.');
  }
  return data;
}

export async function readInvestigationStream(response, onEvent) {
  if (!response.body || !response.headers.get('content-type')?.includes('text/event-stream')) {
    throw new Error('Live activity stream unavailable. Refresh after deploying the matching backend.');
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '', finalResult;
  function consume(frame) {
    const lines = frame.split('\n');
    const event = lines.find(line => line.startsWith('event:'))?.slice(6).trim();
    const payload = lines.filter(line => line.startsWith('data:')).map(line => line.slice(5).trimStart()).join('\n');
    if (!payload || !['workspace', 'tool', 'result', 'error'].includes(event)) return;
    let data;
    try { data = JSON.parse(payload); }
    catch { throw new Error('The activity stream contained an incomplete or unreadable frame. Completed activity is retained; no final verdict is available.'); }
    if (!data || typeof data !== 'object') throw new Error('The activity stream returned an invalid frame. No final verdict is available.');
    if (event === 'error') {
      const known = new Set(['invalid_logs','budget_unavailable','provider_timeout','provider_connection','provider_authentication','provider_rate_limit','provider_http_error','provider_error','model_output_limit','model_response_incomplete','tool_budget_exceeded','turn_budget_exceeded','investigation_failed']);
      const provider = data.provider || {};
      const labels = new Set(['invalid_request_error','invalid_api_key','insufficient_quota','context_length_exceeded','model_not_found','rate_limit_exceeded','server_error','permission_denied','unsupported_parameter','invalid_parameter','invalid_value']);
      const info = [known.has(data.code) ? data.code : 'stream_failed'];
      if (Number.isInteger(provider.http_status) && provider.http_status >= 400 && provider.http_status <= 599) info.push(`HTTP ${provider.http_status}`);
      if (labels.has(provider.provider_code)) info.push(provider.provider_code);
      else if (labels.has(provider.provider_type)) info.push(provider.provider_type);
      if (['model','input','instructions','previous_response_id','tools','max_output_tokens'].includes(provider.parameter)) info.push(`field: ${provider.parameter}`);
      throw new Error(`Investigation did not finish (${info.join(' · ')}). Completed tool activity is retained; no final verdict is available.`);
    }
    if (event === 'result') finalResult = data;
    else onEvent(event, data);
  }
  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      buffer = buffer.replaceAll('\r\n', '\n');
      let boundary;
      while ((boundary = buffer.indexOf('\n\n')) >= 0) {
        consume(buffer.slice(0, boundary)); buffer = buffer.slice(boundary + 2);
      }
      if (done) break;
    }
    if (!finalResult) throw new Error('Connection ended before the final report. Completed activity is retained; no final verdict is available.');
    return finalResult;
  } finally { await reader.cancel().catch(() => {}); reader.releaseLock(); }
}

export function filterEvents(events, query, type) {
  const search = query.toLowerCase().trim();
  return events.filter(event => (type === 'ALL' || event.event_type === type) &&
    [event.event_id, event.event_type, event.user, event.ip, event.raw]
      .some(value => String(value ?? '').toLowerCase().includes(search)))
    .sort((a, b) => Date.parse(a.timestamp) - Date.parse(b.timestamp));
}

export function utcTime(timestamp) {
  const date = new Date(timestamp);
  return Number.isNaN(date.getTime()) ? timestamp : date.toISOString().replace('T', ' ').replace('.000Z', ' UTC');
}
