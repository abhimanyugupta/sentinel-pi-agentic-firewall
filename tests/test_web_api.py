import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from sentinel_pi.app_state import AppState
from sentinel_pi.web_server import create_handler, serve


class WebApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(AppState()))
        cls.server.daemon_threads = True
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = "http://127.0.0.1:" + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def get_json(self, path):
        with urlopen(self.base + path, timeout=3) as response:
            return response.status, response.headers, json.loads(response.read().decode())

    def post_json(self, path, body):
        request = Request(
            self.base + path,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "Origin": self.base},
            method="POST",
        )
        with urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode())

    def assert_post_rejected(self, path, body, headers, expected_status):
        request = Request(
            self.base + path,
            data=body,
            headers=headers,
            method="POST",
        )
        with self.assertRaises(HTTPError) as caught:
            urlopen(request, timeout=3)
        self.assertEqual(caught.exception.code, expected_status)

    def test_health_and_static_dashboard(self):
        status, headers, payload = self.get_json("/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        with urlopen(self.base + "/", timeout=3) as response:
            page = response.read().decode()
        self.assertIn("SENTINEL PI", page)
        self.assertIn("Agent action trace", page)

    def test_state_contains_reproducible_evidence(self):
        _, _, payload = self.get_json("/api/state")
        self.assertGreaterEqual(len(payload["events"]), 3)
        self.assertEqual(payload["metrics"]["protected_unauthorized_mock_emails_executed"], 0)
        self.assertEqual(payload["metrics"]["protected_tool_gate_violations"], 0)

    def test_replay_and_candidate_endpoints(self):
        _, replay = self.post_json("/api/replay", {"scenario_id": "legitimate_support"})
        self.assertTrue(replay["event"]["protected"]["legitimate_ticket_created"])
        _, candidate = self.post_json(
            "/api/policy/candidate",
            {"name": "Escalate context poisoning", "add_block_categories": ["context_poisoning"]},
        )
        self.assertIn("accepted", candidate["candidate"])
        self.assertGreaterEqual(len(candidate["state"]["policy"]["versions"]), 1)

    def test_mutating_api_rejects_foreign_origin(self):
        self.assert_post_rejected(
            "/api/policy/candidate",
            json.dumps({"name": "External candidate", "add_block_categories": ["context_poisoning"]}).encode(),
            {"Content-Type": "application/json", "Origin": "https://attacker.example"},
            403,
        )

    def test_mutating_api_rejects_foreign_host(self):
        self.assert_post_rejected(
            "/api/replay",
            json.dumps({"scenario_id": "legitimate_support"}).encode(),
            {"Content-Type": "application/json", "Origin": self.base, "Host": "attacker.example"},
            403,
        )

    def test_mutating_api_rejects_host_with_uri_suffix(self):
        host = self.base.split("://", 1)[1] + "?attacker.example"
        self.assert_post_rejected(
            "/api/replay",
            json.dumps({"scenario_id": "legitimate_support"}).encode(),
            {"Content-Type": "application/json", "Origin": self.base, "Host": host},
            403,
        )

    def test_mutating_api_requires_json_content_type(self):
        self.assert_post_rejected(
            "/api/replay",
            json.dumps({"scenario_id": "legitimate_support"}).encode(),
            {"Content-Type": "text/plain", "Origin": self.base},
            415,
        )

    def test_mutating_api_rejects_missing_origin(self):
        self.assert_post_rejected(
            "/api/replay",
            json.dumps({"scenario_id": "legitimate_support"}).encode(),
            {"Content-Type": "application/json"},
            403,
        )

    def test_unsafe_baseline_cannot_be_selected_by_request_body(self):
        _, replay = self.post_json(
            "/api/replay", {"scenario_id": "indirect_injection", "unsafe_baseline": True}
        )
        protected = replay["event"]["protected"]
        self.assertFalse(protected["unauthorized_email_executed"])
        self.assertFalse(any(call["tool"] == "send_email" for call in protected["proposed_calls"]))

    def test_unknown_scenario_is_a_controlled_client_error(self):
        request = Request(
            self.base + "/api/replay",
            data=json.dumps({"scenario_id": "../outside"}).encode(),
            headers={"Content-Type": "application/json", "Origin": self.base},
            method="POST",
        )
        with self.assertRaises(HTTPError) as caught:
            urlopen(request, timeout=3)
        self.assertEqual(caught.exception.code, 400)

    def test_malformed_utf8_and_json_are_controlled_client_errors(self):
        for body in (b"\xff", b"{broken"):
            request = Request(
                self.base + "/api/replay",
                data=body,
                headers={"Content-Type": "application/json", "Origin": self.base},
                method="POST",
            )
            with self.assertRaises(HTTPError) as caught:
                urlopen(request, timeout=3)
            self.assertEqual(caught.exception.code, 400)

    def test_api_rejects_oversized_request_bodies(self):
        request = Request(
            self.base + "/api/replay",
            data=b" " * 65_537,
            headers={"Content-Type": "application/json", "Origin": self.base},
            method="POST",
        )
        with self.assertRaises(HTTPError) as caught:
            urlopen(request, timeout=3)
        self.assertEqual(caught.exception.code, 400)

    def test_server_refuses_non_loopback_bind(self):
        with self.assertRaises(ValueError):
            serve(host="0.0.0.0", port=8765)


if __name__ == "__main__":
    unittest.main()
