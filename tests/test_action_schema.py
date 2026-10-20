"""Testes do esquema de saída estruturada das ações do UXAgent.

Estes testes validam somente o contrato JSON da ação; não executam a interface
nem verificam pré-condições reais do controlador.
Requisito: python -m pip install jsonschema
Execução: python test_uxagent_action_schema.py
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from jsonschema import Draft202012Validator

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "uxagent_action.schema.json"


class ActionSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with SCHEMA_PATH.open(encoding="utf-8") as f:
            cls.schema = json.load(f)
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)

    def valid(self, action):
        self.assertEqual(list(self.validator.iter_errors(action)), [])

    def invalid(self, action):
        self.assertNotEqual(list(self.validator.iter_errors(action)), [])

    def test_01_valid_role_assignment(self):
        self.valid({"name": "select_role", "arguments": {"member": "Ari", "role": "LOCATE_RESOURCE"}})

    def test_02_valid_predefined_ping(self):
        self.valid({"name": "send_ping", "arguments": {"code": "PLAN_UPDATED"}})

    def test_03_valid_help_request(self):
        self.valid({"name": "open_help", "arguments": {"topic": "task_dependencies"}})

    def test_04_valid_zero_argument_action(self):
        self.valid({"name": "confirm_plan", "arguments": {}})

    def test_05_unknown_action_is_rejected(self):
        self.invalid({"name": "send_voice_chat", "arguments": {}})

    def test_06_unknown_role_is_rejected(self):
        self.invalid({"name": "select_role", "arguments": {"member": "Ari", "role": "HEALER"}})

    def test_07_missing_required_argument_is_rejected(self):
        self.invalid({"name": "select_role", "arguments": {"member": "Ari"}})

    def test_08_extra_argument_is_rejected(self):
        self.invalid({"name": "confirm_plan", "arguments": {"success": True}})

    def test_09_unknown_ping_code_is_rejected(self):
        self.invalid({"name": "send_ping", "arguments": {"code": "I_AM_DONE"}})

    def test_10_unknown_help_topic_is_rejected(self):
        self.invalid({"name": "open_help", "arguments": {"topic": "emotional_support"}})


    def test_11_valid_checklist_action(self):
        self.valid({"name": "open_checklist", "arguments": {}})

    def test_12_valid_step_order(self):
        self.valid({"name": "set_step_order", "arguments": {"steps": ["LOCATE_RESOURCE", "ACTIVATE_CHECKPOINT", "TRANSPORT_RESOURCE"]}})

    def test_13_duplicate_step_order_is_rejected(self):
        self.invalid({"name": "set_step_order", "arguments": {"steps": ["LOCATE_RESOURCE", "LOCATE_RESOURCE", "TRANSPORT_RESOURCE"]}})

    def test_14_incomplete_step_order_is_rejected(self):
        self.invalid({"name": "set_step_order", "arguments": {"steps": ["LOCATE_RESOURCE", "TRANSPORT_RESOURCE"]}})


if __name__ == "__main__":
    unittest.main(verbosity=2)
