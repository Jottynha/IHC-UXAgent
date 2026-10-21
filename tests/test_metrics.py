from __future__ import annotations

import unittest

from metrics import summarize_session, summarize_sessions


class MetricsTests(unittest.TestCase):
    def test_success_keeps_recovered_error_and_counts_support(self):
        records = [
            {"event": "action_executed", "error": {"category": "operational_slip", "opp_id": "R1"}},
            {"event": "error_recorded", "error": {"category": "operational_slip", "opp_id": "R1"}},
            {"event": "support_opened", "support": {"resource": "checklist"}},
            {"event": "task_evaluated", "outcome": {"status": "success", "success": True}},
        ]
        summary = summarize_session(records)
        self.assertTrue(summary["success"])
        self.assertEqual(summary["actions_executed"], 1)
        self.assertEqual(summary["supports_used"], 1)
        self.assertEqual(summary["error_opportunities"], 1)
        self.assertEqual(summary["error_rate"], 1.0)

    def test_technical_failure_is_unknown(self):
        summary = summarize_session([
            {"event": "technical_failure", "tech_fail": True},
            {"event": "task_evaluated", "outcome": {"status": "unknown", "success": None}},
        ])
        self.assertIsNone(summary["success"])
        self.assertEqual(summary["status"], "unknown")

    def test_zero_denominators_are_undefined(self):
        summary = summarize_sessions([])
        self.assertIsNone(summary["success_rate"])
        self.assertIsNone(summary["known_success_rate"])
        self.assertEqual(summary["unknown_outcomes"], 0)


if __name__ == "__main__":
    unittest.main()