export function disposition(finding) {
  return finding.disposition === 'explained_by_record' ? 'explained' : finding.disposition === 'unresolved' ? 'unresolved' : 'review';
}
export function verdictCounts(findings = []) {
  return findings.reduce((counts, f) => { counts[disposition(f)]++; return counts; }, { explained: 0, review: 0, unresolved: 0 });
}
export function eventVerdict(id, findings = []) {
  const attached = findings.filter(f => f.event_ids.includes(id)).map(disposition);
  return ['unresolved', 'review', 'explained'].find(value => attached.includes(value)) || 'neutral';
}
export function returnedEventIds(history = []) {
  return new Set(history.flatMap(entry => entry.result?.events?.map(e => e.event_id) || []));
}
export function toolSummary(entry) {
  const result = entry.result || {};
  if (result.error) return 'ERROR · inspect details';
  if (Array.isArray(result.events)) return `${result.events.length} events${result.truncated ? ' · more available' : ''}`;
  if (Array.isArray(result.matching_records)) return result.matching_records.length ? `${result.matching_records.map(r => r.change_id).join(', ')} MATCH · supplied` : 'NO SUPPLIED MATCH';
  if (typeof result.all_valid === 'boolean') return result.all_valid ? 'PASS · structured checks' : 'CHECK FAILED';
  return 'RETURNED · inspect details';
}
export function nextSteps(report) {
  const actions = report.handoff?.next_actions?.length ? report.handoff.next_actions : report.recommendations || [];
  return [...new Set(actions.map(s => s.trim()).filter(Boolean))];
}
