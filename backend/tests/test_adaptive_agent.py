import json
from pathlib import Path
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch
import httpx
from openai import APITimeoutError

from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.tools.event_correlator import correlate_events
from app.services.adaptive_agent import (
    AdaptiveRequest, AdaptiveReport, EvidenceWorkspace, Fact, Sequence,
    Query, Inspect, ChangeLookup, investigate_adaptive,
    AdaptiveFailure,
)
from test_investigation_agent import call, response, client_for


CASES = json.loads((Path(__file__).resolve().parents[2] /
                   'frontend/src/scenarios.json').read_text(encoding='utf-8'))


def request(case_id):
    case = next(case for case in CASES if case['id'] == case_id)
    return AdaptiveRequest(logs=case['logs'], changes=case['changes'])


def finding(eid, disposition='unresolved', change_ids=None):
    return {'type': 'PERMISSION_CHANGE_REVIEW', 'description': 'A permission change needs context.',
            'disposition': disposition, 'event_ids': [eid],
            'facts': [{'event_id': eid, 'field': 'event_type', 'value': 'PERMISSION_CHANGE'}],
            'sequences': [], 'alternative_explanation': 'This may be authorized maintenance.',
            'next_check': 'Verify actor identity and authorization with the system owner.',
            'change_ids': change_ids or []}


def report(*findings):
    return {'summary': 'Investigated the supplied evidence; conclusions require review.',
            'findings': list(findings), 'recommendations': ['Verify authorization.'],
            'limitations': ['Supplied record authenticity and narrative interpretations are not verified.'],
            'handoff': {'situation': 'Permission activity requires review.',
                        'evidence_scope': 'Only the supplied synthetic records were inspected.',
                        'next_actions': ['Ask the system owner to verify authorization.'],
                        'open_questions': ['Who controlled the account?']}}


class TestAdaptiveWorkspace(unittest.TestCase):
    def test_exact_record_match_does_not_clear_other_account(self):
        ws = EvidenceWorkspace(request('mixed'))
        match = ws.lookup(ChangeLookup(event_id='EVT005', purpose='Check authorization scope'))
        other = ws.lookup(ChangeLookup(event_id='EVT008', purpose='Check the other change'))
        self.assertEqual(match['matching_records'][0]['change_id'], 'CHG-1042')
        self.assertEqual(other['matching_records'], [])

    def test_wrong_target_revoked_and_out_of_window_do_not_match(self):
        self.assertFalse(EvidenceWorkspace(request('mismatch')).lookup(
            ChangeLookup(event_id='MIS001', purpose='Check target'))['matching_records'])
        for updates in [{'status':'revoked'}, {'starts_at':'2026-10-28T03:00:00Z',
                                              'ends_at':'2026-10-28T04:00:00Z'},
                        {'actor':'different'}, {'role':'reader'}]:
            req = request('documented').model_dump()
            req['changes'][0].update(updates)
            ws = EvidenceWorkspace(AdaptiveRequest.model_validate(req))
            self.assertEqual(ws.lookup(ChangeLookup(event_id='BEN002', purpose='Check record'))['matching_records'], [])

    def test_filters_intersect_and_pagination_reports_omissions(self):
        ws = EvidenceWorkspace(request('mixed'))
        result = ws.query(Query(user='admin', ip='203.0.113.45', limit=2, purpose='Follow this account'))
        self.assertEqual([e['event_id'] for e in result['events']], ['EVT001','EVT002'])
        self.assertTrue(result['truncated'])
        self.assertEqual(result['next_offset'], 2)
        second = ws.query(Query(user='admin', ip='203.0.113.45', offset=2, purpose='Inspect the next page'))
        self.assertEqual([e['event_id'] for e in second['events']], ['EVT003','EVT004'])
        window = ws.query(Query(starts_at='2026-10-28T10:14:00+08:00',
                                ends_at='2026-10-28T10:15:00+08:00', purpose='Inspect a time window'))
        self.assertEqual([e['event_id'] for e in window['events']], ['EVT008','EVT009'])

    def test_fabricated_facts_and_reversed_timing_fail(self):
        ws = EvidenceWorkspace(request('mixed'))
        result = ws.check([Fact(event_id='EVT001',field='user',value='someone-else')],
                          [Sequence(earlier_id='EVT004',later_id='EVT001',max_seconds=60)])
        self.assertFalse(result['all_valid'])
        self.assertTrue(all(not check['valid'] for check in result['checks']))
        self.assertFalse(ws.check([Fact(event_id='FAKE',field='user',value='admin')], [])['all_valid'])
        self.assertTrue(ws.check([Fact(event_id='EVT001',field='timestamp',value='2026-10-28T10:10:00+08:00')], [])['all_valid'])

    def test_cannot_explain_without_a_matching_lookup(self):
        ws = EvidenceWorkspace(request('documented'))
        ws.inspect(Inspect(event_ids=['BEN002'], purpose='Inspect change'))
        value = AdaptiveReport.model_validate(report(finding('BEN002','explained_by_record',['CHG-2001'])))
        with self.assertRaisesRegex(ValueError, 'matching change record'):
            ws.validate_report(value)
        ws.lookup(ChangeLookup(event_id='BEN002',purpose='Check matching record'))
        self.assertTrue(ws.validate_report(value)['all_valid'])

    def test_cannot_cite_uninspected_evidence_or_omit_a_lead(self):
        ws = EvidenceWorkspace(request('mixed'))
        with self.assertRaisesRegex(ValueError, 'did not inspect'):
            ws.validate_report(AdaptiveReport.model_validate(report(finding('EVT008'))))
        ws.inspect(Inspect(event_ids=['EVT008'],purpose='Inspect one lead'))
        with self.assertRaisesRegex(ValueError, 'omits evidence'):
            ws.validate_report(AdaptiveReport.model_validate(report(finding('EVT008'))))

    def test_injection_stays_data_and_tools_cannot_replace_evidence(self):
        ws = EvidenceWorkspace(request('injection'))
        _, result = ws.execute('inspect_events', {'event_ids':['INJ001'],'purpose':'Inspect source'})
        self.assertIn('Ignore previous instructions', result['events'][0]['fields']['note'])
        with self.assertRaises(ValueError):
            ws.execute('run_shell', {'command':'anything'})
        with self.assertRaises(ValidationError):
            ws.execute('query_events', {'purpose':'Replace source', 'logs':'fake'})
        self.assertEqual(ws.by_id['INJ001']['fields']['target'], 'finance_service')

    def test_invalid_windows_and_duplicate_records_rejected(self):
        with self.assertRaises(ValidationError):
            Query(purpose='Search', starts_at='2026-10-28T02:00:00')
        with self.assertRaises(ValidationError):
            Query(purpose='Search', starts_at='2026-10-28T03:00:00Z', ends_at='2026-10-28T02:00:00Z')
        req = request('documented').model_dump()
        req['changes'] *= 2
        with self.assertRaises(ValidationError):
            AdaptiveRequest.model_validate(req)

    def test_mixed_timezone_order_is_by_instant(self):
        logs = ('LATE | 2026-10-28T01:00:00Z | LOGIN_SUCCESS | user=admin\n'
                'EARLY | 2026-10-28T08:00:00+08:00 | LOGIN_FAILED | user=admin')
        self.assertEqual([e['event_id'] for e in EvidenceWorkspace(AdaptiveRequest(logs=logs)).events], ['EARLY','LATE'])

    def test_correlation_does_not_miss_failures_in_a_different_offset(self):
        logs = '\n'.join(f'F{i} | 2026-10-28T08:00:{i:02d}+08:00 | LOGIN_FAILED | user=admin | ip=192.0.2.1' for i in range(3))
        logs += '\nS1 | 2026-10-28T00:00:30Z | LOGIN_SUCCESS | user=admin | ip=192.0.2.1'
        ws=EvidenceWorkspace(AdaptiveRequest(logs=logs))
        self.assertEqual(correlate_events(ws.events)['finding_count'],1)

    def test_source_observations_distinguish_actor_target_and_unchecked_prose(self):
        ws = EvidenceWorkspace(request('mixed'))
        item = finding('EVT005')
        item['description'] = 'Incorrect assessment: admin received the role five seconds after a login.'
        checked = ws.source_observations(AdaptiveReport.model_validate(report(item)).findings[0])
        self.assertIn('actor (user)="admin"',checked[0]['text'])
        self.assertIn('target="backup_service"',checked[0]['text'])
        self.assertNotIn('received',checked[0]['text'])
        self.assertNotIn('seconds',checked[0]['text'])

    def test_checked_timing_observation_references_both_events(self):
        ws = EvidenceWorkspace(request('mixed'))
        item = finding('EVT005')
        item['event_ids'].append('EVT006')
        item['facts'].append({'event_id':'EVT006','field':'event_type','value':'FILE_READ'})
        item['sequences']=[{'earlier_id':'EVT005','later_id':'EVT006','max_seconds':10}]
        checked=ws.source_observations(AdaptiveReport.model_validate(report(item)).findings[0])
        self.assertEqual(checked[-1]['event_ids'],['EVT005','EVT006'])
        self.assertEqual(checked[-1]['text'],'EVT005 occurred 5 seconds before EVT006.')


class TestAdaptiveLoop(unittest.TestCase):
    def test_different_tool_paths_and_dispositions_supported(self):
        # Scripted provider outputs verify branching mechanics, NOT live model intelligence.
        approved = client_for(
            response([call('inspect_events',json.dumps({'event_ids':['BEN002'],'purpose':'Inspect the change'}))]),
            response([call('lookup_change',json.dumps({'event_id':'BEN002','purpose':'Does this match maintenance?'}))]),
            response(report=report(finding('BEN002','explained_by_record',['CHG-2001']))))
        missing = client_for(
            response([call('query_events',json.dumps({'user':'operator','purpose':'Find account activity'}))]),
            response(report=report(finding('AMB001'))))
        first = investigate_adaptive(request('documented'),client=approved)
        second = investigate_adaptive(request('ambiguous'),client=missing)
        self.assertNotEqual([e['tool'] for e in first['tool_history']], [e['tool'] for e in second['tool_history']])
        self.assertEqual(first['report']['findings'][0]['disposition'],'explained_by_record')
        self.assertEqual(second['report']['findings'][0]['disposition'],'unresolved')
        self.assertTrue(first['claim_verification']['all_valid'])
        self.assertEqual(first['tool_history'][1]['purpose'],'Does this match maintenance?')
        observation=first['report']['findings'][0]['source_observations'][0]
        self.assertEqual(observation['event_ids'],['BEN002'])
        self.assertIn('target="backup"',observation['text'])

    def test_failed_claim_can_be_repaired_but_never_returned_as_valid(self):
        invalid = report(finding('AMB001'))
        invalid['findings'][0]['facts'][0]['value']='LOGIN_FAILED'
        client = client_for(response([call('inspect_events',json.dumps({'event_ids':['AMB001'],'purpose':'Inspect change'}))]),
                            response(report=invalid), response(report=report(finding('AMB001'))))
        result = investigate_adaptive(request('ambiguous'),client=client)
        self.assertTrue(result['claim_verification']['all_valid'])
        repair = client.responses.create.call_args_list[2].kwargs
        self.assertIn('rejected by evidence checks',repair['input'][0]['content'])
        self.assertEqual(repair['previous_response_id'],'response-id')

    def test_early_final_has_bounded_retries(self):
        client = client_for(response(report=report()),response(report=report()))
        with self.assertRaisesRegex(RuntimeError,'turn budget'):
            investigate_adaptive(request('ambiguous'),client=client,max_turns=2)

    def test_failed_run_explains_budget_without_raw_report(self):
        client=client_for(response(report={'secret':'do-not-export'}),response(report={}))
        with self.assertRaises(AdaptiveFailure) as caught:
            investigate_adaptive(request('ambiguous'),client=client,max_turns=2)
        self.assertEqual(caught.exception.code,'turn_budget_exceeded')
        self.assertEqual(caught.exception.diagnostics['model_turns'],2)
        self.assertEqual(caught.exception.diagnostics['report_rejections'],['source_not_inspected']*2)
        self.assertNotIn('do-not-export',json.dumps(caught.exception.diagnostics))

    def test_timeout_preserves_tool_path_without_provider_message(self):
        client=client_for(response([call('inspect_events',json.dumps({'event_ids':['AMB001'],'purpose':'Inspect source'}))]),
                          APITimeoutError(request=httpx.Request('POST','https://example.test/private-token')))
        with self.assertRaises(AdaptiveFailure) as caught:
            investigate_adaptive(request('ambiguous'),client=client)
        self.assertEqual(caught.exception.code,'provider_timeout')
        self.assertEqual(caught.exception.diagnostics['tool_path'],['inspect_events'])
        self.assertNotIn('private-token',json.dumps(caught.exception.diagnostics))

    def test_incomplete_output_is_not_accepted_as_report(self):
        partial=response(report=report())
        partial.status='incomplete'
        partial.incomplete_details=NS(reason='max_output_tokens')
        client=client_for(partial)
        with self.assertRaises(AdaptiveFailure) as caught:
            investigate_adaptive(request('ambiguous'),client=client)
        self.assertEqual(caught.exception.code,'model_output_limit')
        self.assertEqual(client.responses.create.call_count,1)

    def test_schema_diagnostics_keep_field_paths_without_inputs_or_unknown_keys(self):
        value=report(finding('AMB001'))
        value['findings'][0]['disposition']='private-value'
        value['private-field']='private-value'
        client=client_for(response([call('inspect_events',json.dumps({'event_ids':['AMB001'],'purpose':'Inspect source'}))]),
                          response(report=value))
        with self.assertRaises(AdaptiveFailure) as caught:
            investigate_adaptive(request('ambiguous'),client=client,max_turns=2)
        issues=caught.exception.diagnostics['validation_issues']
        self.assertTrue(any(item['field']=='findings.#.disposition' for item in issues))
        self.assertNotIn('private-',json.dumps(caught.exception.diagnostics))

    def test_invalid_tool_can_recover(self):
        client = client_for(response([call('shell','{}')]),
                            response([call('inspect_events',json.dumps({'event_ids':['AMB001'],'purpose':'Inspect source'}))]),
                            response(report=report(finding('AMB001'))))
        result=investigate_adaptive(request('ambiguous'),client=client)
        self.assertIn('error',result['tool_history'][0]['result'])

    def test_api_validation_and_sanitized_provider_failure(self):
        api=TestClient(app)
        self.assertEqual(api.post('/api/investigate/adaptive',json={'logs':'bad'}).status_code,422)
        with patch('app.main.investigate_adaptive',side_effect=RuntimeError('private-token')):
            result=api.post('/api/investigate/adaptive',json=request('ambiguous').model_dump())
        self.assertEqual(result.status_code,502)
        self.assertNotIn('private-token',result.text)
