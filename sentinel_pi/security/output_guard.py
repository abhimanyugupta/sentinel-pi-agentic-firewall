"""Final-answer checks for synthetic secrets and fixture-labeled unsupported claims."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class OutputGuardResult:
    allowed: bool
    text: str
    findings: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {"allowed": self.allowed, "text": self.text, "findings": list(self.findings)}


class OutputGuard:
    def __init__(self, canaries: tuple[str, ...]) -> None:
        self.canaries = tuple(value for value in canaries if isinstance(value, str) and value)

    def inspect(
        self,
        answer: str,
        *,
        unsupported_claims: tuple[str, ...] = (),
    ) -> OutputGuardResult:
        if not isinstance(answer, str):
            return OutputGuardResult(False, "I cannot provide a response because output validation failed.", ("malformed_output",))
        if (
            not isinstance(unsupported_claims, tuple)
            or len(unsupported_claims) > 32
            or any(not isinstance(claim, str) or not claim.strip() or len(claim) > 240 for claim in unsupported_claims)
        ):
            return OutputGuardResult(False, "I cannot provide a response because output evidence was invalid.", ("malformed_claim_evidence",))
        redacted = answer
        findings: list[str] = []
        for index, claim in enumerate(unsupported_claims, start=1):
            pattern = re.compile(r"(?<!\w)" + re.escape(claim.strip()) + r"(?!\w)", re.I)
            if pattern.search(redacted):
                redacted = pattern.sub("[UNVERIFIED CLAIM REDACTED]", redacted)
                findings.append(f"unverified_claim_{index}")
        for index, canary in enumerate(self.canaries, start=1):
            if canary.casefold() in redacted.casefold():
                redacted = re.sub(re.escape(canary), "[REDACTED SYNTHETIC SECRET]", redacted, flags=re.I)
                findings.append(f"synthetic_canary_{index}")
        if findings:
            return OutputGuardResult(False, redacted, tuple(findings))
        return OutputGuardResult(True, answer, ())
