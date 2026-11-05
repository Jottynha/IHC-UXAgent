from __future__ import annotations

import unittest

from uxagent_session import UXAgentSession
from mechanisms import MechanismConfig


class SessionTests(unittest.TestCase):
    def test_view_model_contains_only_observed_t2_feed(self):
        session = UXAgentSession(
            "T2",
            session_id="session-ui",
            config=MechanismConfig(
                enabled={"R1": False, "R2": False, "R3": True, "R4": False},
                probabilities={"R1": 0.9, "R2": 0.65, "R3": 0.0, "R4": 0.25},
            ),
        )
        session.trigger_feed_update()
        view = session.view_model()
        self.assertEqual(view["feed"]["revision"], 0)
        self.assertIn("refresh_feed", {item["name"] for item in view["available_actions"]})
        self.assertNotIn("update_applied", view["state"] if "state" in view else {})

    def test_dispatch_rejects_malformed_input_without_crashing(self):
        session = UXAgentSession("T1", session_id="session-invalid")
        result = session.dispatch({"name": "unknown", "arguments": {}})
        self.assertFalse(result.accepted)
        self.assertEqual(result.error["category"], "invalid_action")
        self.assertEqual(session.controller.env.proposal_count, 1)
        self.assertEqual(session.events[-1].name, "action_rejected")
        self.assertEqual(session.view_model()["history"][0]["accepted"], False)

    def test_dispatch_and_evaluate_valid_plan(self):
        session = UXAgentSession("T1", session_id="session-success")
        for action in (
            {"name": "select_role", "arguments": {"member": "member_A", "role": "LOCATE_RESOURCE"}},
            {"name": "select_role", "arguments": {"member": "member_B", "role": "TRANSPORT_RESOURCE"}},
            {"name": "select_role", "arguments": {"member": "member_C", "role": "ACTIVATE_CHECKPOINT"}},
            {"name": "review_plan", "arguments": {}},
            {"name": "confirm_plan", "arguments": {}},
        ):
            self.assertTrue(session.dispatch(action).accepted)
        self.assertEqual(session.evaluate()["success"], True)
        self.assertEqual(session.view_model()["status"], "completed")
        self.assertEqual(len(session.history()), 5)

    def test_t1_does_not_expose_t2_only_actions(self):
        names = {item["name"] for item in UXAgentSession("T1").view_model()["available_actions"]}
        self.assertNotIn("send_ping", names)
        self.assertNotIn("refresh_feed", names)


if __name__ == "__main__":
    unittest.main(verbosity=2)
