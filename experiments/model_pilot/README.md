# Isolated local Gemma 3 pilot

This directory contains the inspectable experimental model agent. It is separate from the stable deterministic backend and is not imported by its runtime. The public source package includes only this explicit file allowlist, the synthetic case set, offline tests, and cumulative-budget records. Historical raw run files, old presentation captures, model weights, caches, and unrelated artifacts are excluded. The saved final-run evidence is provided separately in `supplemental/gemma3-pilot/evidence.json` and checked by its standard-library auditor.

## Observed pilot

The final run used six disclosed synthetic development cases once in each condition and recorded 34/34 returned generations. Unscreened task correctness was 4/6; screened task correctness was 6/6. Both conditions used the same host IntentGate and had zero unauthorized mock effects. The unscreened run contained one attacker-targeted poisoned-ticket proposal and one unsupported-ticket proposal; the host gate denied both. These are observations from a small reused development sample, not a prevention-rate estimate.

The complete development history recorded 133 generation attempts: 94 responses and 39 provider errors, plus two separate warm-up requests. The prior 24-call authorization was exceeded by 109 attempts. No later increase is recorded. This is a process-control failure, and the persistent safeguard blocks further requests by default. The original deterministic 30-case benchmark remains separate and unchanged.

## Offline verification

Run from the repository root with Python 3.10 or newer:

```console
python -m unittest discover -s experiments/model_pilot/tests -v
python supplemental/gemma3-pilot/verify_evidence.py
python -m experiments.model_pilot.budget status
```

The adapter tests use offline doubles and mocked HTTP responses. The evidence verifier checks the saved actual request/response hashes, paired cases, model identity, proposals, gate decisions, task results, and side effects. Neither command contacts Ollama or rebuilds observed model results.

## Host-controlled agent path

- `pilot.py` owns the bounded multi-turn agent loop and synthetic host tool runtime.
- `ollama_local.py` permits only fixed loopback metadata/chat endpoints, rejects proxies and redirects, checks a pinned runtime and full model digest, bounds inputs/outputs/timeouts, and never pulls a model or reads credentials.
- Model output is parsed against a closed JSON proposal schema. It cannot supply trusted provenance, permissions, approval state, or an unsafe-baseline switch.
- Trusted host code binds ticket arguments to the authorized task and returned customer record. Every proposed action still passes the deterministic IntentGate immediately before an in-memory mock execution.
- `budget.py` reserves each request before `/api/chat`, persists failed attempts, uses a cross-process lock, and requires a separately recorded approval to extend the exhausted cumulative limit.
- `audit.py` independently replays a local raw run record. The public saved sanitized recording is verified with `supplemental/gemma3-pilot/verify_evidence.py` instead.

These controls are scoped to the synthetic pilot. The source IDs are host-supplied context, not cryptographically authenticated provenance; the local model experiment is not a production integration.

## Optional future local inference

No inference is authorized by this release checkpoint. The committed ledger already exceeds the generation cap, so the entry point fails closed before making a model request. A future operator must obtain new action-specific approval, use an already-installed model matching the pinned digest and runtime, and record an approved cumulative limit. Do not download weights, incur provider cost, or expose Ollama or the loopback backend.

The operator workflow is deliberately explicit:

1. Review the existing ledger with `python -m experiments.model_pilot.budget status`.
2. After separate human authorization only, record a larger cumulative limit with `python -m experiments.model_pilot.budget approve --kind generation --new-limit <approved-total> --authorization-reference <approval-reference>`.
3. Review and commit that approval record on an isolated experiment branch so the source tree is clean and the approval is durable.
4. Only then run `python -m experiments.model_pilot --approve-local-zero-cost --output <new-evidence-name>.json` against a matching model already available on loopback.

`--approve-local-zero-cost` does not increase the call budget. The separate warm-up allowance is zero by default. Do not copy the private historical raw ledger into a public release; use the sanitized saved evidence for offline review.
