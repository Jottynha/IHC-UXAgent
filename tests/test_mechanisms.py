from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from controller import T1Controller
from environment import T1Environment, T2Environment
from mechanisms import MechanismConfig


def config(enabled: dict[str, bool], probabilities: dict[str, float], seed: int = 11) -> MechanismConfig:
    defaults = {"R1": False, "R2": False, "R3": False, "R4": False}
    defaults.update(enabled)
    probability_defaults = {"R1": 0.90, "R2": 0.65, "R3": 0.70, "R4": 0.25}
    probability_defaults.update(probabilities)
    return MechanismConfig(enabled=defaults, probabilities=probability_defaults, seed=seed)


class R1ValiditySlipTests(unittest.TestCase):
    def test_r1_probability_zero_injects_a_plan_incompatible_action(self):
        env = T1Environment(session_id="r1-zero")
        ctl = T1Controller(env, config({"R1": True}, {"R1": 0.0}))
        proposed = {"name": "select_role", "arguments": {"member": "member_A", "role": "LOCATE_RESOURCE"}}
        result = ctl.apply(proposed)
        self.assertTrue(result.accepted)
        self.assertEqual(result.mechanism_effect["mechanism"], "R1")
        self.assertNotEqual(result.executed_action, proposed)
        self.assertEqual(result.error["category"], "operational_slip")
        # O deslize é executado no estado, não apenas recusado como JSON inválido.
        self.assertEqual(env.assignments["member_A"], result.executed_action["arguments"]["role"])
        self.assertFalse(env.validate_plan()[0])

    def test_r1_probability_one_preserves_valid_candidate(self):
        env = T1Environment(session_id="r1-one")
        ctl = T1Controller(env, config({"R1": True}, {"R1": 1.0}))
        proposed = {"name": "select_role", "arguments": {"member": "member_A", "role": "LOCATE_RESOURCE"}}
        result = ctl.apply(proposed)
        self.assertTrue(result.accepted)
        self.assertEqual(result.mechanism_effect["effect"], "candidate_retained")
        self.assertEqual(result.executed_action, proposed)
        self.assertIsNone(result.error)


class R2CommunicationOpportunityTests(unittest.TestCase):
    def _setup_after_update(self, p: float):
        env = T2Environment(session_id=f"r2-{p}")
        ctl = T1Controller(env, config({"R2": True}, {"R2": p}))
        env.trigger_feed_update()
        observation, metadata = ctl.build_observation({
            "task_id": "T2", "task": "T2", "state": env.snapshot(), "available_actions": [
                {"name": "send_ping", "arguments": {"code": "NEXT_STEP_ACTIVATE_CHECKPOINT"}},
                {"name": "review_plan", "arguments": {}},
            ]
        })
        return env, ctl, observation, metadata

    def test_r2_probability_zero_hides_and_rejects_ping(self):
        env, ctl, observation, metadata = self._setup_after_update(0.0)
        self.assertNotIn("send_ping", {x["name"] for x in observation["available_actions"]})
        self.assertFalse(metadata["communication_exposed"])
        result = ctl.apply({"name": "send_ping", "arguments": {"code": "NEXT_STEP_ACTIVATE_CHECKPOINT"}})
        self.assertFalse(result.accepted)
        self.assertEqual(result.error["category"], "invalid_action")

    def test_r2_probability_one_exposes_ping(self):
        env, ctl, observation, metadata = self._setup_after_update(1.0)
        self.assertIn("send_ping", {x["name"] for x in observation["available_actions"]})
        self.assertTrue(metadata["communication_exposed"])
        result = ctl.apply({"name": "send_ping", "arguments": {"code": "NEXT_STEP_ACTIVATE_CHECKPOINT"}})
        self.assertTrue(result.accepted)

    def test_r2_hides_ping_after_required_communication_is_sent(self):
        env, ctl, observation, metadata = self._setup_after_update(1.0)
        result = ctl.apply({"name": "send_ping", "arguments": {"code": "NEXT_STEP_ACTIVATE_CHECKPOINT"}})
        self.assertTrue(result.accepted)
        next_observation, _ = ctl.build_observation({
            "task_id": "T2", "task": "T2", "state": env.snapshot(),
            "available_actions": [
                {"name": "send_ping", "arguments": {"code": "NEXT_STEP_ACTIVATE_CHECKPOINT"}},
                {"name": "review_plan", "arguments": {}},
            ]
        })
        self.assertNotIn("send_ping", {x["name"] for x in next_observation["available_actions"]})

    def test_r2_rejects_repeated_ping_without_duplicate_execution(self):
        env, ctl, observation, metadata = self._setup_after_update(1.0)
        action = {"name": "send_ping", "arguments": {"code": "NEXT_STEP_ACTIVATE_CHECKPOINT"}}
        self.assertTrue(ctl.apply(action).accepted)
        duplicate = ctl.apply(action)
        self.assertFalse(duplicate.accepted)
        self.assertEqual(duplicate.error["rule_id"], "T2-PING-ONCE")
        self.assertEqual(env.pings, ["NEXT_STEP_ACTIVATE_CHECKPOINT"])

    def test_t2_rejects_ping_code_that_does_not_satisfy_task(self):
        env, ctl, observation, metadata = self._setup_after_update(1.0)
        result = ctl.apply({"name": "send_ping", "arguments": {"code": "PLAN_UPDATED"}})
        self.assertFalse(result.accepted)
        self.assertEqual(result.error["rule_id"], "T2-COMMUNICATION-CODE")
        self.assertEqual(env.pings, [])


class R3FreshStateTests(unittest.TestCase):
    def _observation_after_update(self, p: float):
        env = T2Environment(session_id=f"r3-{p}")
        ctl = T1Controller(env, config({"R3": True}, {"R3": p}))
        env.trigger_feed_update()
        base = {"task_id": "T2", "task": "T2", "state": env.snapshot(), "available_actions": []}
        return env, ctl, ctl.build_observation(base)[0]

    def test_r3_probability_zero_keeps_cached_feed_stale(self):
        env, ctl, observation = self._observation_after_update(0.0)
        self.assertEqual(env.feed_revision, 1)
        self.assertEqual(observation["state"]["feed_revision"], 0)
        # Atualizar explicitamente o feed vence o cache obsoleto.
        ctl.apply({"name": "refresh_feed", "arguments": {}})
        refreshed, _ = ctl.build_observation({"task_id": "T2", "task": "T2", "state": env.snapshot(), "available_actions": []})
        self.assertEqual(refreshed["state"]["feed_revision"], 1)

    def test_r3_probability_one_delivers_fresh_state(self):
        env, ctl, observation = self._observation_after_update(1.0)
        self.assertEqual(observation["state"]["feed_revision"], 1)
        self.assertEqual(observation["state"]["completed_steps"], ["LOCATE_RESOURCE"])


    def test_r3_failure_is_not_resampled_until_explicit_refresh(self):
        env = T2Environment(session_id="r3-once")
        ctl = T1Controller(env, config({"R3": True}, {"R3": 0.0}))
        env.trigger_feed_update()
        base = {"task_id": "T2", "task": "T2", "state": env.snapshot(), "available_actions": []}
        ctl.build_observation(base)
        # Probability zero keeps the same update stale at every later observation.
        second_observation, _ = ctl.build_observation(base)
        self.assertEqual(second_observation["state"]["feed_revision"], 0)



class R4HelpAffordanceTests(unittest.TestCase):
    def test_r4_probability_zero_hides_help_but_not_checklist(self):
        env = T1Environment(session_id="r4-zero")
        ctl = T1Controller(env, config({"R4": True}, {"R4": 0.0}))
        observation, metadata = ctl.build_observation({
            "task_id": "T1", "task": "T1", "state": env.snapshot(), "available_actions": [
                {"name": "open_help", "arguments": {"topic": "task_dependencies"}},
                {"name": "open_checklist", "arguments": {}},
            ]
        })
        names = {x["name"] for x in observation["available_actions"]}
        self.assertNotIn("open_help", names)
        self.assertIn("open_checklist", names)
        self.assertFalse(metadata["help_exposed"])
        result = ctl.apply({"name": "open_help", "arguments": {"topic": "task_dependencies"}})
        self.assertFalse(result.accepted)
        self.assertEqual(result.error["category"], "invalid_action")

    def test_r4_probability_one_exposes_help(self):
        env = T1Environment(session_id="r4-one")
        ctl = T1Controller(env, config({"R4": True}, {"R4": 1.0}))
        observation, _ = ctl.build_observation({
            "task_id": "T1", "task": "T1", "state": env.snapshot(), "available_actions": [
                {"name": "open_help", "arguments": {"topic": "task_dependencies"}}
            ]
        })
        self.assertIn("open_help", {x["name"] for x in observation["available_actions"]})
        result = ctl.apply({"name": "open_help", "arguments": {"topic": "task_dependencies"}})
        self.assertTrue(result.accepted)


class MechanismConfigTests(unittest.TestCase):
    def test_config_file_loads_default_probabilities_with_all_off(self):
        base = Path(__file__).resolve().parents[1]
        cfg = MechanismConfig.from_file(base / "uxagent_mechanisms.json")
        self.assertFalse(any(cfg.enabled.values()))
        self.assertEqual(cfg.probabilities, {"R1": 0.9, "R2": 0.65, "R3": 0.7, "R4": 0.25})
        self.assertEqual(len(cfg.fingerprint), 10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
