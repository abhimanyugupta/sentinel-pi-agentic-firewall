"""Persistent, cumulative approval gate for local model requests.

This module records reservations before a generation or warm-up request is sent.
It does not contact Ollama. The default allowance is intentionally below the
already-recorded history, so no new request can run without a later human
approval recorded in BUDGET_APPROVALS.json.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

KINDS = ("generation", "warmup")
APPROVAL_PHRASE = "I APPROVE THIS MODEL CALL BUDGET INCREASE"
REFERENCE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,63}$")
ROOT = Path(__file__).resolve().parent


class BudgetExhausted(RuntimeError):
    """No call may be sent under the current cumulative approval."""


class BudgetError(ValueError):
    """The persistent budget or approval record is malformed."""


class BudgetGuard:
    def __init__(self, root: str | Path = ROOT, lock_path: str | Path | None = None):
        self.root = Path(root)
        self.policy_path = self.root / "BUDGET_POLICY.json"
        self.state_path = self.root / "BUDGET_STATE.json"
        self.approvals_path = self.root / "BUDGET_APPROVALS.json"
        self.evidence_dir = self.root / "evidence"
        self.lock_path = Path(lock_path) if lock_path is not None else (
            self.root.parent.parent / "artifacts" / "runtime" / "gemma3-budget.lock"
        )

    @contextmanager
    def _lock(self):
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        with self.lock_path.open("a+b") as handle:
            if os.name == "nt":
                import msvcrt

                handle.seek(0)
                if handle.read(1) == b"":
                    handle.write(b"\0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
                try:
                    yield
                finally:
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def _read(path: Path) -> dict:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise BudgetError("budget_record_unavailable_or_invalid") from exc
        if not isinstance(value, dict):
            raise BudgetError("budget_record_schema")
        return value

    @staticmethod
    def _write(path: Path, value: dict) -> None:
        temporary = path.with_name(path.name + ".tmp")
        text = json.dumps(value, indent=2, ensure_ascii=True) + "\n"
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)

    def _history(self, kind: str) -> int:
        if kind == "generation":
            total = 0
            for path in sorted(self.evidence_dir.glob("run-*.json")):
                report = self._read(path)
                attempts = report.get("requests_attempted")
                if type(attempts) is not int or attempts < 0:
                    raise BudgetError("generation_history_schema")
                total += attempts
            return total
        if kind == "warmup":
            # Every warm-up record follows one /api/chat load diagnostic. Count
            # every record, including a failed diagnostic, to avoid free retries.
            return sum(1 for _ in self.evidence_dir.glob("warmup-*.json"))
        raise BudgetError("budget_kind")

    def _usage(self, state: dict, kind: str) -> int:
        try:
            baseline = state["baseline_usage"][kind]
            reservations = state["reservations"][kind]
            if type(baseline) is not int or baseline < 0 or not isinstance(reservations, list):
                raise TypeError
        except (KeyError, TypeError) as exc:
            raise BudgetError("budget_state_schema") from exc
        return max(self._history(kind), baseline + len(reservations))

    def _limit(self, policy: dict, approvals: dict, kind: str) -> int:
        try:
            base = policy["limits"][kind]
            records = approvals["approvals"]
            if type(base) is not int or base < 0 or not isinstance(records, list):
                raise TypeError
        except (KeyError, TypeError) as exc:
            raise BudgetError("budget_policy_schema") from exc
        approved = [item.get("limit") for item in records
                    if isinstance(item, dict) and item.get("kind") == kind]
        if any(type(item) is not int or item < 0 for item in approved):
            raise BudgetError("budget_approval_schema")
        return max([base, *approved])

    def _snapshot(self) -> dict:
        policy = self._read(self.policy_path)
        state = self._read(self.state_path)
        approvals = self._read(self.approvals_path)
        result = {"schema_version": 1, "kinds": {}}
        for kind in KINDS:
            used = self._usage(state, kind)
            limit = self._limit(policy, approvals, kind)
            result["kinds"][kind] = {"used": used, "limit": limit,
                                     "remaining": max(0, limit - used),
                                     "exhausted": used >= limit}
        return result

    def status(self) -> dict:
        with self._lock():
            return self._snapshot()

    def require_capacity(self, kind: str, calls: int = 1) -> None:
        if kind not in KINDS or type(calls) is not int or calls < 1:
            raise BudgetError("budget_request_schema")
        with self._lock():
            snapshot = self._snapshot()["kinds"][kind]
            if snapshot["used"] + calls > snapshot["limit"]:
                raise BudgetExhausted(
                    f"cumulative_budget_exhausted:{kind}:{snapshot['used']}/{snapshot['limit']}; "
                    "a separately recorded human approval is required"
                )

    def reserve(self, kind: str) -> dict:
        """Atomically consume one cumulative allowance before the HTTP request."""
        if kind not in KINDS:
            raise BudgetError("budget_kind")
        with self._lock():
            policy = self._read(self.policy_path)
            state = self._read(self.state_path)
            approvals = self._read(self.approvals_path)
            used = self._usage(state, kind)
            limit = self._limit(policy, approvals, kind)
            if used + 1 > limit:
                raise BudgetExhausted(
                    f"cumulative_budget_exhausted:{kind}:{used}/{limit}; "
                    "a separately recorded human approval is required"
                )
            reservation = {"id": uuid.uuid4().hex, "kind": kind,
                           "reserved_at_utc": datetime.now(timezone.utc).isoformat()}
            state["reservations"][kind].append(reservation)
            self._write(self.state_path, state)
            return reservation

    def approve_increase(self, kind: str, limit: int, authorization_reference: str,
                         confirmation: str) -> dict:
        """Record an explicit human increase; never called by a model or test runner."""
        if kind not in KINDS or type(limit) is not int or limit < 1:
            raise BudgetError("approval_request_schema")
        if not REFERENCE_RE.fullmatch(authorization_reference or ""):
            raise BudgetError("approval_reference_schema")
        if confirmation != APPROVAL_PHRASE:
            raise BudgetError("human_confirmation_required")
        with self._lock():
            policy = self._read(self.policy_path)
            state = self._read(self.state_path)
            approvals = self._read(self.approvals_path)
            current = self._limit(policy, approvals, kind)
            used = self._usage(state, kind)
            if limit <= current or limit <= used:
                raise BudgetError("approval_must_extend_current_budget_and_cover_usage")
            record = {"kind": kind, "limit": limit,
                      "authorization_reference": authorization_reference,
                      "approved_by": "human_operator_attestation",
                      "recorded_at_utc": datetime.now(timezone.utc).isoformat()}
            approvals["approvals"].append(record)
            self._write(self.approvals_path, approvals)
            return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="show recorded cumulative use without model access")
    approval = commands.add_parser("approve", help="record a human-approved increase; no model access")
    approval.add_argument("--kind", choices=KINDS, required=True)
    approval.add_argument("--new-limit", type=int, required=True)
    approval.add_argument("--authorization-reference", required=True)
    args = parser.parse_args(argv)
    guard = BudgetGuard()
    try:
        if args.command == "status":
            result = guard.status()
        else:
            print("This changes the persistent request allowance; it does not make a model request.")
            confirmation = input(f"Type exactly: {APPROVAL_PHRASE}\n> ")
            result = guard.approve_increase(args.kind, args.new_limit,
                                            args.authorization_reference, confirmation)
    except (BudgetError, BudgetExhausted) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
