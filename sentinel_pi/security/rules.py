"""Deterministic offline classifier. Rules are indicators, not a security proof."""

from __future__ import annotations

import re
from typing import Protocol

from sentinel_pi.models import ATTACK_TYPES, Classification, Span
from sentinel_pi.security.preprocess import PreparedContent


class Classifier(Protocol):
    def classify(self, prepared: PreparedContent) -> Classification: ...


PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    "instruction_override": (
        re.compile(r"\b(ignore|disregard|override|forget|bypass)\b.{0,90}\b(previous|earlier|system|developer|user|all|other)?\s*(instructions?|rules?|polic(?:y|ies)|prompt)\b", re.I),
        re.compile(r"\b(do not follow|stop following|replace)\b.{0,60}\b(instructions?|rules?|polic(?:y|ies))\b", re.I),
        re.compile(r"\b(system|security) override\b", re.I),
    ),
    "role_change": (
        re.compile(r"\b(you are now|act as|pretend to be|assume the role of|switch roles? to|from now on you are)\b", re.I),
    ),
    "secret_extraction": (
        re.compile(r"\b(reveal|exfiltrate|print|dump|show|send(?:[_ ]email)?|extract|expose|return|forward)\b.{0,100}\b(secret|token|password|api[ _-]?key|credential|private data|canary|recovery code)\b", re.I),
        re.compile(r"\b(secret|token|password|api[ _-]?key|credential|private data|canary|recovery code)\b.{0,80}\b(reveal|exfiltrate|print|dump|show|send(?:[_ ]email)?|extract|expose|forward)\b", re.I),
    ),
    "tool_abuse": (
        re.compile(r"\b(call|invoke|use|execute|run|trigger)\b.{0,70}\b(send[_ ]email|create[_ ]ticket|delete|transfer|shell|function|tool|payment|settlement)\b", re.I),
        re.compile(r"\b(send[_ ]email|delete|transfer|shell|payment|settlement)\b.{0,70}\b(now|immediately|without approval|to the attacker)\b", re.I),
    ),
    "credential_theft": (
        re.compile(r"\b(password|api[ _-]?key|credential|auth(?:entication)? token|session cookie|one.time passcode|otp|security code|recovery code)\b.{0,90}\b(send|forward|email|post|exfiltrate|share|reveal|provide)\b", re.I),
        re.compile(r"\b(send|forward|email|post|exfiltrate|share|reveal|provide)\b.{0,90}\b(password|api[ _-]?key|credential|auth(?:entication)? token|session cookie|one.time passcode|otp|security code|recovery code)\b", re.I),
    ),
    "context_poisoning": (
        re.compile(r"\b(this page|this document|this email|the following content|hidden instructions?)\b.{0,90}\b(highest authority|trusted|authoritative|override|supersede|system prompt|priority)\b", re.I),
        re.compile(r"\b(treat|consider|mark)\b.{0,70}\b(as trusted|as the system|highest priority|authoritative)\b", re.I),
    ),
    "multi_step_jailbreak": (
        re.compile(r"\b(first|step\s*1)\b.{0,180}\b(then|next|step\s*2)\b.{0,180}\b(finally|after that|step\s*3)\b", re.I | re.S),
        re.compile(r"\b(jailbreak|unlock unrestricted mode)\b.{0,100}\b(first|then|finally|step\s*1)\b", re.I),
    ),
}


class RuleClassifier:
    def classify(self, prepared: PreparedContent) -> Classification:
        categories: set[str] = set()
        spans: list[Span] = []
        rationale: list[str] = []
        original = prepared.envelope.content

        for category, patterns in PATTERNS.items():
            for pattern in patterns:
                for match in pattern.finditer(prepared.normalized_text):
                    if category == "multi_step_jailbreak" and not re.search(
                        r"\b(secret|credential|token|api[ _-]?key|password|send|email|forward|retrieve|exfiltrat|override|bypass|unlock|restricted|admin)\b",
                        match.group(0),
                        re.I,
                    ):
                        continue
                    if category in ("credential_theft", "secret_extraction"):
                        window = prepared.normalized_text[max(0, match.start() - 24):min(len(prepared.normalized_text), match.end() + 48)]
                        if re.search(r"\bpassword reset(?: link)?\b", window, re.I):
                            continue
                    try:
                        start, end = prepared.original_span(match.start(), match.end())
                    except ValueError:
                        continue
                    categories.add(category)
                    spans.append(Span(start, end, category))
                    rationale.append(f"Matched a deterministic {category.replace('_', ' ')} indicator.")
                    break
                if category in categories:
                    break

        for payload in prepared.decoded_payloads:
            payload_has_attack = False
            for category, patterns in PATTERNS.items():
                if any(pattern.search(payload.text) for pattern in patterns):
                    payload_has_attack = True
                    categories.add(category)
                    spans.append(Span(payload.start, payload.end, category))
            if payload_has_attack:
                categories.add("encoded_instructions")
                spans.append(Span(payload.start, payload.end, "encoded_instructions"))
                rationale.append("A bounded Base64 text payload contains an attack indicator.")

        if categories and not prepared.envelope.trusted and prepared.envelope.source_type != "user":
            categories.add("indirect_prompt_injection")
            if not any(span.attack_type == "indirect_prompt_injection" for span in spans):
                first = spans[0]
                spans.append(Span(first.start, first.end, "indirect_prompt_injection"))
            rationale.append("The attack indicator arrived through a lower-trust external source.")

        ordered = tuple(category for category in ATTACK_TYPES if category in categories)
        # Keep evidence bounded and stable; duplicates from multiple rule paths are removed.
        unique: dict[tuple[int, int, str], Span] = {}
        for span in spans:
            if 0 <= span.start < span.end <= len(original):
                unique[(span.start, span.end, span.attack_type)] = span
        return Classification(ordered, tuple(list(unique.values())[:64]), tuple(dict.fromkeys(rationale)))


def apply_literal_indicators(
    prepared: PreparedContent,
    classification: Classification,
    indicators: tuple[tuple[str, str], ...],
) -> Classification:
    """Apply constrained literal indicators from an isolated candidate policy."""
    categories = set(classification.attack_types)
    spans = list(classification.spans)
    rationale = list(classification.rationale)
    normalized = prepared.normalized_text.casefold()
    for phrase, category in indicators:
        needle = phrase.casefold()
        offset = normalized.find(needle)
        if offset < 0:
            continue
        try:
            start, end = prepared.original_span(offset, offset + len(needle))
        except ValueError:
            continue
        categories.add(category)
        spans.append(Span(start, end, category))
        rationale.append(f"Matched a candidate literal indicator for {category.replace('_', ' ')}.")
    ordered = tuple(category for category in ATTACK_TYPES if category in categories)
    unique = {(s.start, s.end, s.attack_type): s for s in spans}
    return Classification(ordered, tuple(list(unique.values())[:64]), tuple(dict.fromkeys(rationale)))
