from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from controller import T1Controller
from environment import T1Environment
from event_logger import EventLogger


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.env = T1Environment(session_id="test-session")
        self.controller = T1Controller(self.env)

    def test_valid_role_assignment(self):
        result = self.controller.apply({"name": "select_role", "arguments": {"member": "member_A", "role": "LOCATE_RESOURCE"}})
        self.assertTrue(result.accepted)
        self.assertEqual(self.env.assignments["member_A"], "LOCATE_RESOURCE")

    def test_incompatible_role_is_rejected(self):
        result = self.controller.apply({"name": "select_role", "arguments": {"member": "member_B", "role": "LOCATE_RESOURCE"}})
        self.assertFalse(result.accepted)
        self.assertEqual(result.error["category"], "skill_constraint_violation")
        self.assertEqual(self.env.assignments, {})

    def test_duplicate_role_is_rejected(self):
        self.controller.apply({"name": "select_role", "arguments": {"member": "member_C", "role": "ACTIVATE_CHECKPOINT"}})
        result = self.controller.apply({"name": "select_role", "arguments": {"member": "member_A", "role": "ACTIVATE_CHECKPOINT"}})
        self.assertFalse(result.accepted)
        self.assertEqual(result.error["category"], "role_missing_or_duplicated")

    def test_confirm_before_review_is_rejected(self):
        self._assign_valid_roles()
        result = self.controller.apply({"name": "confirm_plan", "arguments": {}})
        self.assertFalse(result.accepted)
        self.assertFalse(self.env.plan_confirmed)

    def test_correct_plan_requires_review_then_confirm(self):
        self._assign_valid_roles()
        reviewed = self.controller.apply({"name": "review_plan", "arguments": {}})
        self.assertTrue(reviewed.accepted)
        self.assertTrue(self.env.reviewed)
        confirmed = self.controller.apply({"name": "confirm_plan", "arguments": {}})
        self.assertTrue(confirmed.accepted)
        success, _ = self.env.externally_evaluate()
        self.assertTrue(success)

    def test_role_change_invalidates_previous_review(self):
        self._assign_valid_roles()
        self.controller.apply({"name": "review_plan", "arguments": {}})
        # Trocar a ordem por outra válida ainda altera o plano e exige nova revisão.
        result = self.controller.apply({"name": "set_step_order", "arguments": {"steps": ["ACTIVATE_CHECKPOINT", "LOCATE_RESOURCE", "TRANSPORT_RESOURCE"]}})
        self.assertTrue(result.accepted)
        self.assertFalse(self.env.reviewed)

    def test_invalid_dependency_order_is_rejected(self):
        result = self.controller.apply({"name": "set_step_order", "arguments": {"steps": ["TRANSPORT_RESOURCE", "LOCATE_RESOURCE", "ACTIVATE_CHECKPOINT"]}})
        self.assertFalse(result.accepted)
        self.assertEqual(result.error["category"], "dependency_violation")

    def _assign_valid_roles(self):
        actions = [
            {"name": "select_role", "arguments": {"member": "member_A", "role": "LOCATE_RESOURCE"}},
            {"name": "select_role", "arguments": {"member": "member_B", "role": "TRANSPORT_RESOURCE"}},
            {"name": "select_role", "arguments": {"member": "member_C", "role": "ACTIVATE_CHECKPOINT"}},
        ]
        for action in actions:
            result = self.controller.apply(action)
            self.assertTrue(result.accepted, result.reason)


class EventLoggerTests(unittest.TestCase):
    def test_logs_event_validated_by_schema(self):
        base = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            logger = EventLogger(path, base / "uxagent_event.schema.json", "mock-policy")
            logger.log(event="task_start", actor="controller", session_id="test", step=0,
                       state_post={"plan_confirmed": False})
            entry = json.loads(path.read_text(encoding="utf-8").strip())
            self.assertEqual(entry["event"], "task_start")
            self.assertTrue(entry["synthetic"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
