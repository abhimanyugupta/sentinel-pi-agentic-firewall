"""Curated, auditable source archive builder for local submission review."""

from __future__ import annotations

import hashlib
import io
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from pathlib import PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
ROOT_FILES = (
    ".gitignore",
    "README.md",
    "SPEC.md",
    "requirements-release.txt",
    "output/pdf/SENTINEL_PI_Pitch.pdf",
)
TREE_DIRS = ("sentinel_pi", "tests", "fixtures", "web", "docs", "evidence", "public-demo")
TREE_DIRS = TREE_DIRS + ("submission",)
PRIVATE_REVIEW_REPORTS = {"docs/INDEPENDENT_RELEASE_REVIEW.md"}
PPTX_PATHS = {"submission/SENTINEL_PI_Pitch.pptx"}
PDF_PATHS = {"output/pdf/SENTINEL_PI_Pitch.pdf"}
PUBLIC_DEMO_FILES = (
    ".nojekyll",
    "README.md",
    "index.html",
    "app.js",
    "styles.css",
    "data.js",
)
FORBIDDEN_PATH_PARTS = {".git", ".env", "private", "holdout", "blind", "runtime", "credentials", "secrets", "__pycache__"}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"(?i)(?:api[_-]?key|password|access[_-]?token)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{20,}"),
)
LOCAL_PATH_PATTERN = re.compile(r"(?i)(?:[A-Z]:\\(?:Users|Documents and Settings)\\[^\\\s]+|/(?:Users|home)/[^/\s]+)")
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)


class PackageAuditError(ValueError):
    """Raised when a curated archive violates its inclusion or content rules."""


def _check_text(relative: str, text: str) -> None:
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            raise PackageAuditError(f"Secret-like content was found in {relative}.")
    if LOCAL_PATH_PATTERN.search(text):
        raise PackageAuditError(f"A local machine path was found in {relative}.")
    for match in EMAIL_PATTERN.finditer(text):
        domain = match.group(0).rsplit("@", 1)[1].casefold()
        if not domain.endswith(".invalid"):
            raise PackageAuditError(f"A non-synthetic email address was found in {relative}.")


def _check_pptx(relative: str, data: bytes) -> None:
    """Inspect the one allowed deck without accepting embedded media or links."""
    if relative not in PPTX_PATHS:
        raise PackageAuditError(f"PowerPoint is not on the export allowlist: {relative}")
    try:
        with zipfile.ZipFile(io.BytesIO(data), "r") as presentation:
            names = presentation.namelist()
            if len(names) != len(set(names)):
                raise PackageAuditError(f"PowerPoint contains duplicate parts: {relative}")
            if "ppt/presentation.xml" not in names:
                raise PackageAuditError(f"PowerPoint is missing its presentation part: {relative}")
            slides = []
            for name in names:
                part = PurePosixPath(name)
                if (
                    not part.parts
                    or part.is_absolute()
                    or "\\" in name
                    or ":" in part.parts[0]
                    or ".." in part.parts
                ):
                    raise PackageAuditError(f"PowerPoint contains an unsafe part path: {relative}")
                if name != "_rels/.rels" and Path(name).suffix.casefold() not in {".xml", ".rels"}:
                    raise PackageAuditError(f"PowerPoint contains a non-text embedded part: {relative}")
                try:
                    xml_text = presentation.read(name).decode("utf-8")
                    root = ET.fromstring(xml_text)
                except (UnicodeDecodeError, ET.ParseError) as exc:
                    raise PackageAuditError(f"PowerPoint contains an invalid XML part: {relative}") from exc
                _check_text(relative, xml_text)
                for element in root.iter():
                    for value in element.attrib.values():
                        _check_text(relative, value)
                    if element.text:
                        _check_text(relative, element.text)
                    if element.attrib.get("TargetMode", "").casefold() == "external":
                        raise PackageAuditError(f"PowerPoint contains an external relationship: {relative}")
                if re.fullmatch(r"ppt/slides/slide[1-9][0-9]*\.xml", name):
                    slides.append(name)
            if not slides:
                raise PackageAuditError(f"PowerPoint contains no slides: {relative}")
    except zipfile.BadZipFile as exc:
        raise PackageAuditError(f"PowerPoint is not a valid ZIP package: {relative}") from exc


def _check_pdf(relative: str, data: bytes) -> None:
    """Validate the one exported deck PDF and scan its readable content."""
    if relative not in PDF_PATHS:
        raise PackageAuditError(f"PDF is not on the export allowlist: {relative}")
    if not data.startswith(b"%PDF-") or b"%%EOF" not in data[-2048:]:
        raise PackageAuditError(f"Pitch PDF is malformed: {relative}")
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data), strict=True)
        if reader.is_encrypted or len(reader.pages) != 9:
            raise PackageAuditError(f"Pitch PDF must be an unencrypted nine-page deck: {relative}")
        page_text = []
        root = reader.trailer["/Root"].get_object()
        if any(key in root for key in ("/OpenAction", "/AA", "/AcroForm")):
            raise PackageAuditError(f"Pitch PDF contains active document actions or forms: {relative}")
        names = root.get("/Names")
        if names:
            names = names.get_object()
            if "/EmbeddedFiles" in names or "/JavaScript" in names:
                raise PackageAuditError(f"Pitch PDF contains embedded files or JavaScript: {relative}")
        for page in reader.pages:
            if page.get("/Annots"):
                raise PackageAuditError(f"Pitch PDF contains annotations or external links: {relative}")
            page_text.append(page.extract_text() or "")
        metadata = reader.metadata
        metadata_text = "\n".join(
            f"{key} {value}" for key, value in (metadata or {}).items() if value is not None
        )
        _check_text(relative, "\n".join(page_text) + "\n" + metadata_text)
    except PackageAuditError:
        raise
    except ImportError as exc:
        raise PackageAuditError("Rebuilding the public archive with the pitch PDF requires pypdf for content and active-link checks.") from exc
    except Exception as exc:
        raise PackageAuditError(f"Pitch PDF could not be safely parsed: {relative}") from exc


def _validate_public_demo_files() -> dict[str, bytes]:
    payloads: dict[str, bytes] = {}
    for name in PUBLIC_DEMO_FILES:
        path = ROOT / "public-demo" / name
        if not path.is_file():
            raise PackageAuditError(f"Static demo bundle is missing {name}.")
        relative = _safe_relative(path)
        data = path.read_bytes()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PackageAuditError(f"Static demo file is not UTF-8: {relative}") from exc
        _check_text(relative, text)
        payloads[name] = data
    if b"schema_version" not in payloads["data.js"] or b"live_model_used" not in payloads["data.js"]:
        raise PackageAuditError("Static demo data is missing its version or simulator disclosure.")
    if b"window.SENTINEL_PI_DEMO_DATA = null" in payloads["data.js"]:
        raise PackageAuditError("Static demo data has not been generated from recorded traces.")
    return payloads


def audit_public_demo_archive(path: str | Path) -> dict[str, object]:
    """Verify the static-only Pages bundle and its content manifest."""
    archive_path = Path(path).resolve()
    try:
        archive_path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise PackageAuditError("Static demo archive output must stay inside the project directory.") from exc
    with zipfile.ZipFile(archive_path, "r") as archive:
        names = archive.namelist()
        expected_names = set(PUBLIC_DEMO_FILES) | {"MANIFEST.sha256"}
        if set(names) != expected_names or len(names) != len(expected_names):
            raise PackageAuditError("Static demo archive contains missing or unexpected files.")
        payloads = {name: archive.read(name) for name in PUBLIC_DEMO_FILES}
        manifest = archive.read("MANIFEST.sha256").decode("utf-8")
        expected = "".join(
            f"{hashlib.sha256(data).hexdigest()}  {name}\n"
            for name, data in sorted(payloads.items())
        )
        if manifest != expected:
            raise PackageAuditError("Static demo archive manifest does not match its members.")
        for name, data in payloads.items():
            _check_text(f"public-demo/{name}", data.decode("utf-8"))
        if b"window.SENTINEL_PI_DEMO_DATA = null" in payloads["data.js"]:
            raise PackageAuditError("Static demo archive contains an empty trace snapshot.")
    return {
        "files": len(payloads),
        "manifest_verified": True,
        "external_runtime_dependencies": 0,
        "archive_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
    }


def build_public_demo_archive(output: str | Path = "artifacts/public-demo.zip") -> Path:
    """Build a standalone Pages bundle containing only static demo assets."""
    output_path = Path(output)
    resolved_output = output_path.resolve() if output_path.is_absolute() else (ROOT / output_path).resolve()
    try:
        resolved_output.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise PackageAuditError("Static demo archive output must stay inside the project directory.") from exc
    payloads = _validate_public_demo_files()
    manifest = "".join(
        f"{hashlib.sha256(data).hexdigest()}  {name}\n"
        for name, data in sorted(payloads.items())
    ).encode("utf-8")
    payloads["MANIFEST.sha256"] = manifest
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(resolved_output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(payloads.items()):
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    audit_public_demo_archive(resolved_output)
    return resolved_output


def _safe_relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise PackageAuditError("A package input resolves outside the project directory.") from exc
    return relative.as_posix()


def _collect_files() -> list[tuple[str, Path]]:
    candidates = [ROOT / name for name in ROOT_FILES]
    for directory in TREE_DIRS:
        root = ROOT / directory
        if root.exists():
            candidates.extend(path for path in root.rglob("*") if path.is_file())
    files: dict[str, Path] = {}
    for path in candidates:
        if not path.is_file():
            continue
        relative = _safe_relative(path)
        # Keep the private release-gate report out of the public source export.
        # It records the export checksum, so including it would make that checksum self-referential.
        if relative in PRIVATE_REVIEW_REPORTS:
            continue
        parts = {part.casefold() for part in Path(relative).parts}
        if parts.intersection(FORBIDDEN_PATH_PARTS):
            continue
        if relative.startswith("submission/") and relative not in PPTX_PATHS:
            raise PackageAuditError(f"Submission directory contains a file outside its allowlist: {relative}")
        if path.suffix.casefold() in {".pem", ".key", ".p12", ".pfx", ".sqlite", ".sqlite3", ".db"}:
            continue
        files[relative] = path
    if not files:
        raise PackageAuditError("No eligible files were found for the curated archive.")
    return sorted(files.items())


def _validate_contents(files: list[tuple[str, Path]]) -> dict[str, bytes]:
    payloads: dict[str, bytes] = {}
    for relative, path in files:
        data = path.read_bytes()
        if relative in PPTX_PATHS:
            _check_pptx(relative, data)
            payloads[relative] = data
            continue
        if relative in PDF_PATHS:
            _check_pdf(relative, data)
            payloads[relative] = data
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PackageAuditError(f"Non-UTF-8 file is not permitted in the source package: {relative}") from exc
        _check_text(relative, text)
        payloads[relative] = data
    return payloads


def audit_archive(path: str | Path) -> dict[str, object]:
    """Read back an archive and check its paths, manifest, and secret patterns."""
    archive_path = Path(path).resolve()
    try:
        archive_path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise PackageAuditError("Archive output must stay inside the project directory.") from exc
    with zipfile.ZipFile(archive_path, "r") as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise PackageAuditError("Archive contains duplicate paths.")
        if "MANIFEST.sha256" not in names:
            raise PackageAuditError("Archive is missing its SHA-256 manifest.")
        payloads: dict[str, bytes] = {}
        for name in names:
            zip_path = PurePosixPath(name)
            path_parts = {part.casefold() for part in zip_path.parts}
            if not zip_path.parts or zip_path.is_absolute() or "\\" in name or ":" in zip_path.parts[0] or ".." in zip_path.parts:
                raise PackageAuditError("Archive contains an unsafe path.")
            if path_parts.intersection(FORBIDDEN_PATH_PARTS):
                raise PackageAuditError("Archive contains a forbidden private or runtime path.")
            if Path(name).suffix.casefold() in {".pem", ".key", ".p12", ".pfx", ".sqlite", ".sqlite3", ".db"}:
                raise PackageAuditError("Archive contains a forbidden credential or runtime file type.")
            payloads[name] = archive.read(name)
        manifest = payloads.pop("MANIFEST.sha256").decode("utf-8")
        expected = "".join(f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in sorted(payloads.items()))
        if manifest != expected:
            raise PackageAuditError("Archive manifest does not match the included files.")
        for name, data in payloads.items():
            if Path(name).suffix.casefold() == ".pptx":
                _check_pptx(name, data)
                continue
            if Path(name).suffix.casefold() == ".pdf":
                _check_pdf(name, data)
                continue
            try:
                content = data.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise PackageAuditError(f"Archive contains a non-UTF-8 file: {name}") from exc
            _check_text(name, content)
    return {
        "files": len(payloads),
        "manifest_verified": True,
        "secret_patterns_found": 0,
        "private_holdout_paths_found": 0,
        "archive_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
    }


def build_submission_archive(output: str | Path = "artifacts/submission.zip") -> Path:
    """Build a deterministic ZIP from an explicit source/docs/tests/artifacts allowlist."""
    output_path = Path(output)
    resolved_output = output_path.resolve() if output_path.is_absolute() else (ROOT / output_path).resolve()
    try:
        resolved_output.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise PackageAuditError("Archive output must stay inside the project directory.") from exc

    payloads = _validate_contents(_collect_files())
    manifest = "".join(f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in sorted(payloads.items())).encode("utf-8")
    payloads["MANIFEST.sha256"] = manifest
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(resolved_output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(payloads.items()):
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    audit_archive(resolved_output)
    return resolved_output
