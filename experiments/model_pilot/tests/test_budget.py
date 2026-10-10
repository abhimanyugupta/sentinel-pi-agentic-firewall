"""Offline tests for persistent model-call budget accounting."""
import json
import tempfile
import unittest
from pathlib import Path

from experiments.model_pilot.budget import (
    APPROVAL_PHRASE,
    BudgetExhausted,
    BudgetGuard,
)


class BudgetGuardTests(unittest.TestCase):
    def make_guard(self, root: Path, *, generation_limit=2, warmup_limit=0):
        (root / "evidence").mkdir(parents=True, exist_ok=True)
        (root / "BUDGET_POLICY.json").write_text(json.dumps({
            "schema_version": 1,
            "limits": {"generation": generation_limit, "warmup": warmup_limit},
        }), encoding="utf-8")
        (root / "BUDGET_STATE.json").write_text(json.dumps({
            "schema_version": 1,
            "baseline_usage": {"generation": 0, "warmup": 0},
            "reservations": {"generation": [], "warmup": []},
        }), encoding="utf-8")
        (root / "BUDGET_APPROVALS.json").write_text(json.dumps({
            "schema_version": 1, "approvals": [],
        }), encoding="utf-8")
        return BudgetGuard(root, lock_path=root / "budget.lock")

    def test_existing_recordings_exceed_original_cap_and_block(self):
        guard = BudgetGuard()
        current = guard.status()
        self.assertEqual(current["kinds"]["generation"]["used"], 133)
        self.assertEqual(current["kinds"]["generation"]["limit"], 24)
        self.assertEqual(current["kinds"]["warmup"]["used"], 2)
        self.assertEqual(current["kinds"]["warmup"]["limit"], 0)
        with self.assertRaises(BudgetExhausted):
            guard.require_capacity("generation")
        with self.assertRaises(BudgetExhausted):
            guard.require_capacity("warmup")

    def test_attempt_reservation_persists_across_guard_instances(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = self.make_guard(root)
            first.reserve("generation")
            first.reserve("generation")
            second = BudgetGuard(root, lock_path=root / "budget.lock")
            self.assertEqual(second.status()["kinds"]["generation"]["used"], 2)
            with self.assertRaises(BudgetExhausted):
                second.reserve("generation")

    def test_history_and_reservations_use_the_larger_cumulative_count(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            guard = self.make_guard(root, generation_limit=5)
            state = json.loads((root / "BUDGET_STATE.json").read_text())
            state["baseline_usage"]["generation"] = 4
            (root / "BUDGET_STATE.json").write_text(json.dumps(state), encoding="utf-8")
            evidence = root / "evidence" / "run-011.json"
            evidence.write_text(json.dumps({"requests_attempted": 4}), encoding="utf-8")
            guard.reserve("generation")
            self.assertEqual(guard.status()["kinds"]["generation"]["used"], 5)
            with self.assertRaises(BudgetExhausted):
                guard.reserve("generation")

    def test_increase_requires_explicit_confirmation_and_covers_existing_usage(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            guard = self.make_guard(root, generation_limit=2)
            state = json.loads((root / "BUDGET_STATE.json").read_text())
            state["baseline_usage"]["generation"] = 3
            (root / "BUDGET_STATE.json").write_text(json.dumps(state), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "human_confirmation_required"):
                guard.approve_increase("generation", 4, "approval-ref-2026", "yes")
            record = guard.approve_increase(
                "generation", 4, "approval-ref-2026", APPROVAL_PHRASE,
            )
            self.assertEqual(record["approved_by"], "human_operator_attestation")
            self.assertEqual(guard.status()["kinds"]["generation"]["limit"], 4)
            guard.reserve("generation")

    def test_malformed_history_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            guard = self.make_guard(root)
            (root / "evidence" / "run-001.json").write_text("{}", encoding="utf-8")
            with self.assertRaises(ValueError):
                guard.status()


if __name__ == "__main__":
    unittest.main()
