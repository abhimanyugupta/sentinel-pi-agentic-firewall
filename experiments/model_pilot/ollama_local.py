"""Approved local-only adapter. Never reads credentials or pulls a model."""
from __future__ import annotations

import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from .budget import BudgetExhausted, BudgetGuard
from .pilot import AdapterFailure, Limits, RESPONSE_SCHEMA, canonical, sha

MODEL = "gemma3:latest"
DIGEST = "1fb5619173ca792f99aa52ae58424bf66f895114a5d80567b99d19ede9e52390"
VERSION = "0.40.2"
BASE = "http://127.0.0.1:11434"
HOST_OPTIONS = {"num_ctx": 2048, "num_gpu": 1, "num_batch": 128}


def wire_json(value):
    # JSON schema property order affects constrained-decoder token order.
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':'))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise AdapterFailure("redirect_rejected")


class LocalOllama:
    def __init__(self, *, human_approved: bool = False, budget_guard: BudgetGuard | None = None):
        if human_approved is not True:
            raise AdapterFailure("human_approval_required")
        self.budget_guard = budget_guard or BudgetGuard()
        self.identity = {"provider": "ollama_local", "model": MODEL, "model_digest": DIGEST,
            "runtime_version": VERSION, "live_model": True, "provider_spending_ceiling_usd": 0,
            "human_approved": True, "transport": "fixed_loopback_no_proxy_no_redirect",
            "generation": "constrained JSON tool proposals; not native tool execution",
            "cumulative_budget_guard": "persistent; generation and warm-up limits are separate"}
        self._opener = build_opener(ProxyHandler({}), NoRedirect())

    def _json(self, path: str, timeout: float, data=None):
        if path not in ("/api/tags", "/api/version", "/api/chat", "/api/ps"):
            raise AdapterFailure("endpoint_rejected")
        req = Request(BASE + path, data=wire_json(data).encode() if data is not None else None,
                      headers={"Content-Type": "application/json"})
        try:
            with self._opener.open(req, timeout=max(0.01, timeout)) as response:
                raw = response.read(262_145)
                if len(raw) > 262_144:
                    raise AdapterFailure("provider_response_size")
            value = json.loads(raw)
            if not isinstance(value, dict) or "error" in value:
                raise AdapterFailure("provider_response_schema")
            return value
        except AdapterFailure:
            raise
        except (HTTPError, URLError, TimeoutError, OSError, ValueError):
            # Never propagate remote bodies, environment values, or local paths.
            raise AdapterFailure("local_provider_request_failed") from None

    def _identity_check(self, timeout: float) -> None:
        tags = self._json("/api/tags", timeout)
        matches = [m for m in tags.get("models", []) if isinstance(m, dict) and m.get("name") == MODEL]
        if len(matches) != 1 or matches[0].get("digest") != DIGEST:
            raise AdapterFailure("pinned_model_digest_changed")
        if self._json("/api/version", timeout).get("version") != VERSION:
            raise AdapterFailure("pinned_runtime_version_changed")

    def generate(self, messages: list[dict[str, str]], limits: Limits) -> dict:
        limits.validate()
        if len(canonical(messages).encode()) > 32_768:
            raise AdapterFailure("input_size")
        deadline = time.monotonic() + limits.timeout_seconds
        remaining = lambda: max(0.01, deadline - time.monotonic())
        self._identity_check(remaining())
        options = {"temperature": 0, "seed": limits.seed, "num_predict": limits.max_output_tokens,
                   **HOST_OPTIONS}
        request = {"model": MODEL, "messages": messages, "stream": False,
                   "format": RESPONSE_SCHEMA, "keep_alive": "5m", "options": options}
        try:
            self.budget_guard.reserve("generation")
        except BudgetExhausted:
            raise AdapterFailure("cumulative_budget_exhausted") from None
        value = self._json("/api/chat", remaining(), request)
        self._identity_check(remaining())
        if (time.monotonic() > deadline or value.get("model") != MODEL or value.get("done") is not True
                or value.get("done_reason") != "stop"):
            raise AdapterFailure("incomplete_or_mismatched_generation")
        message = value.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise AdapterFailure("missing_model_text")
        return {"text": message["content"], "metadata": {
            "model": value["model"], "model_digest": DIGEST, "runtime_version": VERSION,
            "http_request_sha256": sha(wire_json(request)),
            "ordered_response_schema_sha256": sha(wire_json(RESPONSE_SCHEMA)),
            "options": options, **{key: value.get(key) for key in (
                "created_at", "done_reason", "prompt_eval_count", "eval_count", "total_duration", "load_duration")}}}

    def loaded_model_info(self) -> dict:
        models = self._json("/api/ps", 5).get("models", [])
        return {"loaded_models": [{key: model.get(key) for key in ("name", "digest", "size", "size_vram")}
                                  for model in models if model.get("digest") == DIGEST]}

    def prepare(self) -> dict:
        """One bounded empty-message model load, separate from empirical episodes."""
        deadline = time.monotonic() + 180
        remaining = lambda: max(0.01, deadline - time.monotonic())
        self._identity_check(min(5, remaining()))
        request = {"model": MODEL, "messages": [], "stream": False,
                   "keep_alive": "5m", "options": dict(HOST_OPTIONS)}
        try:
            self.budget_guard.reserve("warmup")
        except BudgetExhausted:
            raise AdapterFailure("cumulative_budget_exhausted") from None
        value = self._json('/api/chat', remaining(), request)
        self._identity_check(min(5, remaining()))
        if (time.monotonic() > deadline or value.get('model') != MODEL or value.get('done') is not True
                or value.get('done_reason') != 'load'):
            raise AdapterFailure('model_load_unverified')
        return {'request': request, 'timeout_seconds': 180,
                'response': {key: value.get(key) for key in ('model', 'done', 'done_reason', 'total_duration', 'load_duration', 'eval_count')}}
