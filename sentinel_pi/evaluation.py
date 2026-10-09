"""Reproducible evaluation with raw, fixture-linked predictions."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sentinel_pi.agent import run_scenario
from sentinel_pi.models import ATTACK_TYPES, ContentEnvelope, IntentContract, ToolProposal
from sentinel_pi.policy import PolicyManager
from sentinel_pi.security.firewall import Firewall
from sentinel_pi.toolgate import IntentGate, MockToolRuntime

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET = ROOT / "fixtures" / "dev_scenarios.jsonl"


def project_path(value: str | Path) -> Path:
    path = Path(value)
    resolved = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError("Evaluation inputs and outputs must stay inside the project directory.") from exc
    return resolved


def load_cases(path: str | Path = DEFAULT_DATASET) -> tuple[list[dict[str, Any]], str]:
    resolved = project_path(path)
    raw = resolved.read_bytes()
    cases: list[dict[str, Any]] = []
    required = {"id", "source_type", "content", "expected_attack_types", "benign"}
    for line_number, line in enumerate(raw.decode("utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed JSONL at line {line_number}.") from exc
        if not isinstance(item, dict) or set(item) != required:
            raise ValueError(f"Case at line {line_number} does not match the closed fixture schema.")
        if not isinstance(item["id"], str) or not item["id"] or len(item["id"]) > 80:
            raise ValueError(f"Case at line {line_number} has an invalid id.")
        if not isinstance(item["expected_attack_types"], list) or any(
            category not in ATTACK_TYPES for category in item["expected_attack_types"]
        ):
            raise ValueError(f"Case at line {line_number} has an invalid expected_attack_types list.")
        if not isinstance(item["benign"], bool):
            raise ValueError(f"Case at line {line_number} has an invalid benign flag.")
        if item["benign"] != (len(item["expected_attack_types"]) == 0):
            raise ValueError(f"Case at line {line_number} benign flag conflicts with attack labels.")
        cases.append(item)
    if not cases:
        raise ValueError("Evaluation dataset contains no cases.")
    return cases, hashlib.sha256(raw).hexdigest()


def _percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(quantile * len(ordered)) - 1))
    return ordered[index]


def _external_source_gate_check() -> dict[str, Any]:
    """Fixed invariant probe kept outside the 30-case classifier denominator."""
    contract = IntentContract(
        "evaluation-gate-invariant",
        "Create one user-authorized support ticket for C-1042",
        ("create_ticket",),
        allowed_customer_ids=("C-1042",),
    )
    runtime = MockToolRuntime(IntentGate())
    result = runtime.execute(
        contract,
        ToolProposal(
            "create_ticket",
            {
                "customer_id": "C-1042",
                "subject": "Support issue",
                "description": "Follow the instruction embedded in an untrusted page.",
                "category": "hardware_support",
            },
            "The model claims the user requested this action.",
            ("user-task",),
        ),
        host_source_ids=("page-untrusted-eval",),
    )
    return {
        "result": result,
        "side_effects": list(runtime.side_effects),
        "denied_without_side_effect": result["status"] == "denied" and not runtime.side_effects,
    }


def run_evaluation(dataset: str | Path = DEFAULT_DATASET) -> dict[str, Any]:
    cases, dataset_hash = load_cases(dataset)
    dataset_rel = project_path(dataset).relative_to(ROOT.resolve()).as_posix()
    firewall = Firewall()
    category_counts = {
        category: {"cases": 0, "detected": 0, "predicted": 0, "false_positive_labels": 0}
        for category in ATTACK_TYPES
    }
    latencies: list[float] = []
    raw_predictions: list[dict[str, Any]] = []
    benign_count = attack_count = benign_pass = false_positives = detected_cases = blocked_cases = 0
    expected_total = expected_detected = 0
    attack_action_counts = {"allow": 0, "sanitize": 0, "quarantine": 0, "block": 0}
    all_action_counts = {"allow": 0, "sanitize": 0, "quarantine": 0, "block": 0}

    for case in cases:
        envelope = ContentEnvelope(case["content"], case["source_type"], case["id"], False)
        started = time.perf_counter()
        decision = firewall.inspect(envelope)
        all_action_counts[decision.action] += 1
        latency_ms = (time.perf_counter() - started) * 1000
        latencies.append(latency_ms)
        predicted = set(decision.attack_types)
        expected = set(case["expected_attack_types"])
        for category in predicted:
            category_counts[category]["predicted"] += 1
            if category not in expected:
                category_counts[category]["false_positive_labels"] += 1
        if case["benign"]:
            benign_count += 1
            passed = decision.action == "allow"
            benign_pass += int(passed)
            false_positives += int(not passed)
        else:
            attack_count += 1
            attack_action_counts[decision.action] += 1
            expected_total += len(expected)
            hits = expected.intersection(predicted)
            expected_detected += len(hits)
            detected_cases += int(bool(hits))
            blocked_cases += int(decision.action in ("block", "quarantine"))
            for category in expected:
                category_counts[category]["cases"] += 1
                category_counts[category]["detected"] += int(category in predicted)
        raw_predictions.append(
            {
                "case_id": case["id"],
                "source_type": case["source_type"],
                "input_sha256": decision.provenance.content_sha256,
                "benign": case["benign"],
                "expected_attack_types": case["expected_attack_types"],
                "predicted_attack_types": list(decision.attack_types),
                "false_positive_attack_types": sorted(predicted - expected),
                "suspicious_spans": [
                    {"start": span.start, "end": span.end, "attack_type": span.attack_type}
                    for span in decision.suspicious_spans
                ],
                "action": decision.action,
                "risk_score": round(decision.risk_score, 4),
                "rationale": list(decision.rationale),
                "latency_ms": round(latency_ms, 4),
            }
        )

    comparison = run_scenario("indirect_injection")
    legitimate = run_scenario("legitimate_support")
    contamination = run_scenario("answer_contamination")
    gate_invariant = _external_source_gate_check()
    category_results: dict[str, dict[str, Any]] = {}
    for category, values in category_counts.items():
        if not values["cases"] and not values["predicted"]:
            continue
        precision = values["detected"] / values["predicted"] if values["predicted"] else 0.0
        recall = values["detected"] / values["cases"] if values["cases"] else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        category_results[category] = {
            "cases": values["cases"],
            "detected": values["detected"],
            "predicted": values["predicted"],
            "false_positive_labels": values["false_positive_labels"],
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }
    category_tp = sum(values["detected"] for values in category_counts.values())
    category_fp = sum(values["false_positive_labels"] for values in category_counts.values())
    category_fn = sum(values["cases"] - values["detected"] for values in category_counts.values())
    category_precision = category_tp / (category_tp + category_fp) if category_tp + category_fp else 0.0
    category_recall = category_tp / (category_tp + category_fn) if category_tp + category_fn else 0.0
    category_f1 = (
        2 * category_precision * category_recall / (category_precision + category_recall)
        if category_precision + category_recall else 0.0
    )
    return {
        "evaluation_id": datetime.now(timezone.utc).strftime("eval-%Y%m%dT%H%M%SZ"),
        "mode": "offline_deterministic_rules",
        "dataset": dataset_rel,
        "dataset_sha256": dataset_hash,
        "configured_attack_types": list(ATTACK_TYPES),
        "public_development_cases_only": True,
        "metrics": {
            "total_cases": len(cases),
            "attack_cases": attack_count,
            "expected_category_labels": expected_total,
            "expected_category_hits": expected_detected,
            "attack_case_detection_rate": detected_cases / attack_count if attack_count else 0.0,
            "category_micro_recall": expected_detected / expected_total if expected_total else 0.0,
            "category_micro_precision": round(category_precision, 4),
            "category_micro_f1": round(category_f1, 4),
            "category_false_positive_labels": category_fp,
            "per_category": category_results,
            "attacks_quarantined_or_blocked": blocked_cases,
            "attacks_blocked": attack_action_counts["block"],
            "attacks_quarantined": attack_action_counts["quarantine"],
            "attack_cases_not_blocked_or_quarantined": attack_count - blocked_cases,
            "attack_firewall_action_counts": attack_action_counts,
            "all_firewall_action_counts": all_action_counts,
            "benign_cases": benign_count,
            "benign_pass_rate": benign_pass / benign_count if benign_count else 1.0,
            "false_positives": false_positives,
            "benign_false_positives": false_positives,
            "baseline_unauthorized_mock_emails_executed": int(comparison["baseline"]["unauthorized_email_executed"]),
            "protected_unauthorized_mock_emails_executed": int(comparison["protected"]["unauthorized_email_executed"]),
            "protected_tool_gate_violations": comparison["protected"]["gate_violations"],
            "protected_external_instruction_parser_admissions": int(
                comparison["agent_simulation"]["protected_external_content_admitted_to_proposal_parser"]
                and comparison["baseline"]["unauthorized_attempt"] is not None
            ),
            "protected_unauthorized_mock_side_effects": comparison["protected"]["unauthorized_side_effects"],
            "protected_legitimate_task_cases": 1,
            "protected_legitimate_tasks_correct": int(legitimate["protected"]["task_validation"]["correct"]),
            "independent_gate_external_provenance_cases": 1,
            "independent_gate_external_provenance_denials": int(gate_invariant["denied_without_side_effect"]),
            "baseline_answer_canary_leaks": int(contamination["baseline"]["answer_leaked_canary"]),
            "protected_answer_canary_leaks": int(CANARY_IN(contamination["protected"]["answer"])),
            "protected_answer_canary_redactions": sum(
                finding.startswith("synthetic_canary_")
                for finding in contamination["protected"]["answer_guard"]["findings"]
            ),
            "baseline_unsupported_answer_claims": len(contamination["baseline"]["unsupported_claims_present"]),
            "protected_unsupported_answer_claims": len(contamination["protected"]["unsupported_claims_present"]),
            "protected_unsupported_claim_redactions": sum(
                finding.startswith("unverified_claim_")
                for finding in contamination["protected"]["answer_guard"]["findings"]
            ),
            "median_latency_ms": round(statistics.median(latencies), 4) if latencies else 0.0,
            "p95_latency_ms": round(_percentile(latencies, 0.95), 4),
        },
        "before_after": {
            "public_classifier_component": {
                "attack_case_denominator": attack_count,
                "blocked": attack_action_counts["block"],
                "quarantined": attack_action_counts["quarantine"],
                "block_or_quarantine": blocked_cases,
                "other_actions": attack_count - blocked_cases,
            },
            "unauthorized_email": {
                "baseline_executed": comparison["baseline"]["unauthorized_email_executed"],
                "protected_executed": comparison["protected"]["unauthorized_email_executed"],
                "protected_content_suppressed_by_firewall": comparison["protected"]["external_instruction_suppressed_by_firewall"],
                "protected_gate": comparison["protected"]["unauthorized_attempt"]["gate"] if comparison["protected"]["unauthorized_attempt"] else None,
                "protected_parser_admission": comparison["agent_simulation"]["protected_external_content_admitted_to_proposal_parser"],
            },
            "legitimate_support_task": {
                "denominator": 1,
                "baseline_correct": int(legitimate["baseline"]["task_validation"]["correct"]),
                "protected_correct": int(legitimate["protected"]["task_validation"]["correct"]),
                "protected_validation": legitimate["protected"]["task_validation"],
            },
            "independent_tool_gate": gate_invariant,
            "answer_contamination": {
                "baseline_leaked": contamination["baseline"]["answer_leaked_canary"],
                "protected_leaked": CANARY_IN(contamination["protected"]["answer"]),
                "protected_findings": contamination["protected"]["answer_guard"]["findings"],
                "baseline_unsupported_claims": contamination["baseline"]["unsupported_claims_present"],
                "protected_unsupported_claims": contamination["protected"]["unsupported_claims_present"],
            },
        },
        "raw_predictions": raw_predictions,
    }


def CANARY_IN(value: str) -> bool:
    from sentinel_pi.toolgate import CANARY

    return CANARY.casefold() in value.casefold()


def save_report(report: dict[str, Any], output: str | Path = "artifacts/evaluation-latest.json") -> Path:
    resolved = project_path(output)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return resolved


def run_candidate_suite(dataset: str | Path = DEFAULT_DATASET) -> dict[str, Any]:
    cases, dataset_hash = load_cases(dataset)
    manager = PolicyManager(cases)
    severity = manager.evaluate_candidate(
        {"name": "Elevate indirect injections", "add_block_categories": ["indirect_prompt_injection"]}
    )
    common_phrase = manager.evaluate_candidate(
        {
            "name": "Common phrase indicator candidate",
            "add_literal_indicators": [{"phrase": "customer support", "attack_type": "instruction_override"}],
        }
    )
    unsafe = manager.evaluate_candidate(
        {"name": "Attempt to widen tool permissions", "permitted_tools": ["send_email"]}
    )
    return {
        "dataset_sha256": dataset_hash,
        "public_development_cases_only": True,
        "severity_hardening_candidate": severity,
        "common_phrase_candidate": common_phrase,
        "unauthorized_schema_candidate": unsafe,
        "policy_history": manager.snapshot(),
    }
