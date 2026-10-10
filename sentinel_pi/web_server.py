"""Local-only standard-library JSON API and static UI server."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlsplit

from sentinel_pi.app_state import AppState, ROOT

WEB_ROOT = ROOT / "web"
MAX_BODY_BYTES = 65_536
OVERSIZE_DRAIN_LIMIT = MAX_BODY_BYTES + 4_096


def create_handler(state: AppState):
    class Handler(BaseHTTPRequestHandler):
        server_version = "SENTINEL-PI-local/0.1"
        _MUTATING_PATHS = {
            "/api/replay",
            "/api/evaluate",
            "/api/policy/candidate",
            "/api/policy/rollback",
        }

        def log_message(self, format: str, *args: Any) -> None:
            # Avoid logging request bodies, which may contain untrusted content.
            super().log_message(format, *args)

        def _headers(self, content_type: str, length: int) -> None:
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(length))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "same-origin")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")

        def _json(self, status: int, value: Any) -> None:
            data = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self._headers("application/json; charset=utf-8", len(data))
            self.end_headers()
            self.wfile.write(data)

        def _read_json(self) -> Any:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as exc:
                raise ValueError("Content-Length must be a valid integer.") from exc
            if length < 0:
                raise ValueError("Request body exceeds the local API limit.")
            if length > MAX_BODY_BYTES:
                if length <= OVERSIZE_DRAIN_LIMIT:
                    # Drain only a small over-limit body before returning 400. This
                    # avoids resetting a local client that is still sending it.
                    self.rfile.read(length)
                else:
                    # Never read an attacker-declared unbounded body just to reply.
                    self.close_connection = True
                raise ValueError("Request body exceeds the local API limit.")
            raw = self.rfile.read(length)
            try:
                value = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise json.JSONDecodeError("Malformed JSON body.", raw.decode("utf-8", errors="replace"), 0) from exc
            if not isinstance(value, dict):
                raise ValueError("Request body must be a JSON object.")
            return value

        def _has_same_loopback_origin(self) -> bool:
            origin = self.headers.get("Origin", "")
            host = self.headers.get("Host", "")
            if not origin or not host:
                return False
            try:
                origin_parts = urlsplit(origin)
                host_parts = urlsplit(f"//{host}")
                origin_host = origin_parts.hostname.casefold() if origin_parts.hostname else ""
                request_host = host_parts.hostname.casefold() if host_parts.hostname else ""
                origin_port = origin_parts.port or 80
                request_port = host_parts.port or 80
            except ValueError:
                return False
            allowed_hosts = {"127.0.0.1", "localhost"}
            return (
                origin_parts.scheme.casefold() == "http"
                and origin_parts.path in ("", "/")
                and not origin_parts.query
                and not origin_parts.fragment
                and origin_parts.username is None
                and origin_parts.password is None
                and host_parts.path == ""
                and host_parts.username is None
                and host_parts.password is None
                and origin_host in allowed_hosts
                and request_host == origin_host
                and origin_port == self.server.server_port
                and request_port == self.server.server_port
                and not host_parts.query
                and not host_parts.fragment
            )

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/api/health":
                self._json(200, {"status": "ok", "mode": "local_synthetic_demo"})
            elif path == "/api/state":
                self._json(200, state.snapshot())
            elif path == "/api/scenarios":
                self._json(200, {"scenarios": state.snapshot()["scenarios"]})
            elif path == "/":
                self._static("index.html", "text/html; charset=utf-8")
            elif path == "/web/app.js":
                self._static("app.js", "text/javascript; charset=utf-8")
            elif path == "/web/styles.css":
                self._static("styles.css", "text/css; charset=utf-8")
            else:
                self._json(404, {"error": "Not found."})

        def _static(self, name: str, content_type: str) -> None:
            path = (WEB_ROOT / name).resolve()
            if path.parent != WEB_ROOT.resolve() or not path.is_file():
                self._json(404, {"error": "Not found."})
                return
            data = path.read_bytes()
            self.send_response(200)
            self._headers(content_type, len(data))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            if path not in self._MUTATING_PATHS:
                self._json(404, {"error": "Not found."})
                return
            if not self._has_same_loopback_origin():
                self._json(403, {"error": "State-changing requests require the same loopback origin."})
                return
            content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().casefold()
            if content_type != "application/json":
                self._json(415, {"error": "State-changing requests require application/json."})
                return
            try:
                body = self._read_json()
                if path == "/api/replay":
                    event = state.replay(body.get("scenario_id", ""))
                    self._json(200, {"event": event, "state": state.snapshot()})
                elif path == "/api/evaluate":
                    result = state.evaluate()
                    self._json(200, {"evaluation": result, "state": state.snapshot()})
                elif path == "/api/policy/candidate":
                    result = state.propose_policy(body)
                    self._json(200, {"candidate": result, "state": state.snapshot()})
                elif path == "/api/policy/rollback":
                    self._json(200, {"rollback": state.rollback_policy(), "state": state.snapshot()})
                else:
                    self._json(404, {"error": "Not found."})
            except json.JSONDecodeError:
                self._json(400, {"error": "Malformed JSON body."})
            except ValueError as exc:
                self._json(400, {"error": str(exc)})
            except Exception as exc:
                self._json(500, {"error": f"Local operation failed ({type(exc).__name__})."})

        def do_HEAD(self) -> None:
            self.send_response(405)
            self._headers("application/json; charset=utf-8", 0)
            self.end_headers()

    return Handler


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    if host != "127.0.0.1" and host != "localhost":
        raise ValueError("The demo server may bind only to loopback.")
    server = ThreadingHTTPServer((host, port), create_handler(AppState()))
    server.daemon_threads = True
    print(f"SENTINEL PI local console: http://127.0.0.1:{server.server_port}")
    print("Synthetic records only. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping local server.")
    finally:
        server.server_close()
