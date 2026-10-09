# SENTINEL PI

**A local, offline prompt-injection firewall prototype for tool-using agents.**

ET AI Hackathon: Agentic Edition · Problem 2 — Agentic Cybersecurity: Prompt Injection Firewall

## Product thesis

SENTINEL PI combines untrusted-content provenance, answer-contamination safeguards, deterministic tool authorization, and a bounded regression loop. The current evidence distinguishes classifier labels, firewall actions, tool side effects, and one synthetic support-task correctness check rather than treating them as one security score.

In the indirect-injection replay, a clearly labeled deterministic simulator reads the fixture text and proposes a mock recovery-code email. The firewall withholds the flagged page before it reaches the protected proposal parser, while the authorized support ticket still completes. The support task builds its ticket from the returned synthetic customer record and checks the created ticket against the user task and record. A separate provenance-laundering probe has a proposal claim `user-task` while host context identifies an external page; the gate denies it without a side effect. The host context is supplied by trusted caller code, is not cryptographically authenticated, and is not evidence about a live model's reasoning.

The accepted public candidate raises severity only: five attack fixtures move from quarantine to block, but all 18 were already blocked or quarantined. It produces zero newly contained cases and does not reduce the protected trace's zero unauthorized side effects. The candidate is therefore described as policy hardening and regression testing, not improved attack resistance. A separate answer-contamination replay shows the synthetic baseline repeating two unsupported account claims; the protected answer guard redacts those exact fixture phrases and the canary.

## Run it

Requires Python 3.10 or newer. The application runtime uses only the Python standard library and makes no external network requests; browser traffic stays on loopback. The full test suite and curated release-archive audit also use `pypdf` from `requirements-release.txt` to inspect the deck PDF.

If `pypdf` is not already available in your Python environment, install the pinned release-audit dependency before running the full test suite or building the source archive:

```console
python -m pip install -r requirements-release.txt
```

```console
python --version
python -m unittest discover -s tests -v
python -m sentinel_pi demo --scenario indirect_injection
python -m sentinel_pi eval
python -m sentinel_pi candidate
python -m sentinel_pi serve
```

Open `http://127.0.0.1:8765` while the server is running. Stop it with Ctrl+C. The server refuses non-loopback bind addresses. Evaluation JSON and candidate evidence are written under `artifacts/`.

Useful demo scenarios are `legitimate_support`, `indirect_injection`, and `answer_contamination`. `python -m sentinel_pi package` creates and audits `artifacts/submission.zip`; the archive is built from an explicit source, fixture, test, web, documentation, public-evidence, and pitch-material allowlist and contains a SHA-256 manifest.

The GitHub Pages-compatible read-only demo is in [`public-demo/`](public-demo/). It loads a precomputed snapshot, has no API/write calls or model access, and is labeled as a deterministic simulator. Rebuild its data and standalone Pages bundle with `python -m sentinel_pi public-demo`. This writes `public-demo/data.js` and `artifacts/public-demo.zip`; the ZIP contains only the static HTML, CSS, JavaScript, data snapshot, `.nojekyll`, README, and manifest.

The editable deck is [`submission/SENTINEL_PI_Pitch.pptx`](submission/SENTINEL_PI_Pitch.pptx). Its PowerPoint-rendered PDF export is [`output/pdf/SENTINEL_PI_Pitch.pdf`](output/pdf/SENTINEL_PI_Pitch.pdf). The static site deployment instructions and private-repository warning are in [`public-demo/README.md`](public-demo/README.md). The optional model-investigator scope and release decision are in [`docs/MODEL_INVESTIGATOR_ASSESSMENT.md`](docs/MODEL_INVESTIGATOR_ASSESSMENT.md); no real model call has been made.

## What it demonstrates

- Provenance-aware handling of untrusted content, bounded Unicode normalization and Base64 text decoding, and suspicious-span evidence.
- A strict structured-classifier interface with a quarantine fallback for provider errors or invalid output. The default classifier is deterministic and offline.
- A firewall that withholds blocked or quarantined external content from the protected proposal parser. No sanitizer is implemented, so `sanitize` also fails closed at this boundary.
- A separate intent gate that checks tool name, exact argument shape, authorized customer/destination, host-bound action provenance, budgets, approval, and canary egress immediately before in-memory mock side effects. Proposal source IDs must match the source tuple supplied separately by the trusted caller and the original intent contract. It distinguishes `allow`, `deny`, and `require_approval`; pending approval never triggers a side effect.
- An answer guard for synthetic canaries and fixture-labeled exact phrases, plus constrained candidate regression checks. The evaluator distinguishes severity from containment and measures the one protected attack trace and one synthetic support task separately. Literal-rule promotion and full-policy rollback have focused tests. Promoted policy state applies to later replays in the current process; a new process starts from the default policy.
- A dashboard backed by actual local scenario replays and evaluator output.

## Current evidence and limits

The checked-in fixtures are a **public development regression corpus**, not a blind holdout or a representative security benchmark. The current corpus has 18 attack cases covering all nine configured categories and 12 benign controls. The latest run matched 49/49 expected labels, with 54 predictions and 5 extra labels; 13 cases were blocked and 5 quarantined. These category and firewall-action results do not by themselves prove end-to-end attack prevention. The one named protected attack trace recorded 0 parser admissions and 0 unauthorized email effects; the one synthetic support task passed its six ticket predicates (1/1). The latest run is in [`evidence/evaluation-public.json`](evidence/evaluation-public.json), with candidate outcomes in [`evidence/candidates-public.json`](evidence/candidates-public.json). Review [`docs/EVALUATION.md`](docs/EVALUATION.md) for denominators and limits.

This prototype has no live LLM, external content fetch, real customer records, credentials, real email, or production tool. The content-triggered agent simulator is a deterministic offline fixture harness, not observed model behavior. The unsupported-claim check matches curated phrases; it is not semantic fact verification. It does not establish real-world prevention or live-model performance. The intentionally unsafe baseline is isolated in code and only executes fictional, in-memory mock operations.

## Project guide

- [`SPEC.md`](SPEC.md) — mission, threat model, requirements, and definition of done
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — components, trust boundaries, and data flow
- [`docs/EVALUATION.md`](docs/EVALUATION.md) — corpus, metrics, observed results, and feature/depth self-assessment
- [`docs/ADVERSARIAL_REVIEW.md`](docs/ADVERSARIAL_REVIEW.md) — reproduced findings, repairs, regression evidence, and remaining caveats
- [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) — 2–4 minute walkthrough
- [`docs/DEMO_STORYBOARD.md`](docs/DEMO_STORYBOARD.md) — recording storyboard with timed screen actions
- [`docs/PITCH.md`](docs/PITCH.md) — short pitch and slide outline
- [`submission/SENTINEL_PI_Pitch.pptx`](submission/SENTINEL_PI_Pitch.pptx) — editable pitch deck
- [`docs/PUBLIC_DEMO_PLAN.md`](docs/PUBLIC_DEMO_PLAN.md) — safe hosted-demo plan; the current server stays on loopback
- [`public-demo/index.html`](public-demo/index.html) — static precomputed replay experience; no server required
- [`docs/MODEL_INVESTIGATOR_ASSESSMENT.md`](docs/MODEL_INVESTIGATOR_ASSESSMENT.md) — scoped optional AI investigator assessment and evidence requirements
- [`docs/SUBMISSION_CHECKLIST.md`](docs/SUBMISSION_CHECKLIST.md) — final verification and human review checklist
- [`docs/PACKAGE_AUDIT.md`](docs/PACKAGE_AUDIT.md) — archive inclusion and privacy rules

All records, email addresses, and recovery codes in the demo are synthetic. Email addresses use the reserved `.invalid` suffix.
