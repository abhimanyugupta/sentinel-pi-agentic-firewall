"""Command-line entry point."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sentinel_pi.agent import load_demo_scenarios, run_scenario
from sentinel_pi.evaluation import ROOT, run_candidate_suite, run_evaluation, save_report


def main() -> int:
    parser = argparse.ArgumentParser(prog="sentinel-pi", description="Offline prompt-injection firewall demo")
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo", help="Replay synthetic baseline and protected workflows")
    demo.add_argument("--scenario", choices=tuple(load_demo_scenarios()), default="indirect_injection")
    evaluation = sub.add_parser("eval", help="Run the public development evaluation corpus")
    evaluation.add_argument("--dataset", default="fixtures/dev_scenarios.jsonl")
    evaluation.add_argument("--output", default="artifacts/evaluation-latest.json")
    sub.add_parser("candidate", help="Evaluate severity, common-phrase, and unauthorized policy proposals")
    sub.add_parser("public-demo", help="Refresh precomputed static replays and build a Pages-only archive")
    sub.add_parser("serve", help="Run the local-only dashboard")
    sub.add_parser("package", help="Build a curated submission archive")
    args = parser.parse_args()

    if args.command == "demo":
        print(json.dumps(run_scenario(args.scenario), indent=2, ensure_ascii=False))
    elif args.command == "eval":
        report = run_evaluation(args.dataset)
        output = save_report(report, args.output)
        save_report(report, "evidence/evaluation-public.json")
        print(json.dumps({"report": output.relative_to(ROOT).as_posix(), "metrics": report["metrics"]}, indent=2))
    elif args.command == "candidate":
        report = run_candidate_suite()
        output = ROOT / "artifacts" / "candidates-latest.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (ROOT / "evidence").mkdir(parents=True, exist_ok=True)
        (ROOT / "evidence" / "candidates-public.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(json.dumps({"report": output.relative_to(ROOT).as_posix(), "severity_hardening_accepted": report["severity_hardening_candidate"]["accepted"], "common_phrase_accepted": report["common_phrase_candidate"]["accepted"], "unauthorized_schema_accepted": report["unauthorized_schema_candidate"]["accepted"]}, indent=2))
    elif args.command == "public-demo":
        from sentinel_pi.packaging import audit_public_demo_archive, build_public_demo_archive
        from sentinel_pi.public_demo import write_public_demo_data

        snapshot = write_public_demo_data()
        output = build_public_demo_archive()
        print(json.dumps({
            "snapshot": snapshot.relative_to(ROOT).as_posix(),
            "archive": output.relative_to(ROOT).as_posix(),
            "bytes": output.stat().st_size,
            "audit": audit_public_demo_archive(output),
        }, indent=2))
    elif args.command == "serve":
        from sentinel_pi.web_server import serve

        serve()
    elif args.command == "package":
        from sentinel_pi.packaging import audit_archive, build_submission_archive

        output = build_submission_archive()
        print(json.dumps({
            "archive": output.relative_to(ROOT).as_posix(),
            "bytes": output.stat().st_size,
            "audit": audit_archive(output),
        }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
