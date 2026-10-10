"""Bounded, non-executing normalization and provenance preservation."""

from __future__ import annotations

import base64
import hashlib
import re
import unicodedata
from dataclasses import dataclass

from sentinel_pi.models import ContentEnvelope, Provenance

BASE64_TOKEN = re.compile(r"(?<![A-Za-z0-9+/_-])[A-Za-z0-9+/_-]{20,}={0,2}(?![A-Za-z0-9+/_-])")
INVISIBLE = {0x00AD, 0x034F, 0x061C, 0x180E, 0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF}


@dataclass(frozen=True)
class DecodedPayload:
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class EncodedInspection:
    complete: bool
    reasons: tuple[str, ...]
    candidates_inspected: int


@dataclass(frozen=True)
class PreparedContent:
    envelope: ContentEnvelope
    normalized_text: str
    normalized_to_original: tuple[int, ...]
    decoded_payloads: tuple[DecodedPayload, ...]
    encoded_inspection: EncodedInspection
    provenance: Provenance

    def original_span(self, start: int, end: int) -> tuple[int, int]:
        if start < 0 or end <= start or end > len(self.normalized_to_original):
            raise ValueError("normalized span is out of bounds")
        return self.normalized_to_original[start], self.normalized_to_original[end - 1] + 1


class Preprocessor:
    MAX_DECODED_BYTES = 4096
    MAX_CANDIDATES = 32
    MAX_ENCODED_TOKEN_CHARS = 8192

    def prepare(self, envelope: ContentEnvelope) -> PreparedContent:
        envelope.validate()
        normalized: list[str] = []
        mapping: list[int] = []
        changed = False
        removed = False
        for index, char in enumerate(envelope.content):
            if ord(char) in INVISIBLE or unicodedata.category(char) == "Cf":
                removed = True
                continue
            folded = unicodedata.normalize("NFKC", char)
            if folded != char:
                changed = True
            for item in folded:
                normalized.append(item)
                mapping.append(index)

        normalized_text = "".join(normalized)
        decoded: list[DecodedPayload] = []
        inspection_reasons: list[str] = []
        candidates_inspected = 0
        for match in BASE64_TOKEN.finditer(normalized_text):
            if candidates_inspected >= self.MAX_CANDIDATES:
                inspection_reasons.append("candidate_count_limit_exceeded")
                break
            candidates_inspected += 1
            token = match.group(0)
            if len(token) > self.MAX_ENCODED_TOKEN_CHARS:
                inspection_reasons.append("encoded_token_length_limit_exceeded")
                break
            try:
                padded_token = token + ("=" * (-len(token) % 4))
                raw = base64.b64decode(padded_token, altchars=b"-_", validate=True)
                if not raw:
                    continue
                if len(raw) > self.MAX_DECODED_BYTES:
                    inspection_reasons.append("decoded_byte_budget_exceeded")
                    continue
                text = raw.decode("utf-8", errors="strict")
            except (ValueError, UnicodeDecodeError):
                continue
            if not text or not any(ch.isalpha() for ch in text):
                continue
            printable_ratio = sum(ch.isprintable() or ch in "\r\n\t" for ch in text) / len(text)
            if printable_ratio >= 0.92:
                decoded.append(
                    DecodedPayload(
                        mapping[match.start()],
                        mapping[match.end() - 1] + 1,
                        text,
                    )
                )

        transforms: list[str] = []
        if changed:
            transforms.append("unicode_nfkc")
        if removed:
            transforms.append("removed_invisible_format_controls")
        if decoded:
            transforms.append("bounded_base64_text_decode")
        provenance = Provenance(
            source_type=envelope.source_type,
            source_id=envelope.source_id,
            trusted=envelope.trusted,
            content_sha256=hashlib.sha256(envelope.content.encode("utf-8")).hexdigest(),
            decoded_payloads=len(decoded),
            transforms=tuple(transforms),
        )
        return PreparedContent(
            envelope=envelope,
            normalized_text=normalized_text,
            normalized_to_original=tuple(mapping),
            decoded_payloads=tuple(decoded),
            encoded_inspection=EncodedInspection(
                complete=not inspection_reasons,
                reasons=tuple(dict.fromkeys(inspection_reasons)),
                candidates_inspected=candidates_inspected,
            ),
            provenance=provenance,
        )
