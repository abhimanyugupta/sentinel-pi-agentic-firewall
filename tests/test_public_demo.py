import json
import subprocess
import sys
import unittest
import uuid
from pathlib import Path

from sentinel_pi.evaluation import ROOT
from sentinel_pi.public_demo import build_public_demo_snapshot, write_public_demo_data


class PublicDemoTests(unittest.TestCase):
    def test_snapshot_contains_precomputed_traces_and_current_public_evidence(self):
        first = build_public_demo_snapshot()
        second = build_public_demo_snapshot()
        self.assertEqual(first, second)
        self.assertFalse(first["simulator"]["live_model_used"])
        self.assertEqual(first["evaluation"]["metrics"]["total_cases"], 30)
        self.assertEqual(first["evaluation"]["metrics"]["attack_cases"], 18)
        self.assertEqual(first["evaluation"]["metrics"]["benign_cases"], 12)
        self.assertEqual(first["evaluation"]["metrics"]["independent_gate_external_provenance_cases"], 1)
        self.assertEqual(len(first["evaluation"]["configured_attack_types"]), 9)
        candidate = first["candidates"]["severity_hardening_candidate"]
        self.assertEqual(candidate["candidate_classification"], "policy_hardening_only")
        self.assertFalse(candidate["security_improvement_demonstrated"])
        self.assertEqual(candidate["policy_comparison"]["newly_contained_cases"], [])
        self.assertEqual(candidate["end_to_end"]["baseline"]["protected_unauthorized_side_effects"], 0)
        self.assertEqual(candidate["end_to_end"]["candidate"]["protected_unauthorized_side_effects"], 0)
        self.assertEqual(len(first["traces"]), 4)
        for trace in first["traces"]:
            self.assertFalse(trace["agent_simulation"]["live_model_used"])
        by_id = {trace["scenario_id"]: trace for trace in first["traces"]}
        attack = by_id["indirect_injection"]
        self.assertTrue(attack["baseline"]["unauthorized_email_executed"])
        self.assertFalse(attack["protected"]["unauthorized_email_executed"])
        self.assertTrue(attack["protected"]["external_instruction_suppressed_by_firewall"])
        contamination = by_id["answer_contamination"]
        self.assertTrue(contamination["baseline"]["answer_leaked_canary"])
        self.assertNotIn("SYN-CANARY", contamination["protected"]["answer"])
        self.assertIn("[REDACTED SYNTHETIC SECRET]", contamination["protected"]["answer"])

    def test_generated_page_uses_no_network_or_write_api_and_renders_text_safely(self):
        data_path = write_public_demo_data()
        serialized = data_path.read_text(encoding="utf-8").split("window.SENTINEL_PI_DEMO_DATA = ", 1)[1].rsplit(";", 1)[0]
        snapshot = json.loads(serialized)
        self.assertEqual(snapshot, build_public_demo_snapshot())
        site = ROOT / "public-demo"
        html = (site / "index.html").read_text(encoding="utf-8")
        js = (site / "app.js").read_text(encoding="utf-8")
        css = (site / "styles.css").read_text(encoding="utf-8")
        for forbidden in ("fetch(", "XMLHttpRequest", "WebSocket", "EventSource", "sendBeacon", "innerHTML", "insertAdjacentHTML", "document.write("):
            self.assertNotIn(forbidden, js)
        self.assertNotIn("<form", html.casefold())
        self.assertNotIn("https://", html + js + css)
        self.assertIn("textContent", js)
        self.assertIn("PRECOMPUTED SYNTHETIC TRACES", html)
        self.assertIn("configured_attack_types", js)
        self.assertNotIn('"9 / 9"', js)
        self.assertIn("policy_hardening_only", js)
        self.assertIn("connect-src 'none'", html)
        self.assertIn("object-src 'none'", html)

    def test_indirect_injection_is_default_and_authorized_task_is_prominent(self):
        snapshot = build_public_demo_snapshot()
        self.assertEqual(snapshot["traces"][0]["scenario_id"], "indirect_injection")
        self.assertTrue(snapshot["traces"][0]["intent"]["task"].strip())
        html = (ROOT / "public-demo" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "public-demo" / "app.js").read_text(encoding="utf-8")
        self.assertIn('id="authorized-task"', html)
        self.assertIn("trace.intent.task", js)
        self.assertEqual(len(snapshot["traces"]), 4)


    def test_incident_first_experience_keeps_recorded_and_synthetic_evidence_separate(self):
        site = ROOT / "public-demo"
        html = (site / "index.html").read_text(encoding="utf-8")
        js = (site / "app.js").read_text(encoding="utf-8")
        css = (site / "styles.css").read_text(encoding="utf-8")
        self.assertIn('id="incident"', html)
        self.assertIn('id="decision-passport"', html)
        self.assertIn('href="./gemma3/index.html"', html)
        self.assertIn("ACTUAL GEMMA PROPOSAL", html)
        self.assertIn("Refund approved by administrator", html)
        self.assertIn("Same gate in both conditions", html)
        self.assertIn("not a blind benchmark", html)
        self.assertIn("The replay lab below is deterministic", html)
        self.assertIn("renderDecisionPassport(trace)", js)
        self.assertIn('textContent = entry.detail', js)
        self.assertNotIn("innerHTML", js)
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn("passport-grid", css)
        self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr));", css)
        self.assertIn(".comparison-grid > .run-panel { min-width: 0; }", css)
        self.assertIn(".trace-block pre { max-width: 100%; white-space: pre-wrap; overflow-wrap: anywhere; }", css)
        self.assertIn("@media (max-width: 860px)", css)
        self.assertIn(".comparison-grid { grid-template-columns: 1fr; }", css)
        self.assertIn(".panel-title-row { align-items: flex-start; flex-wrap: wrap; }", css)
        self.assertNotIn("live-dot", html + css)
        data = (site / "data.js").read_text(encoding="utf-8")
        self.assertIn('window.SENTINEL_PI_DEMO_DATA = {', data)
        snapshot = json.loads(data[data.index("= ") + 2:].strip().removesuffix(";"))
        self.assertEqual(snapshot["traces"][0]["scenario_id"], "indirect_injection")
        self.assertNotIn("https://", html + js + css)

    def test_recorded_player_wraps_long_identity_and_case_cards(self):
        css = (ROOT / "supplemental/gemma3-pilot/styles.css").read_text(encoding="utf-8")
        self.assertIn("#model-identity,#source-hash{overflow-wrap:anywhere}", css)
        self.assertIn(".condition{min-width:0;", css)

    def test_recorded_player_presents_synchronized_four_stage_boundary_xray(self):
        template = (ROOT / "supplemental/gemma3-pilot/index.template.html").read_text(encoding="utf-8")
        app = (ROOT / "supplemental/gemma3-pilot/app.js").read_text(encoding="utf-8")
        css = (ROOT / "supplemental/gemma3-pilot/styles.css").read_text(encoding="utf-8")
        self.assertIn('id="xray-source"', template)
        self.assertIn('id="xray-stages"', template)
        self.assertIn('aria-live="polite"', template)
        for stage in ("Untrusted input", "Actual Gemma-generated proposal", "Host authorization", "Legitimate task + effects"):
            self.assertIn(stage, app)
        self.assertIn("attack_target_proposed", app)
        self.assertIn("SAME HOST INTENT GATE", app)
        self.assertIn('textContent = `Lower-trust document', app)
        self.assertNotIn("innerHTML", app)
        self.assertIn("grid-template-columns:repeat(4,minmax(0,1fr))", css)
        self.assertIn("@media(max-width:980px)", css)
        self.assertIn("@media(max-width:560px)", css)

    def test_recorded_player_builder_rejects_output_outside_project(self):
        script = ROOT / "supplemental/gemma3-pilot/build_player.py"
        output = ROOT.parent / f"sentinel-pi-output-guard-{uuid.uuid4().hex}.html"
        self.assertFalse(output.exists())
        result = subprocess.run(
            [sys.executable, str(script), "--output", str(output)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("player_output_must_remain_in_project", result.stderr)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
