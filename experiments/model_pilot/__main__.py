"""Operator-only pilot entry point; no API route or automatic live fallback."""
import argparse
import json
import subprocess
from pathlib import Path

from sentinel_pi.packaging import EMAIL_PATTERN, LOCAL_PATH_PATTERN, SECRET_PATTERNS, _check_text
from .budget import BudgetExhausted, BudgetGuard
from .ollama_local import LocalOllama
from .pilot import ROOT, canonical, run_pilot


def sanitized(value, counts):
    if isinstance(value, dict):
        return {key: sanitized(item, counts) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitized(item, counts) for item in value]
    if not isinstance(value, str):
        return value
    original = value
    for pattern in (*SECRET_PATTERNS, LOCAL_PATH_PATTERN):
        value = pattern.sub("[REDACTED]", value)
    value = EMAIL_PATTERN.sub(lambda m: m.group(0) if m.group(0).rsplit('@', 1)[1].endswith('.invalid') else '[REDACTED_EMAIL]', value)
    counts[0] += value != original
    return value


def main():
    parser = argparse.ArgumentParser(description="Separate local synthetic model pilot")
    parser.add_argument('--approve-local-zero-cost', action='store_true', required=True)
    parser.add_argument('--output', default='run-001.json')
    args = parser.parse_args()
    if Path(args.output).name != args.output or not args.output.endswith('.json'):
        parser.error('Output must be a simple JSON filename.')
    output = ROOT / 'evidence' / args.output
    if output.exists():
        parser.error('Evidence is immutable; choose a new output filename.')
    budget_guard = BudgetGuard()
    try:
        budget_guard.require_capacity('generation', 1)
    except BudgetExhausted as exc:
        parser.error(str(exc))
    source_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    clean = not bool(subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip())
    if not clean:
        parser.error('Commit the reviewed source before recording live evidence.')
    adapter = LocalOllama(human_approved=args.approve_local_zero_cost, budget_guard=budget_guard)
    report = run_pilot(adapter)
    report['source_commit_sha'] = source_sha
    report['source_tree_clean_before_evidence'] = clean
    try:
        report['local_inference_placement'] = adapter.loaded_model_info()
    except Exception:
        report['local_inference_placement'] = {'status': 'unverified'}
    counts = [0]
    report = sanitized(report, counts)
    report['evidence_sanitization'] = {'strings_redacted': counts[0], 'hashes_refer_to_original_strings': True}
    text = json.dumps(report, indent=2, ensure_ascii=False) + '\n'
    _check_text('pilot-evidence', text)
    if len(text.encode()) > 1_000_000:
        raise ValueError('Evidence size budget exceeded.')
    output.parent.mkdir(exist_ok=True)
    with output.open('x', encoding='utf-8') as handle:
        handle.write(text)
    print(canonical({'evidence': output.relative_to(ROOT).as_posix(), 'requests_attempted': report['requests_attempted'],
                     'summary': report['summary'], 'strings_redacted': counts[0]}))


if __name__ == '__main__':
    main()
