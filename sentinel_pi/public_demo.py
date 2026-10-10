"""Build a read-only static page from recorded synthetic project evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sentinel_pi.agent import load_demo_scenarios, run_scenario

ROOT = Path(__file__).resolve().parent.parent
DEMO_DATA = ROOT / "public-demo" / "data.js"


def _read_json(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def build_public_demo_snapshot() -> dict[str, Any]:
    """Return sanitized deterministic traces plus the committed public evidence."""
    traces = []
    scenarios = load_demo_scenarios()
    scenario_order = (
        "indirect_injection",
        "legitimate_support",
        "answer_contamination",
        "encoded_instruction",
    )
    for scenario_id in scenario_order:
        if scenario_id not in scenarios:
            raise ValueError(f"Required public demo scenario is missing: {scenario_id}")
        trace = run_scenario(scenario_id)
        # These values are execution noise, not evidence. Removing them makes the
        # data artifact stable while preserving every security-relevant trace.
        trace["run_id"] = f"precomputed-{scenario_id}"
        trace.pop("created_at", None)
        trace.pop("duration_ms", None)
        trace["intent"]["task_id"] = f"precomputed-{scenario_id}"
        traces.append(trace)

    evaluation = _read_json("evidence/evaluation-public.json")
    candidates = _read_json("evidence/candidates-public.json")
    return {
        "schema_version": 1,
        "label": "PRECOMPUTED SYNTHETIC REPLAYS",
        "simulator": {
            "name": "deterministic-content-triggered-simulator-v1",
            "live_model_used": False,
        },
        "evaluation": evaluation,
        "candidates": candidates,
        "traces": traces,
    }


def write_public_demo_data(output: str | Path = DEMO_DATA) -> Path:
    """Write a same-origin JavaScript data file; the page needs no API server."""
    output_path = Path(output)
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    resolved = output_path.resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError("Static demo data output must stay inside the project.") from exc

    snapshot = build_public_demo_snapshot()
    serialized = json.dumps(snapshot, ensure_ascii=True, indent=2, sort_keys=True)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        "// Generated from public synthetic fixtures and committed evaluation evidence.\n"
        "// This is precomputed data; loading this file performs no model or API call.\n"
        f"window.SENTINEL_PI_DEMO_DATA = {serialized};\n",
        encoding="utf-8",
        newline="\n",
    )
    return resolved
