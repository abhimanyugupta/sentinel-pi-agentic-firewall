"""In-memory application state backed by reproducible local fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from threading import RLock
from typing import Any

from sentinel_pi.agent import load_demo_scenarios, run_scenario
from sentinel_pi.evaluation import DEFAULT_DATASET, run_evaluation, save_report
from sentinel_pi.policy import PolicyManager

ROOT = Path(__file__).resolve().parent.parent


class AppState:
    def __init__(self) -> None:
        cases = [json.loads(line) for line in DEFAULT_DATASET.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.policy_manager = PolicyManager(cases)
        self.scenarios = load_demo_scenarios()
        self.events: list[dict[str, Any]] = []
        self.evaluation = run_evaluation()
        save_report(self.evaluation)
        self._lock = RLock()
        # Populate the console with real local runs, not display-only constants.
        for scenario_id in ("legitimate_support", "indirect_injection", "answer_contamination"):
            self.events.append(run_scenario(scenario_id, self.policy_manager.active_policy))

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "metrics": self.evaluation["metrics"],
                "evaluation_id": self.evaluation["evaluation_id"],
                "events": list(reversed(self.events[-20:])),
                "scenarios": [
                    {"id": value["id"], "title": value["title"]}
                    for value in self.scenarios.values()
                ],
                "policy": self.policy_manager.snapshot(),
            }

    def replay(self, scenario_id: str) -> dict[str, Any]:
        with self._lock:
            if scenario_id not in self.scenarios:
                raise ValueError("Unknown demo scenario.")
            event = run_scenario(scenario_id, self.policy_manager.active_policy)
            self.events.append(event)
            return event

    def evaluate(self) -> dict[str, Any]:
        with self._lock:
            self.evaluation = run_evaluation()
            save_report(self.evaluation)
            return self.evaluation

    def propose_policy(self, proposal: Any) -> dict[str, Any]:
        with self._lock:
            result = self.policy_manager.evaluate_candidate(proposal)
            path = ROOT / "artifacts" / "candidates-latest.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(self.policy_manager.snapshot(), indent=2) + "\n", encoding="utf-8")
            return result

    def rollback_policy(self) -> dict[str, Any]:
        with self._lock:
            result = self.policy_manager.rollback()
            path = ROOT / "artifacts" / "candidates-latest.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(self.policy_manager.snapshot(), indent=2) + "\n", encoding="utf-8")
            return result
