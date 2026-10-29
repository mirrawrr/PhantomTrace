import json
import unittest
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from app.main import app
from app.services.investigation_agent import investigate_agent, InvalidLogs
from test_evidence_tools import SAMPLE_LOGS


def call(name, arguments="{}"):
    return NS(type="function_call", name=name, arguments=arguments, call_id=name)


def response(calls=(), report=None):
    return NS(id="response-id", output=list(calls), output_text=json.dumps(report))


REPORT = {"summary": "Permission change needs review.", "findings": [
    {"type": "REVIEW", "description": "Permission changed", "event_ids": ["EVT005"]}],
    "recommendations": ["Confirm authorization"],
    "limitations": ["References establish existence, not truth."]}


def client_for(*responses):
    client = Mock()
    client.responses.create.side_effect = responses
    return client


class TestAgent(unittest.TestCase):
    def test_full_loop_and_context(self):
        client = client_for(response([call("parse_logs")]),
                            response([call("correlate_events"), call("verify_evidence")]),
                            response(report=REPORT))
        result = investigate_agent(SAMPLE_LOGS, client=client)
        self.assertEqual(result["verification"]["verified_references"], 1)
        self.assertEqual(len(result["tool_history"]), 3)
        continuation = client.responses.create.call_args_list[1].kwargs
        self.assertEqual(continuation["previous_response_id"], "response-id")
        self.assertEqual(continuation["input"][0]["call_id"], "parse_logs")
        self.assertEqual(len(client.responses.create.call_args_list[2].kwargs["input"]), 2)

    def test_rejects_fabricated_final_reference(self):
        report = dict(REPORT, findings=[dict(REPORT["findings"][0], event_ids=["FAKE"])])
        client = client_for(response([call("parse_logs"), call("correlate_events"),
                                     call("verify_evidence")]), response(report=report))
        with self.assertRaisesRegex(RuntimeError, "invalid evidence"):
            investigate_agent(SAMPLE_LOGS, client=client)

    def test_invalid_logs_do_not_contact_model(self):
        client = Mock()
        with self.assertRaises(InvalidLogs):
            investigate_agent("invalid", client=client)
        client.responses.create.assert_not_called()

    def test_early_final_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "before evidence"):
            investigate_agent(SAMPLE_LOGS, client=client_for(response(report=REPORT)))

    def test_invalid_report_rejected(self):
        client = client_for(response([call("parse_logs"), call("correlate_events"),
                                     call("verify_evidence")]), response(report={}))
        with self.assertRaisesRegex(RuntimeError, "invalid report"):
            investigate_agent(SAMPLE_LOGS, client=client)

    def test_tool_errors_and_turn_limit(self):
        client = client_for(response([call("correlate_events"), call("shell"),
                                     call("parse_logs", "not-json")]))
        with self.assertRaisesRegex(RuntimeError, "turn limit"):
            investigate_agent(SAMPLE_LOGS, client=client, max_turns=1)

    def test_recovers_from_invalid_arguments(self):
        client = client_for(response([call("parse_logs", '{"logs":"replacement"}')]),
                            response([call("parse_logs"), call("correlate_events"),
                                      call("verify_evidence")]), response(report=REPORT))
        result = investigate_agent(SAMPLE_LOGS, client=client)
        self.assertIn("error", result["tool_history"][0]["result"])
        self.assertEqual(len(result["events"]), 5)

    def test_per_turn_limit(self):
        with self.assertRaisesRegex(RuntimeError, "per-turn"):
            investigate_agent(SAMPLE_LOGS, client=client_for(response([call("parse_logs")] * 4)))

    def test_api_validation_and_sanitized_failure(self):
        api = TestClient(app)
        self.assertEqual(api.post("/api/investigate/agent", json={"logs": "bad"}).status_code, 422)
        with patch("app.main.investigate_agent", side_effect=RuntimeError("private-token")):
            result = api.post("/api/investigate/agent", json={"logs": SAMPLE_LOGS})
        self.assertEqual(result.status_code, 502)
        self.assertNotIn("private-token", result.text)

    def test_api_success(self):
        with patch("app.main.investigate_agent", return_value={"status": "completed"}):
            result = TestClient(app).post("/api/investigate/agent", json={"logs": SAMPLE_LOGS})
        self.assertEqual(result.status_code, 200)
