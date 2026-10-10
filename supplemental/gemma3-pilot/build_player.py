"""Build the self-contained static player from the bundled recording only."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path

from verify_evidence import verify

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]


def _hash(value: str) -> str:
    return base64.b64encode(hashlib.sha256(value.encode("utf-8")).digest()).decode("ascii")


def safe_json_for_script(value: object) -> str:
    text = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    return (text.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
            .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def build(output: Path) -> Path:
    output = output.resolve()
    try:
        output.relative_to(PROJECT_ROOT.resolve())
    except ValueError as exc:
        raise ValueError("player_output_must_remain_in_project") from exc
    verify(HERE / "evidence.json")
    evidence = json.loads((HERE / "evidence.json").read_text(encoding="utf-8"))
    template = (HERE / "index.template.html").read_text(encoding="utf-8")
    styles = (HERE / "styles.css").read_text(encoding="utf-8")
    app = (HERE / "app.js").read_text(encoding="utf-8")
    budget = json.loads((HERE / "budget_deviation.json").read_text(encoding="utf-8"))
    inline_script = ("const PILOT_EVIDENCE = " + safe_json_for_script(evidence) + ";\n"
                     + "const PILOT_BUDGET = " + safe_json_for_script(budget) + ";\n" + app)
    replacements = {
        "@@SCRIPT_HASH@@": _hash(inline_script),
        "@@STYLE_HASH@@": _hash(styles),
        "@@INLINE_SCRIPT@@": inline_script,
        "@@INLINE_STYLES@@": styles,
    }
    page = template
    for marker, value in replacements.items():
        page = page.replace(marker, value)
    if "@@" in page:
        raise ValueError("unresolved_player_template_marker")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding="utf-8", newline="\n")
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "public-demo" / "gemma3" / "index.html")
    args = parser.parse_args(argv)
    output = build(args.output)
    print(json.dumps({"output": output.relative_to(PROJECT_ROOT).as_posix(),
                      "evidence_verified": True, "live_requests": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
