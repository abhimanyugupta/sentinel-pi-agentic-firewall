import json
import unittest
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


if __name__ == "__main__":
    unittest.main()
