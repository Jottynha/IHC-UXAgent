from __future__ import annotations

import unittest

from uxagent_session import UXAgentSession


class ReservedTaskTests(unittest.TestCase):
    def test_t3_requires_explicit_removal_and_can_replan(self):
        session = UXAgentSession("T3", session_id="session-t3")
        self.assertIn(
            "remove_assignment",
            {item["name"] for item in session.view_model()["available_actions"]},
        )
        session.trigger_feed_update()
        session.view_model()
        for action in (
            {"name": "refresh_feed", "arguments": {}},
            {"name": "remove_assignment", "arguments": {"member": "member_C"}},
            {"name": "select_role", "arguments": {"member": "member_D", "role": "ACTIVATE_CHECKPOINT"}},
            {"name": "select_role", "arguments": {"member": "member_B", "role": "TRANSPORT_RESOURCE"}},
            {"name": "review_plan", "arguments": {}},
            {"name": "confirm_plan", "arguments": {}},
        ):
            self.assertTrue(session.dispatch(action).accepted)
        outcome = session.evaluate()
        self.assertTrue(outcome["success"], outcome)

    def test_t4_requires_order_feed_ping_and_plan(self):
        session = UXAgentSession("T4", session_id="session-t4")
        session.trigger_feed_update()
        session.view_model()
        for action in (
            {"name": "set_step_order", "arguments": {
                "steps": ["LOCATE_RESOURCE", "ACTIVATE_CHECKPOINT", "TRANSPORT_RESOURCE"],
            }},
            {"name": "send_ping", "arguments": {"code": "NEXT_STEP_ACTIVATE_CHECKPOINT"}},
            {"name": "select_role", "arguments": {"member": "member_B", "role": "TRANSPORT_RESOURCE"}},
            {"name": "select_role", "arguments": {"member": "member_C", "role": "ACTIVATE_CHECKPOINT"}},
            {"name": "review_plan", "arguments": {}},
            {"name": "confirm_plan", "arguments": {}},
        ):
            self.assertTrue(session.dispatch(action).accepted)
        outcome = session.evaluate()
        self.assertTrue(outcome["success"], outcome)

    def test_reserved_actions_do_not_leak_into_t1(self):
        names = {item["name"] for item in UXAgentSession("T1").view_model()["available_actions"]}
        self.assertNotIn("remove_assignment", names)


if __name__ == "__main__":
    unittest.main()
