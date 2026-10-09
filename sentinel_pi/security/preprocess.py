"""Bounded, non-executing normalization and provenance preservation."""

from __future__ import annotations

import base64
import hashlib
import re
import unicodedata
from dataclasses import dataclass

from sentinel_pi.models import ContentEnvelope, Provenance

BASE64_TOKEN = re.compile(r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{20,8192}={0,2}(?![A-Za-z0-9+/])")
INVISIBLE = {0x00AD, 0x034F, 0x061C, 0x180E, 0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF}


@dataclass(frozen=True)
class DecodedPayload:
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class PreparedContent:
    envelope: ContentEnvelope
    normalized_text: str
    normalized_to_original: tuple[int, ...]
    decoded_payloads: tuple[DecodedPayload, ...]
    provenance: Provenance

    def original_span(self, start: int, end: int) -> tuple[int, int]:
        if start < 0 or end <= start or end > len(self.normalized_to_original):
            raise ValueError("normalized span is out of bounds")
        return self.normalized_to_original[start], self.normalized_to_original[end - 1] + 1


class Preprocessor:
    MAX_DECODED_BYTES = 4096
    MAX_CANDIDATES = 32

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

        decoded: list[DecodedPayload] = []
        for match in list(BASE64_TOKEN.finditer(envelope.content))[: self.MAX_CANDIDATES]:
            token = match.group(0)
            if len(token) > ((self.MAX_DECODED_BYTES + 2) // 3) * 4 + 4:
                continue
            try:
                raw = base64.b64decode(token, validate=True)
                if not raw or len(raw) > self.MAX_DECODED_BYTES:
                    continue
                text = raw.decode("utf-8", errors="strict")
            except (ValueError, UnicodeDecodeError):
                continue
            if not text or not any(ch.isalpha() for ch in text):
                continue
            printable_ratio = sum(ch.isprintable() or ch in "\r\n\t" for ch in text) / len(text)
            if printable_ratio >= 0.92:
                decoded.append(DecodedPayload(match.start(), match.end(), text))

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
            normalized_text="".join(normalized),
            normalized_to_original=tuple(mapping),
            decoded_payloads=tuple(decoded),
            provenance=provenance,
        )
