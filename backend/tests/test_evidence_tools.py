
import unittest

from app.tools.log_parser import parse_security_logs
from app.tools.event_correlator import correlate_events
from app.tools.evidence_verifier import verify_evidence


# Synthetic security logs for testing PhantomTrace
SAMPLE_LOGS = """
EVT001 | 2026-10-28T02:10:00Z | LOGIN_FAILED | user=admin | ip=203.0.113.45
EVT002 | 2026-10-28T02:10:08Z | LOGIN_FAILED | user=admin | ip=203.0.113.45
EVT003 | 2026-10-28T02:10:15Z | LOGIN_FAILED | user=admin | ip=203.0.113.45
EVT004 | 2026-10-28T02:11:00Z | LOGIN_SUCCESS | user=admin | ip=203.0.113.45
EVT005 | 2026-10-28T02:12:00Z | PERMISSION_CHANGE | user=admin | target=backup_service | role=administrator
"""


class TestEvidenceTools(unittest.TestCase):

    # Test 1: Parse valid security logs
    def test_parse_valid_logs(self):
        result = parse_security_logs(SAMPLE_LOGS)

        self.assertEqual(result["total_events"], 5)
        self.assertEqual(result["errors"], [])
        self.assertEqual(len(result["events"]), 5)

    # Test 2: Reject invalid timestamps
    def test_reject_invalid_timestamp(self):
        logs = (
            "EVT006 | invalid-date | LOGIN_FAILED | "
            "user=admin | ip=203.0.113.45"
        )

        result = parse_security_logs(logs)

        self.assertEqual(result["total_events"], 0)
        self.assertTrue(result["errors"])

    # Test 3: Reject duplicate event IDs
    def test_reject_duplicate_ids(self):
        logs = """
EVT001 | 2026-10-28T02:10:00Z | LOGIN_FAILED | user=admin
EVT001 | 2026-10-28T02:11:00Z | LOGIN_SUCCESS | user=admin
"""

        result = parse_security_logs(logs)

        self.assertEqual(result["total_events"], 1)
        self.assertTrue(result["errors"])

    # Test 4: Detect suspicious authentication sequence
    def test_detect_suspicious_sequence(self):
        parsed = parse_security_logs(SAMPLE_LOGS)
        result = correlate_events(parsed["events"])

        self.assertEqual(result["event_count"], 5)
        self.assertEqual(result["finding_count"], 2)

        finding_types = [
            finding["type"]
            for finding in result["findings"]
        ]

        self.assertIn(
            "FAILED_LOGINS_THEN_SUCCESS",
            finding_types
        )
        self.assertIn(
            "PERMISSION_CHANGE_REVIEW",
            finding_types
        )

    # Test 5: Verify legitimate evidence references
    def test_verify_valid_evidence_ids(self):
        parsed = parse_security_logs(SAMPLE_LOGS)
        events = parsed["events"]

        correlation = correlate_events(events)

        result = verify_evidence(
            events,
            correlation["findings"]
        )

        self.assertEqual(result["total_findings"], 2)
        self.assertEqual(result["verified_references"], 2)

        for verification in result["results"]:
            self.assertTrue(
                verification["references_valid"]
            )

    # Test 6: Detect non-existent evidence references
    def test_detect_invalid_evidence_id(self):
        parsed = parse_security_logs(SAMPLE_LOGS)

        fake_findings = [
            {
                "type": "TEST_FINDING",
                "event_ids": ["EVT999"]
            }
        ]

        result = verify_evidence(
            parsed["events"],
            fake_findings
        )

        self.assertEqual(
            result["verified_references"], 0
        )
        self.assertFalse(
            result["results"][0]["references_valid"]
        )
        self.assertIn(
            "EVT999",
            result["results"][0]["missing_ids"]
        )


if __name__ == "__main__":
    unittest.main()
