"""Restricted defensive policy proposals with isolated regression evidence."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Iterable

from sentinel_pi.models import ATTACK_TYPES, ContentEnvelope, IntentContract, ToolProposal
from sentinel_pi.security.firewall import Firewall, FirewallPolicy
from sentinel_pi.security.preprocess import Preprocessor
from sentinel_pi.security.rules import RuleClassifier
from sentinel_pi.toolgate import IntentGate, MockToolRuntime


@dataclass(frozen=True)
class CandidatePatch:
    name: str
    add_block_categories: tuple[str, ...] = ()
    add_literal_indicators: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class PolicyVersion:
    version: int
    policy: FirewallPolicy
    accepted_candidate: str
    evidence: dict[str, Any]


class CandidateSchemaError(ValueError):
    pass


def parse_candidate(value: Any) -> CandidatePatch:
    if not isinstance(value, dict) or set(value) - {"name", "add_block_categories", "add_literal_indicators"}:
        raise CandidateSchemaError("Candidate schema allows only name, add_block_categories, and add_literal_indicators.")
    name = value.get("name")
    if not isinstance(name, str) or not name.strip() or len(name) > 80:
        raise CandidateSchemaError("Candidate name must be 1 to 80 characters.")
    raw_categories = value.get("add_block_categories", [])
    raw_indicators = value.get("add_literal_indicators", [])
    if not isinstance(raw_categories, list) or not isinstance(raw_indicators, list):
        raise CandidateSchemaError("Candidate categories and indicators must be lists.")
    if len(raw_categories) > 3 or len(raw_indicators) > 3:
        raise CandidateSchemaError("A candidate may add at most three categories and three literal indicators.")
    if any(not isinstance(category, str) or category not in ATTACK_TYPES for category in raw_categories):
        raise CandidateSchemaError("Candidate contains an unknown category.")
    indicators: list[tuple[str, str]] = []
    for item in raw_indicators:
        if not isinstance(item, dict) or set(item) != {"phrase", "attack_type"}:
            raise CandidateSchemaError("Each literal indicator must contain exactly phrase and attack_type.")
        phrase = item["phrase"]
        category = item["attack_type"]
        if not isinstance(phrase, str) or not 8 <= len(phrase) <= 120:
            raise CandidateSchemaError("Literal indicators must contain 8 to 120 characters.")
        if category not in ATTACK_TYPES:
            raise CandidateSchemaError("Literal indicator category is unknown.")
        if any(mark in phrase for mark in (".*", ".+", "(?", "[", "]", "\\d", "\\w")):
            raise CandidateSchemaError("Regular expressions and wildcard patterns are not allowed.")
        indicators.append((phrase, category))
    return CandidatePatch(name.strip(), tuple(dict.fromkeys(raw_categories)), tuple(indicators))


class PolicyManager:
    def __init__(self, cases: Iterable[dict[str, Any]], policy: FirewallPolicy | None = None) -> None:
        self._initial = policy or FirewallPolicy()
        self._active = self._initial
        self._cases = tuple(cases)
        self.history: list[PolicyVersion] = [
            PolicyVersion(1, self._active, "initial", {"created": True})
        ]
        self._rollback_stack: list[PolicyVersion] = []
        self.candidate_evidence: list[dict[str, Any]] = []

    @property
    def active_policy(self) -> FirewallPolicy:
        return self._active

    def evaluate_candidate(self, raw_candidate: Any) -> dict[str, Any]:
        try:
            patch = parse_candidate(raw_candidate)
        except CandidateSchemaError as exc:
            evidence = {"accepted": False, "stage": "schema", "reason": str(exc)}
            self.candidate_evidence.append(evidence)
            return evidence

        candidate_policy = replace(
            self._active,
            policy_id=f"policy-v{len(self.history) + 1}",
            block_categories=tuple(dict.fromkeys(self._active.block_categories + patch.add_block_categories)),
            literal_indicators=tuple(
                dict.fromkeys(self._active.literal_indicators + patch.add_literal_indicators)
            ),
        )
        baseline = self._measure(self._active)
        candidate = self._measure(candidate_policy)
        baseline_e2e = self._measure_end_to_end(self._active)
        candidate_e2e = self._measure_end_to_end(candidate_policy)
        gate_invariant = self._gate_invariant()
        policy_comparison = self._compare_attack_outcomes(baseline, candidate)
        security_improvement = (
            candidate["attack_escaped_cases"] < baseline["attack_escaped_cases"]
            or candidate_e2e["untrusted_instruction_parser_admissions"]
            < baseline_e2e["untrusted_instruction_parser_admissions"]
            or candidate_e2e["protected_unauthorized_side_effects"]
            < baseline_e2e["protected_unauthorized_side_effects"]
        )
        checks = {
            "attack_detection_not_lower": candidate["attack_detection_rate"] >= baseline["attack_detection_rate"],
            "attack_containment_not_lower": candidate["contained_attack_rate"] >= baseline["contained_attack_rate"],
            "attack_escapes_not_higher": candidate["attack_escaped_cases"] <= baseline["attack_escaped_cases"],
            "policy_severity_increased": candidate["blocked_attack_rate"] > baseline["blocked_attack_rate"],
            "benign_pass_not_lower": candidate["benign_pass_rate"] >= baseline["benign_pass_rate"],
            "false_positives_not_higher": candidate["false_positives"] <= baseline["false_positives"],
            "end_to_end_attack_outcomes_not_worse": (
                candidate_e2e["untrusted_instruction_parser_admissions"]
                <= baseline_e2e["untrusted_instruction_parser_admissions"]
                and candidate_e2e["protected_unauthorized_side_effects"]
                <= baseline_e2e["protected_unauthorized_side_effects"]
            ),
            "legitimate_task_correctness_not_lower": (
                candidate_e2e["legitimate_tasks_correct"] >= baseline_e2e["legitimate_tasks_correct"]
            ),
            "tool_gate_unchanged_and_safe": gate_invariant,
        }
        accepted = all(checks.values())
        evidence: dict[str, Any] = {
            "candidate": patch.name,
            "accepted": accepted,
            "stage": "evaluation",
            "checks": checks,
            "baseline": baseline,
            "candidate_metrics": candidate,
            "policy_comparison": policy_comparison,
            "end_to_end": {"baseline": baseline_e2e, "candidate": candidate_e2e},
            "security_improvement_demonstrated": security_improvement,
            "candidate_classification": (
                "attack_containment_improvement"
                if security_improvement
                else "policy_hardening_only"
                if checks["policy_severity_increased"]
                else "no_demonstrated_security_improvement"
            ),
            "tool_gate_invariant": gate_invariant,
            "public_development_cases_only": True,
            "active_policy_before": self._active.policy_id,
        }
        if accepted:
            self._rollback_stack.append(self.history[-1])
            self._active = candidate_policy
            self.history.append(PolicyVersion(len(self.history) + 1, candidate_policy, patch.name, evidence))
            evidence["active_policy_after"] = candidate_policy.policy_id
        else:
            failed = [key for key, passed in checks.items() if not passed]
            evidence["reason"] = "Candidate failed: " + ", ".join(failed)
        self.candidate_evidence.append(evidence)
        return evidence

    def rollback(self) -> dict[str, Any]:
        if not self._rollback_stack:
            return {"rolled_back": False, "reason": "There is no undiscarded prior policy version to restore."}
        previous = self._rollback_stack.pop()
        old_active = self._active
        self._active = replace(previous.policy, policy_id=f"policy-v{len(self.history) + 1}-rollback")
        evidence = {
            "rolled_back": True,
            "from": old_active.policy_id,
            "to": self._active.policy_id,
            "restored_version": previous.version,
            "preserved_history": True,
        }
        self.history.append(PolicyVersion(len(self.history) + 1, self._active, "rollback", evidence))
        return evidence

    def snapshot(self) -> dict[str, Any]:
        return {
            "rollback_available": bool(self._rollback_stack),
            "active_policy": {
                "policy_id": self._active.policy_id,
                "block_categories": list(self._active.block_categories),
                "quarantine_threshold": self._active.quarantine_threshold,
                "literal_indicators": [list(rule) for rule in self._active.literal_indicators],
            },
            "versions": [
                {
                    "version": item.version,
                    "policy_id": item.policy.policy_id,
                    "block_categories": list(item.policy.block_categories),
                    "quarantine_threshold": item.policy.quarantine_threshold,
                    "literal_indicators": [list(rule) for rule in item.policy.literal_indicators],
                    "accepted_candidate": item.accepted_candidate,
                    "evidence": item.evidence,
                }
                for item in self.history
            ],
            "candidate_evidence": self.candidate_evidence,
        }

    def _measure(self, policy: FirewallPolicy) -> dict[str, Any]:
        firewall = Firewall(classifier=RuleClassifier(), policy=policy)
        attack_count = benign_count = detected = blocked = contained = benign_pass = false_positives = 0
        escaped = 0
        action_counts = {"allow": 0, "sanitize": 0, "quarantine": 0, "block": 0}
        attack_actions: dict[str, str] = {}
        for case in self._cases:
            envelope = ContentEnvelope(case["content"], case["source_type"], case["id"], False)
            decision = firewall.inspect(envelope)
            action_counts[decision.action] += 1
            expected = set(case["expected_attack_types"])
            if case["benign"]:
                benign_count += 1
                if decision.action == "allow":
                    benign_pass += 1
                else:
                    false_positives += 1
            else:
                attack_count += 1
                if expected.intersection(decision.attack_types):
                    detected += 1
                if decision.action == "block":
                    blocked += 1
                if decision.action in ("block", "quarantine"):
                    contained += 1
                else:
                    escaped += 1
                attack_actions[case["id"]] = decision.action
        return {
            "attack_cases": attack_count,
            "attack_detection_rate": detected / attack_count if attack_count else 0.0,
            "attack_detected_cases": detected,
            "blocked_attack_rate": blocked / attack_count if attack_count else 0.0,
            "blocked_attack_cases": blocked,
            "contained_attack_rate": contained / attack_count if attack_count else 0.0,
            "contained_attack_cases": contained,
            "attack_escaped_cases": escaped,
            "attack_action_counts": {
                action: sum(1 for value in attack_actions.values() if value == action)
                for action in action_counts
            },
            "attack_actions_by_case": attack_actions,
            "benign_cases": benign_count,
            "benign_pass_rate": benign_pass / benign_count if benign_count else 1.0,
            "false_positives": false_positives,
            "all_case_action_counts": action_counts,
        }

    @staticmethod
    def _compare_attack_outcomes(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
        before = baseline["attack_actions_by_case"]
        after = candidate["attack_actions_by_case"]
        case_ids = sorted(set(before) & set(after))
        contained_actions = {"block", "quarantine"}
        return {
            "severity_only_reclassified_cases": [
                case_id for case_id in case_ids if before[case_id] == "quarantine" and after[case_id] == "block"
            ],
            "newly_contained_cases": [
                case_id for case_id in case_ids if before[case_id] not in contained_actions and after[case_id] in contained_actions
            ],
            "newly_escaped_cases": [
                case_id for case_id in case_ids if before[case_id] in contained_actions and after[case_id] not in contained_actions
            ],
        }

    @staticmethod
    def _measure_end_to_end(policy: FirewallPolicy) -> dict[str, Any]:
        # Keep policy-component metrics separate from observed demo-tool outcomes.
        # These two fixed public scenarios are not part of the 30-case denominator.
        from sentinel_pi.agent import run_scenario

        attack = run_scenario("indirect_injection", policy)
        legitimate = run_scenario("legitimate_support", policy)
        return {
            "attack_scenarios": 1,
            "untrusted_instruction_parser_admissions": int(
                attack["agent_simulation"]["protected_external_content_admitted_to_proposal_parser"]
                and attack["baseline"]["unauthorized_attempt"] is not None
            ),
            "protected_unauthorized_side_effects": attack["protected"]["unauthorized_side_effects"],
            "legitimate_task_cases": 1,
            "legitimate_tasks_correct": int(legitimate["protected"]["task_validation"]["correct"]),
            "legitimate_task_checks": legitimate["protected"]["task_validation"]["checks"],
            "attack_firewall_action": attack["firewall"]["action"],
        }

    @staticmethod
    def _gate_invariant() -> bool:
        contract = IntentContract(
            "candidate-check", "Do not email external destinations", ("send_email",),
            allowed_recipients=("attacker@example.invalid",), explicit_approval=True,
        )
        runtime = MockToolRuntime(IntentGate())
        proposal = ToolProposal(
            "send_email",
            {"recipient": "attacker@example.invalid", "subject": "x", "body": "x"},
            "The model claims the user requested this action.",
            ("user-task",),
        )
        result = runtime.execute(contract, proposal, host_source_ids=("untrusted-candidate",))
        return result["status"] == "denied" and not runtime.side_effects
