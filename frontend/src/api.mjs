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

export async function investigate(logs, { signal, fetcher = fetch } = {}) {
  validateLogs(logs);
  const response = await fetcher('/api/investigate/agent', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ logs }), signal,
  });
  let data;
  try { data = await response.json(); }
  catch { throw new Error('The backend returned an unreadable response. Check that FastAPI is running.'); }
  if (!response.ok) {
    if (response.status === 422) {
      const errors = data.detail?.errors;
      throw new Error(Array.isArray(errors) ? errors.join('\n') : 'The backend rejected these logs. Check the event format and timestamps.');
    }
    throw new Error(response.status === 502
      ? 'The AI investigation could not finish. Check the backend API key and configuration, then retry.'
      : `Investigation failed (HTTP ${response.status}). Please retry.`);
  }
  if (data.status !== 'completed' || !data.report ||
      typeof data.report.summary !== 'string' ||
      !Array.isArray(data.report.findings) || !Array.isArray(data.report.recommendations) ||
      !Array.isArray(data.report.limitations) || !Array.isArray(data.events) ||
      !Array.isArray(data.tool_history) || !Array.isArray(data.verification?.results)) {
    throw new Error('The backend response does not match the investigation format. Update the backend and retry.');
  }
  return data;
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
