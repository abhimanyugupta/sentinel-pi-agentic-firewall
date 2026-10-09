"""Firewall orchestration and safe classifier fallback."""

from __future__ import annotations

from dataclasses import dataclass

from sentinel_pi.models import (
    ATTACK_TYPES,
    FIREWALL_ACTIONS,
    Classification,
    ContentEnvelope,
    FirewallDecision,
    Provenance,
    parse_classification,
)
from sentinel_pi.security.preprocess import Preprocessor
from sentinel_pi.security.rules import Classifier, RuleClassifier, apply_literal_indicators


@dataclass(frozen=True)
class FirewallPolicy:
    policy_id: str = "policy-v1"
    block_categories: tuple[str, ...] = (
        "secret_extraction",
        "credential_theft",
        "tool_abuse",
    )
    quarantine_threshold: float = 0.45
    literal_indicators: tuple[tuple[str, str], ...] = ()


class Firewall:
    def __init__(
        self,
        classifier: Classifier | None = None,
        preprocessor: Preprocessor | None = None,
        policy: FirewallPolicy | None = None,
        safe_fallback: str = "quarantine",
    ) -> None:
        if safe_fallback not in FIREWALL_ACTIONS:
            raise ValueError("safe_fallback must be a known firewall action")
        if safe_fallback == "allow":
            raise ValueError("safe_fallback cannot allow content after classifier failure")
        self.classifier = classifier or RuleClassifier()
        self.preprocessor = preprocessor or Preprocessor()
        self.policy = policy or FirewallPolicy()
        self.safe_fallback = safe_fallback

    def inspect(self, envelope: ContentEnvelope) -> FirewallDecision:
        prepared = self.preprocessor.prepare(envelope)
        try:
            classification = parse_classification(self.classifier.classify(prepared), len(envelope.content))
            if self.policy.literal_indicators:
                classification = apply_literal_indicators(
                    prepared, classification, self.policy.literal_indicators
                )
        except Exception as exc:  # fail closed on provider exceptions and schema violations
            return FirewallDecision(
                attack_types=(),
                suspicious_spans=(),
                risk_score=0.65,
                action=self.safe_fallback,
                rationale=(f"Classifier unavailable or invalid ({type(exc).__name__}); safe fallback applied.",),
                provenance=prepared.provenance,
            )
        return self._decision(prepared.provenance, classification)

    def _decision(self, provenance: Provenance, classification: Classification) -> FirewallDecision:
        categories = classification.attack_types
        if not categories:
            return FirewallDecision((), (), 0.02, "allow", ("No configured attack indicator matched.",), provenance)

        severe = set(categories).intersection(self.policy.block_categories)
        score = min(0.99, 0.38 + 0.11 * len(categories) + (0.22 if severe else 0.0))
        if severe or score >= self.policy.quarantine_threshold + 0.28:
            action = "block"
        elif score >= self.policy.quarantine_threshold:
            action = "quarantine"
        else:
            action = "sanitize"
        rationales = list(classification.rationale)
        rationales.append(f"Policy {self.policy.policy_id} selected {action} at risk {score:.2f}.")
        return FirewallDecision(
            attack_types=categories,
            suspicious_spans=classification.spans,
            risk_score=score,
            action=action,
            rationale=tuple(rationales),
            provenance=provenance,
        )


class FixedClassifier:
    """Test seam for structured classifier implementations and failure cases."""

    def __init__(self, result: object = Classification(), error: Exception | None = None) -> None:
        self.result = result
        self.error = error

    def classify(self, prepared):
        if self.error is not None:
            raise self.error
        return self.result
