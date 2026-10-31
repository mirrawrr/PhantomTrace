"""Opt-in live fixture evaluation; preserve failures and never print provider secrets."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from time import monotonic

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))

from openai import OpenAIError
from pydantic import ValidationError
from app.services.adaptive_agent import AdaptiveFailure, AdaptiveRequest, investigate_adaptive, provider_failure_code
from app.services.investigation_agent import InvalidLogs
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


def error_details(exc):
    if isinstance(exc, AdaptiveFailure):
        return {'error':'Investigation failed.', 'error_code':exc.code, 'diagnostics':exc.diagnostics}
    if isinstance(exc, OpenAIError):
        code=provider_failure_code(exc)
    elif isinstance(exc, (ValidationError, InvalidLogs)):
        code='invalid_case_input'
    elif isinstance(exc, RuntimeError):
        code='configuration_or_runtime_error'
    else:
        code='unexpected_error'
    return {'error':'Investigation failed.', 'error_code':code}


def summarize(items, live):
    summary={'planned_runs':len(items),
             'baseline_matched_targets':sum(item['fixed_rule_baseline']['matched_targets'] for item in items),
             'total_targets':sum(item['fixed_rule_baseline']['total_targets'] for item in items)}
    if live:
        completed=[item for item in items if 'error' not in item['adaptive']]
        summary.update(completed_runs=len(completed), failed_runs=len(items)-len(completed),
                       adaptive_matched_targets=sum(item['adaptive']['matched_targets'] for item in completed),
                       unexpected_explained_findings=sum(item['adaptive']['unexpected_explained_findings'] for item in completed),
                       denominator_policy='Failed investigations remain in planned_runs and total_targets and contribute zero matched targets. No failed run is silently retried.')
    return summary


def evaluate(cases, *, live=False, repeats=1, runner=investigate_adaptive):
    output={'evaluation_version':2, 'started_at_utc':datetime.now(timezone.utc).isoformat(),
            'scope':'Small public synthetic regression set, not real-world accuracy or student learning. The rules-only baseline lacks change-record matching; this does not isolate model quality.',
            'live_model_run':live,'repeats':repeats,'cases':[]}
    for repeat in range(1,repeats+1):
        for case in cases:
            baseline=correlate_events(parse_security_logs(case['logs'])['events'])
            item={'id':case['id'],'run':repeat,'fixed_rule_baseline':score(baseline['findings'],case['expected'])}
            if live:
                start=monotonic()
                try:
                    result=runner(AdaptiveRequest(logs=case['logs'],changes=case['changes']))
                    item['adaptive']=score(result['report']['findings'],case['expected'])
                    item['model']=result['model']
                    item['metrics']=result['metrics']
                    item['tool_path']=[e['tool'] for e in result['tool_history']]
                    item['structured_checks_valid']=result['claim_verification']['all_valid']
                except Exception as exc:
                    item['adaptive']=error_details(exc)
                    item['failed_elapsed_seconds']=round(monotonic()-start,3)
            else:
                item['adaptive']='NOT RUN: use --live to measure actual model behavior.'
            output['cases'].append(item)
    output['summary']=summarize(output['cases'],live)
    return output


def main():
    cases=json.loads((ROOT/'frontend/src/scenarios.json').read_text(encoding='utf-8'))
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live',action='store_true',help='Send synthetic evidence to Meta; consumes API credits.')
    parser.add_argument('--case',action='append',choices=[case['id'] for case in cases],help='Evaluate only this case; repeat flag to select more.')
    parser.add_argument('--repeat',type=int,default=1,choices=range(1,6),help='Explicit repetitions (1-5); every attempt is retained and live repeats consume more credits.')
    args=parser.parse_args()
    selected=[case for case in cases if not args.case or case['id'] in args.case]
    output=evaluate(selected,live=args.live,repeats=args.repeat)
    print(json.dumps(output,indent=2))


if __name__=='__main__':
    main()
