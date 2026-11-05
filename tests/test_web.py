from __future__ import annotations

import json
import threading
import unittest
import tempfile
from pathlib import Path
from http.client import HTTPConnection

from uxagent_web import create_server


class WebInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.server = create_server(port=0, task_id="T1", log_dir=Path(self.temp_dir.name))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.connection = HTTPConnection("127.0.0.1", self.server.server_address[1], timeout=3)

    def tearDown(self):
        self.connection.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.temp_dir.cleanup()

    def request(self, method, path, payload=None):
        body = json.dumps(payload).encode() if payload is not None else None
        self.connection.request(method, path, body, {"Content-Type": "application/json"} if body else {})
        response = self.connection.getresponse()
        return response.status, json.loads(response.read())

    def test_home_and_state_are_available(self):
        self.connection.request("GET", "/")
        response = self.connection.getresponse()
        self.assertEqual(response.status, 200)
        self.assertIn("Lobby cooperativo", response.read().decode())
        status, state = self.request("GET", "/api/state")
        self.assertEqual(status, 200)
        self.assertEqual(state["ui_version"], "ui-contract-v2")

    def test_action_round_trip_updates_view_and_history(self):
        status, state = self.request("POST", "/api/action", {
            "name": "select_role",
            "arguments": {"member": "member_A", "role": "LOCATE_RESOURCE"},
        })
        self.assertEqual(status, 200)
        self.assertEqual(state["assignments"]["member_A"], "LOCATE_RESOURCE")
        self.assertEqual(len(state["history"]), 1)
        log_path = Path(self.temp_dir.name) / "web-t1.jsonl"
        self.assertTrue(log_path.exists())
        self.assertGreaterEqual(len(log_path.read_text(encoding="utf-8").splitlines()), 3)

    def test_invalid_action_is_reported_without_server_error(self):
        status, state = self.request("POST", "/api/action", {"name": "invalid", "arguments": {}})
        self.assertEqual(status, 200)
        self.assertFalse(state["history"][0]["accepted"])

    def test_evaluator_endpoint_uses_external_state(self):
        for action in (
            {"name": "select_role", "arguments": {"member": "member_A", "role": "LOCATE_RESOURCE"}},
            {"name": "select_role", "arguments": {"member": "member_B", "role": "TRANSPORT_RESOURCE"}},
            {"name": "select_role", "arguments": {"member": "member_C", "role": "ACTIVATE_CHECKPOINT"}},
            {"name": "review_plan", "arguments": {}},
            {"name": "confirm_plan", "arguments": {}},
        ):
            self.request("POST", "/api/action", action)
        status, outcome = self.request("POST", "/api/evaluate")
        self.assertEqual(status, 200)
        self.assertTrue(outcome["success"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
