"""Testes de contrato do esquema de eventos do UXAgent.

Estes testes validam somente uxagent_event.schema.json. Eles não substituem os
ensaios de integração V02-V08/V10, que dependem do controlador e da interface.
Requisito: python -m pip install jsonschema
Execução: python test_uxagent_event_schema.py
"""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

BASE_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = BASE_DIR / "uxagent_event.schema.json"


def make_event(**overrides):
    """Cria um evento sintético básico válido, com overrides para testes negativos."""
    event = {
        "schema_version": "1.0",
        "sid": "session-test-001",
        "tid": "T1",
        "cond": "calibration",
        "actor": "llm",
        "synthetic": True,
        "cfg_ver": "cfg-test-v1",
        "ui_ver": "ui-wireframe-v1",
        "llm_model": "gpt-6-luna-candidate",
        "llm_version": None,
        "prompt_ver": "prompt-v1",
        "step": 0,
        "event": "action_proposed",
        "ts_sys": "2026-10-16T14:00:00Z",
        "obs_id": "obs-0001",
        "state_pre": {"plan_confirmed": False},
        "state_post": None,
        "act_prop": {
            "name": "select_role",
            "arguments": {"member": "Ari", "role": "LOCATE_RESOURCE"},
        },
        "act_exec": None,
        "reject": None,
        "support": None,
        "error": None,
        "opp_id": "R1-opp-1",
        "outcome": None,
        "tech_fail": False,
        "tech_fail_reason": None,
        "note": None,
    }
    event.update(overrides)
    return event


class EventSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with SCHEMA_PATH.open("r", encoding="utf-8") as handle:
            cls.schema = json.load(handle)
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(
            cls.schema,
            format_checker=FormatChecker(),
        )

    def assert_valid(self, event):
        self.assertEqual(list(self.validator.iter_errors(event)), [])

    def assert_invalid(self, event):
        self.assertNotEqual(list(self.validator.iter_errors(event)), [])

    def test_01_valid_synthetic_llm_action(self):
        self.assert_valid(make_event())

    def test_02_valid_human_event_is_not_synthetic(self):
        event = make_event(
            actor="human",
            synthetic=False,
            cond="human_profile",
            event="task_start",
            act_prop=None,
            obs_id=None,
            state_pre=None,
        )
        self.assert_valid(event)

    def test_03_required_session_id_cannot_be_missing(self):
        event = make_event()
        event.pop("sid")
        self.assert_invalid(event)

    def test_04_unknown_top_level_field_is_rejected(self):
        event = make_event(unregistered_field="unexpected")
        self.assert_invalid(event)

    def test_05_unknown_task_identifier_is_rejected(self):
        self.assert_invalid(make_event(tid="T5"))

    def test_06_unknown_event_type_is_rejected(self):
        self.assert_invalid(make_event(event="agent_says_success"))

    def test_07_action_outside_closed_vocabulary_is_rejected(self):
        event = make_event(
            act_prop={"name": "solve_everything", "arguments": {}}
        )
        self.assert_invalid(event)

    def test_08_human_origin_cannot_be_marked_synthetic(self):
        self.assert_invalid(make_event(actor="human", synthetic=True))

    def test_09_llm_origin_must_be_marked_synthetic(self):
        self.assert_invalid(make_event(actor="llm", synthetic=False))

    def test_10_technical_failure_requires_technical_event_type(self):
        self.assert_invalid(make_event(event="action_executed", tech_fail=True))

    def test_11_technical_failure_event_is_valid(self):
        event = make_event(
            actor="controller",
            synthetic=True,
            event="technical_failure",
            tech_fail=True,
            act_prop=None,
            act_exec=None,
            tech_fail_reason="state_log_unavailable",
            outcome={"status": "unknown", "success": None, "reason": "state unavailable"},
        )
        self.assert_valid(event)

    def test_12_invalid_timestamp_format_is_rejected(self):
        self.assert_invalid(make_event(ts_sys="yesterday at noon"))

    def test_13_unknown_support_resource_is_rejected(self):
        event = make_event(
            event="support_opened",
            support={"resource": "telepathy", "opened": True, "topic": None},
        )
        self.assert_invalid(event)

    def test_14_null_proposed_action_is_allowed_for_non_action_event(self):
        event = make_event(
            event="task_start",
            act_prop=None,
            act_exec=None,
            obs_id=None,
            state_pre=None,
        )
        self.assert_valid(event)


if __name__ == "__main__":
    unittest.main(verbosity=2)
