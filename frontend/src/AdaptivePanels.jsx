import React from 'react';

export function AdaptiveFindingDetails({ finding }) {
  if (!finding.disposition) return null;
  return <div className="adaptive-details">
    <p className={`disposition disposition-${finding.disposition}`}>{finding.disposition === 'explained_by_record' ? 'Explained by supplied record · not independently authenticated' : finding.disposition === 'unresolved' ? 'Unresolved · more evidence needed' : 'Requires analyst review'}</p>
    <dl><dt>Another explanation</dt><dd>{finding.alternative_explanation}</dd><dt>Next evidence to collect</dt><dd>{finding.next_check}</dd></dl>
    {!!finding.change_ids?.length && <p className="muted">Matching supplied records: {finding.change_ids.join(', ')}</p>}
    <details className="fact-details"><summary>Inspect checked facts and timing</summary><ul>{finding.facts.map((fact,index) => <li key={index}><code>{fact.event_id}</code> · {fact.field} = <code>{fact.value}</code></li>)}{finding.sequences.map((sequence,index) => <li key={`sequence-${index}`}><code>{sequence.earlier_id}</code> precedes <code>{sequence.later_id}</code> within {sequence.max_seconds}s</li>)}</ul></details>
  </div>;
}

export function HandoffPanel({ result }) {
  const handoff = result.report.handoff;
  if (!handoff) return null;
  const steps = result.tool_history.filter(entry => !entry.result?.error);
  return <>
    <section className="panel handoff-panel"><p className="eyebrow">ANALYST HANDOFF · DRAFT FOR HUMAN REVIEW</p><h3>What to tell the next analyst</h3><p>{handoff.situation}</p><h4>Evidence scope</h4><p>{handoff.evidence_scope}</p><div className="report-bottom"><div><h4>Next actions</h4><ul>{handoff.next_actions.map((text,index) => <li key={index}>{text}</li>)}</ul></div><div><h4>Still unknown</h4><ul>{handoff.open_questions.map((text,index) => <li key={index}>{text}</li>)}</ul></div></div></section>
    <section className="panel investigation-path"><p className="eyebrow">HOW THE INVESTIGATION PROCEEDED</p><p className="muted">Short questions supplied with actual tool calls. These explain the investigation steps; they are not private model reasoning.</p><ol>{steps.map((step,index) => <li key={index}><strong>{step.purpose}</strong><small>{step.tool} · {step.result.events ? `${step.result.events.length} events returned` : step.result.matching_records ? `${step.result.matching_records.length} matching records` : step.result.all_valid ? 'Structured checks passed' : 'Structured checks require review'}</small></li>)}</ol></section>
  </>;
}
