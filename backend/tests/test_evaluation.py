import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from evaluate_adaptive import evaluate, error_details
from test_adaptive_agent import CASES, report, finding


class TestEvaluation(unittest.TestCase):
    def test_failed_run_is_counted_and_not_silently_retried(self):
        case=next(c for c in CASES if c['id']=='ambiguous')
        calls=[]
        def runner(request):
            calls.append(request)
            if len(calls)==1:
                raise RuntimeError('credential-do-not-export')
            return {'report':report(finding('AMB001')),'model':'mock-test-model',
                    'metrics':{'elapsed_seconds':1},'tool_history':[],
                    'claim_verification':{'all_valid':True}}
        output=evaluate([case],live=True,repeats=2,runner=runner)
        self.assertEqual(len(calls),2)
        self.assertEqual(output['summary']['completed_runs'],1)
        self.assertEqual(output['summary']['failed_runs'],1)
        self.assertEqual(output['summary']['total_targets'],2)
        self.assertEqual(output['summary']['adaptive_matched_targets'],1)
        self.assertNotIn('credential-do-not-export',json.dumps(output))
        self.assertEqual([item['run'] for item in output['cases']],[1,2])

    def test_offline_mode_never_contacts_model(self):
        def runner(request):
            self.fail('No provider calls permitted in offline mode')
        output=evaluate(CASES,live=False,runner=runner)
        self.assertEqual(output['summary']['total_targets'],8)
        self.assertEqual(output['summary']['baseline_matched_targets'],5)
        self.assertNotIn('adaptive_matched_targets',output['summary'])
        self.assertTrue(all('NOT RUN' in item['adaptive'] for item in output['cases']))

    def test_unknown_failure_does_not_print_exception_message(self):
        value=error_details(ValueError('private-token-or-evidence'))
        self.assertEqual(value['error_code'],'unexpected_error')
        self.assertNotIn('private-token',json.dumps(value))
