"""Small typed contracts shared by the firewall, agent, evaluator, and UI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

ATTACK_TYPES = (
    "instruction_override",
    "role_change",
    "secret_extraction",
    "tool_abuse",
    "credential_theft",
    "context_poisoning",
    "multi_step_jailbreak",
    "encoded_instructions",
    "indirect_prompt_injection",
)
SOURCE_TYPES = ("user", "html", "pdf", "email", "markdown", "api", "code", "ocr")
FIREWALL_ACTIONS = ("allow", "sanitize", "quarantine", "block")


@dataclass(frozen=True)
class ContentEnvelope:
    content: str
    source_type: str
    source_id: str
    trusted: bool = False

    def validate(self) -> None:
        if not isinstance(self.content, str):
            raise ValueError("content must be a string")
        if len(self.content) > 100_000:
            raise ValueError("content exceeds the 100000 character limit")
        if self.source_type not in SOURCE_TYPES:
            raise ValueError("unsupported source_type")
        if not isinstance(self.source_id, str) or not self.source_id or len(self.source_id) > 96:
            raise ValueError("source_id must be a non-empty string of at most 96 characters")
        if not isinstance(self.trusted, bool):
            raise ValueError("trusted must be a boolean")


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    attack_type: str


@dataclass(frozen=True)
class Provenance:
    source_type: str
    source_id: str
    trusted: bool
    content_sha256: str
    decoded_payloads: int = 0
    transforms: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "source_id": self.source_id,
            "trusted": self.trusted,
            "content_sha256": self.content_sha256,
            "decoded_payloads": self.decoded_payloads,
            "transforms": list(self.transforms),
        }


@dataclass(frozen=True)
class Classification:
    attack_types: tuple[str, ...] = ()
    spans: tuple[Span, ...] = ()
    rationale: tuple[str, ...] = ()


@dataclass(frozen=True)
class FirewallDecision:
    attack_types: tuple[str, ...]
    suspicious_spans: tuple[Span, ...]
    risk_score: float
    action: str
    rationale: tuple[str, ...]
    provenance: Provenance
    sanitized_content: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "attack_types": list(self.attack_types),
            "suspicious_spans": [
                {"start": s.start, "end": s.end, "attack_type": s.attack_type}
                for s in self.suspicious_spans
            ],
            "risk_score": round(self.risk_score, 4),
            "action": self.action,
            "rationale": list(self.rationale),
            "provenance": self.provenance.to_dict(),
            "sanitized_content": self.sanitized_content,
        }


@dataclass(frozen=True)
class IntentContract:
    task_id: str
    task: str
    permitted_tools: tuple[str, ...]
    allowed_customer_ids: tuple[str, ...] = ()
    allowed_recipients: tuple[str, ...] = ()
    approval_required_for: tuple[str, ...] = ("send_email",)
    allowed_ticket_categories: tuple[str, ...] = ("hardware_support",)
    explicit_approval: bool = False
    max_ticket_creations: int = 1
    authorized_action_source_ids: tuple[str, ...] = ("user-task",)


@dataclass(frozen=True)
class ToolProposal:
    tool: str
    arguments: dict[str, Any]
    reason: str
    source_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class GateDecision:
    outcome: str
    reason: str
    policy_id: str
    tool: str

    @property
    def allowed(self) -> bool:
        return self.outcome == "allow"

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "outcome": self.outcome,
            "reason": self.reason,
            "policy_id": self.policy_id,
            "tool": self.tool,
            "allowed": self.allowed,
        }


@dataclass
class ScenarioEvent:
    event_id: str
    scenario_id: str
    title: str
    source_type: str
    source_id: str
    content: str
    decision: FirewallDecision
    proposed_calls: list[dict[str, Any]] = field(default_factory=list)
    gate_decisions: list[dict[str, Any]] = field(default_factory=list)
    side_effects: list[dict[str, Any]] = field(default_factory=list)
    answer: str = ""
    answer_guard: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    baseline: dict[str, Any] = field(default_factory=dict)


def parse_classification(value: Any, content_length: int) -> Classification:
    """Validate classifier output as a closed, typed schema."""
    if isinstance(value, Classification):
        result = value
    elif isinstance(value, dict):
        if set(value) != {"attack_types", "spans", "rationale"}:
            raise ValueError("classifier output has unknown or missing fields")
        if not isinstance(value["attack_types"], (list, tuple)) or not isinstance(value["rationale"], (list, tuple)):
            raise ValueError("classifier categories and rationale must be arrays")
        raw_spans = value["spans"]
        if not isinstance(raw_spans, (list, tuple)):
            raise ValueError("classifier spans must be a list")
        spans: list[Span] = []
        for item in raw_spans:
            if not isinstance(item, dict) or set(item) != {"start", "end", "attack_type"}:
                raise ValueError("classifier span has unknown or missing fields")
            spans.append(Span(item["start"], item["end"], item["attack_type"]))
        result = Classification(tuple(value["attack_types"]), tuple(spans), tuple(value["rationale"]))
    else:
        raise ValueError("classifier result is not a supported schema")

    if not isinstance(result.attack_types, tuple) or not isinstance(result.rationale, tuple):
        raise ValueError("classifier categories and rationale must be tuples")
    if any(not isinstance(t, str) or t not in ATTACK_TYPES for t in result.attack_types):
        raise ValueError("classifier returned an unsupported attack type")
    if any(not isinstance(item, str) or len(item) > 240 for item in result.rationale):
        raise ValueError("classifier rationale must contain short strings")
    if any(not isinstance(span, Span) for span in result.spans):
        raise ValueError("classifier spans must use the Span schema")
    for span in result.spans:
        if (
            not isinstance(span.start, int)
            or not isinstance(span.end, int)
            or span.start < 0
            or span.end <= span.start
            or span.end > content_length
            or span.attack_type not in ATTACK_TYPES
        ):
            raise ValueError("classifier returned an invalid span")
    if len(result.attack_types) > len(ATTACK_TYPES) or len(result.spans) > 64:
        raise ValueError("classifier output exceeds the schema limits")
    return result
