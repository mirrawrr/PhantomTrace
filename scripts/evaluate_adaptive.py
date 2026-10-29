"""Opt-in live fixture evaluation; no performance claims without a measured run."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))

from app.services.adaptive_agent import AdaptiveRequest, investigate_adaptive
from app.tools.event_correlator import correlate_events
from app.tools.log_parser import parse_security_logs


def score(findings, expected):
    outcomes = {}
    for event_id, allowed in expected.items():
        related = [f.get('disposition','review') for f in findings if event_id in f['event_ids']]
        outcomes[event_id] = bool(related) and all(value in allowed for value in related)
    unjustified_explanations = sum(
        f.get('disposition') == 'explained_by_record' and
        any('explained_by_record' not in expected.get(eid,[]) for eid in f['event_ids'])
        for f in findings)
    return {'matched_targets':sum(outcomes.values()),'total_targets':len(outcomes),
            'unexpected_explained_findings':unjustified_explanations,'targets':outcomes}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live',action='store_true',help='Send synthetic cases to Meta using your local key; consumes API credits.')
    args=parser.parse_args()
    cases=json.loads((ROOT/'frontend/src/scenarios.json').read_text(encoding='utf-8'))
    output={'scope':'Small synthetic regression set measuring expected dispositions and coverage, not real-world accuracy or student learning. The rules-only baseline has no change-record matching; this comparison does not isolate model quality.',
            'live_model_run':args.live,'cases':[]}
    for case in cases:
        baseline=correlate_events(parse_security_logs(case['logs'])['events'])
        item={'id':case['id'],'fixed_rule_baseline':score(baseline['findings'],case['expected'])}
        if args.live:
            try:
                result=investigate_adaptive(AdaptiveRequest(logs=case['logs'],changes=case['changes']))
                item['adaptive']=score(result['report']['findings'],case['expected'])
                item['metrics']=result['metrics']
                item['tool_path']=[e['tool'] for e in result['tool_history']]
                item['structured_checks_valid']=result['claim_verification']['all_valid']
            except Exception:
                # Never echo provider errors or credentials into evaluation artifacts.
                item['adaptive']={'error':'Investigation failed; check local configuration or retry.'}
        else:
            item['adaptive']='NOT RUN: use --live to measure actual model behavior.'
        output['cases'].append(item)
    print(json.dumps(output,indent=2))


if __name__=='__main__':
    main()
