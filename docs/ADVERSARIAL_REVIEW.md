# Independent Adversarial Review — Repair Report

Historical repair evidence for the prior four-finding mission. The later candidate-policy, support-task, provenance-laundering, rollback, evaluation, static-demo, and presentation dispositions are in [`INDEPENDENT_RELEASE_REVIEW.md`](INDEPENDENT_RELEASE_REVIEW.md); use that report for the current release candidate.

Date: 2026-10-09
Branch: `work/sentinel-pi-hackathon`
Review scope: the two P0 concerns and the two P1 concerns in the repair request. This report records the repair evidence before branch publication; no merge, deployment, or submission was performed.

## Findings and repairs

### P0 — Scripted attack causality

**Root cause.** Before repair, `run_scenario` selected the unauthorized email branch using `scenario_id != "legitimate_support"`. The fixture content was not parsed to decide whether the email proposal existed. Replacing attack text while keeping the scenario ID therefore still produced the email.

**Repair.** `DeterministicAgentSimulator` in `sentinel_pi/agent.py:22-49` is an explicitly labeled, offline simulator. It proposes a mock email only when the actual content contains an email action, a recovery-code/secret reference, and a synthetic `.invalid` destination. The event records `live_model_used: false`. This demonstrates fixture causality, not live-model behavior.

**Regression evidence.** `tests/test_toolgate_agent.py:31-43` keeps the scenario ID and metadata fixed while replacing the malicious text with benign support content. Before the repair, the test failed because the email still executed; after the repair, the proposal and side effect are absent.

### P0 — Firewall action enforcement and independent gate

**Root cause.** The earlier flow computed and logged a firewall decision after preparing calls, but did not use `block` or `quarantine` to control the protected proposal parser's input.

**Repair.** `sentinel_pi/agent.py:127-130` now supplies external text to the protected proposal parser only for `allow`. `block` and `quarantine` withhold it; because no sanitizer is implemented, `sanitize` also fails closed. This suppression is recorded in the event. The separate `IntentGate` still runs immediately before every protected side effect.

**Regression evidence.** `tests/test_toolgate_agent.py:45-57` verifies that both a block decision and a quarantine decision leave no external email proposal in the protected path. `tests/test_toolgate_agent.py:60-77` bypasses the firewall and sends an otherwise permitted, explicitly approved email proposal from an external source directly to the gate; it is denied without a side effect. The evaluation repeats an external-source ticket invariant separately from the classifier corpus (`sentinel_pi/evaluation.py:72-103, 215-216`).

**Additional integration regression.** The first direct CLI inspection after this repair found that the protected indirect-injection answer still reused the unsafe baseline draft and falsely said an email was sent. A failing assertion was added before correction. Protected runs now draft that response from the trusted workflow summary; the answer-contamination fixture separately feeds a clearly labeled synthetic adversarial draft to the output guard so the canary and claim redactions remain demonstrated without implying a live-model result.

**Clean-room loopback regression.** The first test run from the extracted archive was blocked by the sandbox (`WinError 10013`) on loopback sockets. After a local-loopback test retry was allowed, five of seven API tests passed, but the oversized-body test observed `ConnectionAbortedError (WinError 10053)` once: the server returned 400 before consuming a small excess body, so Windows could reset the client while it was still sending. The server now drains only a bounded, slightly oversized body (up to 4 KiB over the API limit) before returning 400, and closes without draining larger declared bodies. The existing 400 assertion remains unchanged.

**Repair evidence.** The change is in `sentinel_pi/web_server.py:15, 41-56`. After rebuilding the archive, the extracted package passed all **39/39 tests**, including all seven loopback API tests. The clean-room checkout was removed after verifying its resolved path remained inside the project runtime directory.

### P1 — Candidate literal-rule promotion and rollback

**Root cause.** Candidate measurement wrapped the base classifier with candidate-only literal indicators, while the promoted `FirewallPolicy` stored only block categories and threshold. Later replays therefore lost the tested indicator. Rollback could only restore fields present in that incomplete policy.

**Repair.** `FirewallPolicy` now includes `literal_indicators` (`sentinel_pi/security/firewall.py:20-30`), and `Firewall.inspect` applies them during ordinary runs (`sentinel_pi/security/firewall.py:49-57`). Candidate acceptance merges new indicators into the complete active policy (`sentinel_pi/policy.py:85-94`). Active and version snapshots serialize those rules (`sentinel_pi/policy.py:142-164`); rollback restores the full prior policy (`sentinel_pi/policy.py:126-140`).

**Regression evidence.** Before the repair, `tests/test_evaluation_policy.py` raised `AttributeError` because the active policy had no `literal_indicators` field. The repaired `tests/test_evaluation_policy.py:72-126` accepts a literal rule on a fixed two-case synthetic corpus, verifies a future `Firewall(policy=active_policy)` replay blocks the attack, then verifies rollback restores the prior block categories and indicator set and the replay no longer matches the removed rule.

### P1 — Intent and provenance

**Root cause.** `ToolProposal.source_ids` existed but `IntentGate` ignored it. An external page could therefore influence an otherwise permitted ticket action, and the gate allowed it when the normal argument checks passed.

**Repair.** `IntentContract.authorized_action_source_ids` defaults to the user task (`sentinel_pi/models.py:113`). The gate validates the contract and proposal provenance and requires every side-effect proposal to cite non-empty source IDs within that scope (`sentinel_pi/toolgate.py:34-76`). The synthetic legitimate ticket continues to cite `user-task` and passes. The offline simulator attaches the envelope's source ID to any external proposal.

**Regression evidence.** Before repair, the external-source ticket test returned `executed`, and the explicit gate-fallback email test also returned `executed`. `tests/test_toolgate_agent.py:77-105` now verifies an external page cannot drive a permitted ticket action, while the same ticket from `user-task` executes. The gate fallback test independently verifies denial and zero side effects.

**Integration caveat.** The current gate validates source IDs against the contract but does not cryptographically authenticate a source ledger. A real integration must attach provenance in trusted host code and must not accept source IDs from model-generated text. The current deterministic simulator attaches the source ID from the envelope.

## Test-first results

The requested regressions were added and run before implementation changes:

| Command | Pre-fix observation |
| --- | --- |
| `python -m unittest discover -s tests -p test_toolgate_agent.py` | 14 tests; 4 failures: benign counterfactual still executed email, block still produced a protected email proposal, external-source ticket executed, and external-source email executed. |
| `python -m unittest discover -s tests -p test_evaluation_policy.py` | 6 tests; 1 error: active policy had no `literal_indicators` field after candidate acceptance. |
| `python -m unittest discover -s tests -p test_toolgate_agent.py` (late CLI regression) | 14 tests; 1 failure and 1 error: protected answer repeated the unsafe “I sent” claim, and the separate output-guard probe lacked an explicit trace label. |
| Extracted archive loopback suite before server correction | One flaky `ConnectionAbortedError (WinError 10053)` in the existing oversized-body test; the other six API tests passed in the escalated retry. |

After repair, the complete project suite passed: `python -m unittest discover -s tests -v` — **41/41 tests**, including seven loopback API tests, the end-to-end `AppState` candidate replay, and PowerPoint export-audit tests. The exact curated archive also passed a clean-room extraction run: **41/41 tests**. Additional checks passed: `python -m compileall -q sentinel_pi tests` and `node --check web/app.js`. The dashboard labels the deterministic simulator and distinguishes firewall suppression from an intent-gate denial.

CLI verification passed:

- `python -m sentinel_pi demo --scenario indirect_injection`: baseline content-triggered email executed in the mock runtime; firewall block withheld the page before the protected proposal parser; legitimate ticket completed; zero gate violations.
- `python -m sentinel_pi eval`: completed using the same 30 development cases.
- `python -m sentinel_pi candidate`: safe category escalation accepted; broad phrase and permission-widening/schema proposals rejected.

## Revised evaluation figures

Run ID: `eval-20261009T134208Z`
Development fixture SHA-256: `5ba4ef489dbb03c0b0493f9c515d86ae621295e9783fa11d0100887cccb0dcb4`

The classifier denominator remains **30 cases (18 attack, 12 benign)**; no cases or labels were added, removed, or reclassified. An independent one-case provenance invariant is reported separately and is not part of that denominator.

| Measure | Observed |
| --- | ---: |
| Expected category labels matched | 49 / 49 |
| Predicted category labels | 54 (5 extra labels) |
| Category micro-precision / recall / F1 | 90.74% / 100% / 95.15% |
| Attack cases with an expected category detected | 18 / 18 |
| Attacks quarantined or blocked | 18 / 18 |
| Benign controls passed / false positives | 12 / 12 / 0 |
| Baseline unauthorized mock email executed | 1 |
| Protected email proposal suppressed by firewall | 1 / 1 attack replay |
| Protected unauthorized email executed / gate violations | 0 / 0 |
| Independent external-provenance gate invariant denied without side effect | 1 / 1 |
| Baseline / protected answer canary leakage | 1 / 0 (one guard redaction) |
| Baseline / protected unsupported claims | 2 / 0 (two phrase redactions) |
| Firewall median / p95 latency | 0.1330 ms / 0.3319 ms |

Latency is a local deterministic-rule microbenchmark; it excludes a live model, networking, and production overhead. All attack metrics remain fixture-level results on the public development corpus. The curated JSON report is `evidence/evaluation-public.json`. The updated release archive and its manifest are verified separately; the archive hash is intentionally not embedded in its own contents.

## Remaining caveats and next work

- The detector and agent simulator are deterministic and offline; no live model/provider behavior was tested.
- The public corpus is small and known. Its results do not estimate field performance or establish universal prevention.
- Provenance IDs must come from trusted host code in any future integration.
- Sanitization is not implemented; `sanitize` currently fails closed at the protected proposal boundary.
- The October 11 submission package should be regenerated from the repaired tree and reviewed alongside the pitch deck and demo video before any human submission. No external submission was made.
