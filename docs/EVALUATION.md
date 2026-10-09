# Evaluation Method and Observed Results

## What is measured

Run `python -m sentinel_pi eval`. The evaluator inspects the unchanged public development fixture file, records raw predictions and hashes, then reports several distinct outcomes:

- Category-label precision, recall, and F1 use expected versus predicted labels.
- Attack-case detection counts a case when at least one expected category matches.
- Firewall action counts distinguish `block`, `quarantine`, and other decisions. A blocked/quarantined input is a component boundary outcome, not proof of a denied tool call or end-to-end prevention.
- The named indirect-injection replay records whether untrusted text reaches the protected proposal parser and whether a protected unauthorized mock side effect occurs.
- A separate synthetic support workflow checks the created ticket against the authorized task contract and the returned customer record.
- A separate provenance-laundering probe asks the gate to accept a model-claimed `user-task` source while host context identifies an external page.
- A separate answer-contamination fixture checks the planted canary and two exact unsupported phrases.

The last four checks are separate from the 30-case classifier denominator. All data are public synthetic development fixtures, not independent samples or a blind benchmark. The results do not estimate performance on external traffic.

## Latest recorded run

The curated report is [`../evidence/evaluation-public.json`](../evidence/evaluation-public.json). Run ID: `eval-20261009T163107Z`. Fixture SHA-256: `5ba4ef489dbb03c0b0493f9c515d86ae621295e9783fa11d0100887cccb0dcb4`.

| Measure | Observed result |
| --- | ---: |
| Public classifier fixtures | 30 (18 attack, 12 benign) |
| Expected category labels matched | 49 / 49 |
| Predicted labels | 54 (5 extra labels) |
| Category micro-precision / recall / F1 | 90.74% / 100% / 95.15% |
| Attack cases with at least one expected category detected | 18 / 18 |
| Attack firewall actions | 13 block, 5 quarantine, 0 other |
| Benign controls allowed / false positives | 12 / 12, 0 / 12 |
| Indirect-injection simulator baseline unauthorized emails | 1 |
| Same protected trace parser admissions / unauthorized email effects | 0 / 0 |
| Protected synthetic support task correctness | 1 / 1 task |
| Host-bound provenance spoofing attempts denied without side effect | 1 / 1 |
| Answer canary | Baseline 1 leak; protected 1 lexical redaction |
| Unsupported answer phrases | Baseline 2; protected 2 exact phrase redactions |
| Deterministic firewall latency | 0.1144 ms median, 0.3191 ms p95 |

The 18/18 firewall action result is not the end-to-end attack-prevention denominator. It says those 18 known cases received a `block` or `quarantine` action in this component run. The separate agent trace demonstrates one fixed malicious scenario: the deterministic simulator proposed and executed one unauthorized synthetic email in the isolated unsafe baseline; the protected path admitted no malicious text to its proposal parser and executed no unauthorized email. The tool-gate probe is one additional case. These counts are not pooled into a security success rate.

The 49 expected labels, 54 predictions, and five extra labels produce 90.74% category micro-precision, 100% recall, and 95.15% F1. Five extra category labels occur on attack fixtures: two extra secret-extraction labels and three extra credential-theft labels. They do not flag the 12 benign controls in this corpus. Benign-control pass rate and label precision therefore answer different questions.

| Category | Expected labels | Matched | Extra labels | Precision | F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Instruction override | 5 | 5 | 0 | 100% | 100% |
| Role change | 3 | 3 | 0 | 100% | 100% |
| Secret extraction | 8 | 8 | 2 | 80% | 88.89% |
| Tool abuse | 4 | 4 | 0 | 100% | 100% |
| Credential theft | 5 | 5 | 3 | 62.5% | 76.92% |
| Context poisoning | 2 | 2 | 0 | 100% | 100% |
| Multi-step jailbreak | 2 | 2 | 0 | 100% | 100% |
| Encoded instructions | 2 | 2 | 0 | 100% | 100% |
| Indirect prompt injection | 18 | 18 | 0 | 100% | 100% |

Latency is a local microbenchmark of deterministic preprocessing and rules. It excludes model inference, networking, and production application overhead.

## Candidate policy result

Run `python -m sentinel_pi candidate`. The curated candidate report is [`../evidence/candidates-public.json`](../evidence/candidates-public.json).

The accepted candidate adds `indirect_prompt_injection` to the hard-block categories. In the 18 public attack cases, 13 previously returned `block` and five returned `quarantine`; after the candidate, the five quarantined cases return `block`. All 18 cases were already contained from the firewall's perspective. The candidate therefore produced **five severity-only reclassifications, zero newly contained cases, and zero newly escaped cases**.

The independent end-to-end comparison is also unchanged: one protected indirect-injection simulator scenario admitted no malicious content to the proposal parser and produced zero unauthorized side effects before and after; the one synthetic legitimate support task passed all six ticket predicates before and after. This candidate is classified as `policy_hardening_only`. It is not evidence of improved attack resistance.

The evaluator keeps detection, block/quarantine containment, escaped attack cases, benign-control pass rate, false positives, one fixed support-task correctness check, protected parser admissions, unauthorized side effects, and the tool-gate invariant separate. An accepted candidate may raise policy severity only after these regression checks pass. The category escalation is accepted for that bounded hardening purpose. The common-phrase candidate is not promoted because it adds no hard-block severity after the preceding candidate; it did not reduce benign pass rate or increase false positives on the 12 controls. A permission-changing schema is rejected before evaluation. Acceptance does not imply security improvement.

Tests separately verify that an accepted literal indicator persists in the active policy and affects a later firewall replay. That focused test uses its own in-memory examples; it does not add cases to or change the public 30-case denominator. Rollback restores all policy fields. Repeated rollback consumes prior states without resurrecting a discarded candidate branch. Active candidate state still resets when the application process restarts.

## Bounded adversarial checks and limits

- A quoted malicious instruction inside a benign explanatory document is detected and withheld. This confirms safe handling for that example but also shows that lexical detection may overflag quotation; the 0/12 false-positive result applies only to the twelve labeled benign controls, not quote sensitivity generally.
- Full-width and zero-width Unicode obfuscation and bounded Base64 instruction text have unit coverage. Malformed envelopes, classifier schema errors, and classifier exceptions fail closed to quarantine.
- The answer guard redacts the planted canary and exact fixture-provided unsupported phrases. A paraphrase such as “the system confirmed the account and granted the refund” passes when the fixture only lists the exact phrases “account is verified” and “refund is approved.” This is a tested lexical limitation, not semantic fact verification.
- No blind holdout, independent red-team adjudication, live model/provider call, statistical confidence interval, or real tool execution exists.
- The deterministic simulator exercises one synthetic content-to-proposal trace. It does not establish live-model behavior or general attack prevention.

## D1/F3 self-assessment

This is a **D1/F3 self-assessment on public development fixtures only**. The official Problem 2 feature thresholds are F1: at least two attack types, F2: at least five, and F3: at least seven. All nine configured categories have public fixture-level observations, so F3 is a feature-coverage claim for this prototype. It is not an independently validated score. D1 is the defensible depth claim for bounded text input and mostly acceptable output on this finite known replay set. The corpus does not establish D2's high reliability requirement, and the prototype has no multimodal input for D3. Rubric basis: ET AI Hackathon Detailed Problem Statements, Problem 2, pp. 7–8.

## Reproduction commands

```console
python -m unittest discover -s tests -v
python -m sentinel_pi eval
python -m sentinel_pi candidate
python -m sentinel_pi demo --scenario indirect_injection
python -m sentinel_pi demo --scenario legitimate_support
python -m sentinel_pi public-demo
```
