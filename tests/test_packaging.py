import hashlib
import tempfile
import unittest
import zipfile
from io import BytesIO
from pathlib import Path
from pypdf import PdfReader

from sentinel_pi.packaging import (
    EXPERIMENT_FILES,
    ROOT,
    PackageAuditError,
    _validate_contents,
    audit_archive,
    build_public_demo_archive,
    build_submission_archive,
)


class PackagingTests(unittest.TestCase):
    def test_curated_archive_is_repeatable_manifested_and_excludes_runtime(self):
        first = build_submission_archive()
        first_hash = hashlib.sha256(first.read_bytes()).hexdigest()
        second = build_submission_archive()
        second_hash = hashlib.sha256(second.read_bytes()).hexdigest()
        self.assertEqual(first_hash, second_hash)
        audit = audit_archive(second)
        self.assertTrue(audit["manifest_verified"])
        with zipfile.ZipFile(second) as archive:
            names = archive.namelist()
        self.assertIn("README.md", names)
        self.assertIn("docs/ARCHITECTURE.md", names)
        self.assertIn("docs/MODEL_INVESTIGATOR_ASSESSMENT.md", names)
        self.assertIn("tests/test_toolgate_agent.py", names)
        self.assertIn("fixtures/dev_scenarios.jsonl", names)
        self.assertIn("evidence/evaluation-public.json", names)
        self.assertIn("evidence/candidates-public.json", names)
        self.assertIn("submission/SENTINEL_PI_Pitch_Final.pptx", names)
        self.assertIn("output/pdf/SENTINEL_PI_Pitch_Final.pdf", names)
        self.assertNotIn("submission/SENTINEL_PI_Pitch.pptx", names)
        self.assertNotIn("submission/SENTINEL_PI_Pitch_Updated.pptx", names)
        self.assertIn("public-demo/index.html", names)
        self.assertIn("public-demo/data.js", names)
        self.assertIn("public-demo/gemma3/index.html", names)
        self.assertIn("supplemental/gemma3-pilot/evidence.json", names)
        self.assertIn("supplemental/gemma3-pilot/verify_evidence.py", names)
        self.assertIn("supplemental/gemma3-pilot/GEMMA3_PILOT_REVIEW.md", names)
        self.assertEqual({name for name in names if name.startswith("experiments/model_pilot/")}, set(EXPERIMENT_FILES))
        self.assertIn("experiments/model_pilot/ollama_local.py", names)
        self.assertIn("experiments/model_pilot/pilot.py", names)
        self.assertIn("experiments/model_pilot/tests/test_pilot.py", names)
        self.assertIn("experiments/model_pilot/tests/test_budget.py", names)
        self.assertIn("experiments/model_pilot/cases.json", names)
        self.assertIn("supplemental/gemma3-pilot/evidence.json", names)
        self.assertNotIn("experiments/model_pilot/evidence/run-010.json", names)
        self.assertNotIn("experiments/model_pilot/evidence/run-008.json", names)
        self.assertNotIn("experiments/model_pilot/presentation/preview.png", names)
        self.assertNotIn("supplemental/gemma3-pilot/player/index.html", names)
        self.assertIn("MANIFEST.sha256", names)
        self.assertNotIn("PLAN.md", names)
        self.assertNotIn("STATUS.md", names)
        self.assertNotIn("DECISIONS.md", names)
        self.assertNotIn("AGENTS.md", names)
        self.assertNotIn("WORKING.md", names)
        self.assertNotIn("docs/INDEPENDENT_RELEASE_REVIEW.md", names)
        self.assertNotIn("docs/EXTERNAL_ADVERSARIAL_REVIEW.md", names)
        self.assertFalse(any(name.startswith("artifacts/") for name in names))
        self.assertFalse(any(name.startswith("experiments/model_pilot/evidence/") for name in names))
        self.assertFalse(any(name.startswith("experiments/model_pilot/presentation/") for name in names))
        self.assertFalse(any(".git" in name.split("/") for name in names))
        self.assertFalse(any("holdout" in name.casefold() or "private" in name.casefold() for name in names))
        with zipfile.ZipFile(second) as archive:
            deck = zipfile.ZipFile(BytesIO(archive.read("submission/SENTINEL_PI_Pitch_Final.pptx")))
            self.assertIn("ppt/presentation.xml", deck.namelist())
            slide_parts = [n for n in deck.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")]
            self.assertEqual(len(slide_parts), 9)
            slide_text = "".join(
                deck.read("ppt/slides/slide9.xml").decode("utf-8").split("<a:t>")[1:]
            ).casefold()
            self.assertIn("public replay is static and read-only", slide_text)
            self.assertIn("109 over", slide_text)
            self.assertIn("94 returned", slide_text)
            self.assertIn("39 errors", slide_text)
            slide4_text = "".join(
                deck.read("ppt/slides/slide4.xml").decode("utf-8").split("<a:t>")[1:]
            ).casefold()
            self.assertIn("34/34 generations returned", slide4_text)
            self.assertIn("6 cases per condition", slide4_text)
            self.assertNotIn("no public demo is deployed", slide_text)
            pdf = PdfReader(BytesIO(archive.read("output/pdf/SENTINEL_PI_Pitch_Final.pdf")), strict=True)
            self.assertEqual(len(pdf.pages), 9)

    def test_static_pages_archive_is_minimal_and_manifested(self):
        archive_path = build_public_demo_archive()
        with zipfile.ZipFile(archive_path) as archive:
            names = set(archive.namelist())
            model_page = archive.read("gemma3/index.html").decode("utf-8")
        self.assertEqual(names, {
            ".nojekyll", "README.md", "index.html", "app.js", "styles.css", "data.js",
            "gemma3/index.html", "MANIFEST.sha256"
        })
        lowered = model_page.casefold()
        self.assertIn("precomputed model recording", lowered)
        self.assertIn("recorded local ollama options", lowered)
        for option, value in (("temperature", 0), ("seed", 42), ("num_predict", 384),
                              ("num_ctx", 2048), ("num_gpu", 1), ("num_batch", 128)):
            self.assertIn(option, lowered)
            self.assertIn(f'"{option}":{value}', lowered)
        self.assertIn("connect-src 'none'", lowered)
        self.assertIn("textcontent", lowered)
        self.assertNotIn("innerhtml", lowered)
        self.assertNotIn("fetch(", lowered)
        self.assertNotIn("xmlhttprequest", lowered)
        self.assertNotIn("websocket(", lowered)

    def test_pdf_scanner_rejects_real_email_in_metadata(self):
        from pypdf import PdfWriter

        runtime = ROOT / "artifacts" / "runtime"
        runtime.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=runtime) as temp_dir:
            sample = Path(temp_dir) / "sample.pdf"
            writer = PdfWriter()
            for _ in range(9):
                writer.add_blank_page(width=960, height=540)
            writer.add_metadata({"/Title": "contact " + "person" + chr(64) + "example.com"})
            with sample.open("wb") as handle:
                writer.write(handle)
            with self.assertRaises(PackageAuditError):
                _validate_contents([("output/pdf/SENTINEL_PI_Pitch_Final.pdf", sample)])

    def test_archive_output_cannot_escape_project(self):
        with self.assertRaises(PackageAuditError):
            build_submission_archive("../outside.zip")

    def test_package_scanner_rejects_real_email_domains_and_local_paths(self):
        runtime = ROOT / "artifacts" / "runtime"
        runtime.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=runtime) as temp_dir:
            sample = Path(temp_dir) / "sample.txt"
            sample.write_text("contact " + "person" + chr(64) + "example.com", encoding="utf-8")
            with self.assertRaises(PackageAuditError):
                _validate_contents([("sample.txt", sample)])
            sample.write_text("local path: C:" + chr(92) + "Users" + chr(92) + "someone", encoding="utf-8")
            with self.assertRaises(PackageAuditError):
                _validate_contents([("sample.txt", sample)])

    def test_package_scanner_rejects_external_powerpoint_relationships(self):
        runtime = ROOT / "artifacts" / "runtime"
        runtime.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=runtime) as temp_dir:
            sample = Path(temp_dir) / "sample.pptx"
            with zipfile.ZipFile(sample, "w") as deck:
                deck.writestr("ppt/presentation.xml", "<presentation />")
                deck.writestr(
                    "ppt/slides/slide1.xml",
                    "<slide><text>Safe synthetic slide</text></slide>",
                )
                deck.writestr(
                    "ppt/_rels/presentation.xml.rels",
                    '<Relationships><Relationship TargetMode="External" Target="https://example.invalid" /></Relationships>',
                )
            with self.assertRaises(PackageAuditError):
                _validate_contents([("submission/SENTINEL_PI_Pitch_Final.pptx", sample)])


if __name__ == "__main__":
    unittest.main()
