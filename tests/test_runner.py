from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

BASE = Path(__file__).resolve().parents[1]


class MockEndToEndTests(unittest.TestCase):
    def test_cli_mock_runs_t1_and_writes_valid_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["UXAGENT_LOG_DIR"] = str(Path(tmp) / "logs")
            result = subprocess.run(
                [sys.executable, str(BASE / "run_uxagent_t1.py"), "--mock"],
                cwd=BASE,
                env=env,
                text=True,
                capture_output=True,
                timeout=20,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)
            self.assertIn("RESULTADO: SUCESSO", result.stdout)
            log_files = list((Path(tmp) / "logs").glob("*.jsonl"))
            self.assertEqual(len(log_files), 1)
            with (BASE / "uxagent_event.schema.json").open(encoding="utf-8") as f:
                schema = json.load(f)
            validator = Draft202012Validator(schema, format_checker=FormatChecker())
            records = [json.loads(line) for line in log_files[0].read_text(encoding="utf-8").splitlines()]
            self.assertGreaterEqual(len(records), 10)
            for record in records:
                self.assertEqual(list(validator.iter_errors(record)), [])
            self.assertEqual(records[-1]["event"], "task_end")
            self.assertTrue(records[-1]["outcome"]["success"])

    def test_cli_mock_runs_t2_and_writes_valid_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["UXAGENT_LOG_DIR"] = str(Path(tmp) / "logs")
            result = subprocess.run(
                [sys.executable, str(BASE / "run_uxagent_t1.py"), "--mock", "--task", "T2"],
                cwd=BASE, env=env, text=True, capture_output=True, timeout=20, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)
            self.assertIn("RESULTADO: SUCESSO", result.stdout)
            log_files = list((Path(tmp) / "logs").glob("*.jsonl"))
            self.assertEqual(len(log_files), 1)
            with (BASE / "uxagent_event.schema.json").open(encoding="utf-8") as f:
                schema = json.load(f)
            validator = Draft202012Validator(schema, format_checker=FormatChecker())
            records = [json.loads(line) for line in log_files[0].read_text(encoding="utf-8").splitlines()]
            for record in records:
                self.assertEqual(list(validator.iter_errors(record)), [])
                self.assertEqual(record["tid"], "T2")
            self.assertTrue(records[-1]["outcome"]["success"])
            self.assertTrue(any(r.get("opp_id") == "T2-FEED-UPDATE" for r in records))

    def _write_test_config(self, path: Path, mechanism: str, probability: float):
        with (BASE / "uxagent_mechanisms.json").open(encoding="utf-8") as f:
            config = json.load(f)
        config["mechanisms"][mechanism]["probability"] = probability
        path.write_text(json.dumps(config), encoding="utf-8")

    def test_cli_r1_forced_slip_is_logged_as_proposed_vs_executed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = root / "config.json"
            self._write_test_config(cfg, "R1", 0.0)
            env = os.environ.copy()
            env["UXAGENT_LOG_DIR"] = str(root / "logs")
            result = subprocess.run(
                [sys.executable, str(BASE / "run_uxagent_t1.py"), "--mock", "--task", "T1",
                 "--enable", "R1", "--config", str(cfg), "--max-steps", "1"],
                cwd=BASE, env=env, text=True, capture_output=True, timeout=20, check=False,
            )
            self.assertEqual(result.returncode, 1, result.stdout + "\n" + result.stderr)  # um passo não termina T1
            log_files = list((root / "logs").glob("*.jsonl"))
            self.assertEqual(len(log_files), 1)
            records = [json.loads(line) for line in log_files[0].read_text(encoding="utf-8").splitlines()]
            injected = [r for r in records if r["event"] == "action_executed" and r.get("error", {}).get("category") == "operational_slip"]
            self.assertEqual(len(injected), 1)
            self.assertNotEqual(injected[0]["act_prop"], injected[0]["act_exec"])
            with (BASE / "uxagent_event.schema.json").open(encoding="utf-8") as f:
                schema = json.load(f)
            validator = Draft202012Validator(schema, format_checker=FormatChecker())
            for record in records:
                self.assertEqual(list(validator.iter_errors(record)), [])

    def test_cli_r2_no_communication_opportunity_leads_to_external_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = root / "config.json"
            self._write_test_config(cfg, "R2", 0.0)
            env = os.environ.copy()
            env["UXAGENT_LOG_DIR"] = str(root / "logs")
            result = subprocess.run(
                [sys.executable, str(BASE / "run_uxagent_t1.py"), "--mock", "--task", "T2",
                 "--enable", "R2", "--config", str(cfg), "--max-steps", "10"],
                cwd=BASE, env=env, text=True, capture_output=True, timeout=20, check=False,
            )
            self.assertEqual(result.returncode, 1, result.stdout + "\n" + result.stderr)
            self.assertIn("RESULTADO: FALHA", result.stdout)
            log_files = list((root / "logs").glob("*.jsonl"))
            records = [json.loads(line) for line in log_files[0].read_text(encoding="utf-8").splitlines()]
            self.assertFalse(records[-1]["outcome"]["success"])
            self.assertIn("não foi comunicada", records[-1]["outcome"]["reason"])

    def test_cli_r3_stale_observation_can_be_recovered_by_refresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = root / "config.json"
            self._write_test_config(cfg, "R3", 0.0)
            env = os.environ.copy()
            env["UXAGENT_LOG_DIR"] = str(root / "logs")
            result = subprocess.run(
                [sys.executable, str(BASE / "run_uxagent_t1.py"), "--mock", "--task", "T2",
                 "--enable", "R3", "--config", str(cfg), "--max-steps", "12"],
                cwd=BASE, env=env, text=True, capture_output=True, timeout=20, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)
            self.assertIn("RESULTADO: SUCESSO", result.stdout)
            log_files = list((root / "logs").glob("*.jsonl"))
            records = [json.loads(line) for line in log_files[0].read_text(encoding="utf-8").splitlines()]
            self.assertTrue(any((r.get("act_prop") or {}).get("name") == "refresh_feed" for r in records))
            self.assertTrue(records[-1]["outcome"]["success"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
