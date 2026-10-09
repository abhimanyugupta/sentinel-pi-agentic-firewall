# Three-Minute Recording Storyboard

Target runtime: about three minutes, within the required 2–4 minute range. Use the read-only static replay lab. Every trace is precomputed and synthetic.

## Before recording

1. Run the commands in `SUBMISSION_CHECKLIST.md`, including the clean archive checks.
2. Serve the extracted public demo bundle from a static-only local HTTP server or use the final approved public URL. Do not expose, tunnel, or reverse-proxy the local API server.
3. Confirm the precomputed banner, all four fixture choices, baseline/protected columns, raw evidence, evaluation denominator, policy comparison, and support-task checks.
4. Close unrelated tabs and notifications. Hide personal account controls and local paths. Use a readable zoom and 16:9 capture where possible.

## Timed storyboard

| Time | Picture and action | Narration | Evidence to leave visible |
| --- | --- | --- | --- |
| 0:00–0:25 | Show the task “Create one hardware ticket for C-1042” beside the lower-trust page instruction to send a recovery code. | “An agent may need retrieved facts to complete a task, but retrieved text must not rewrite the task or grant new authority.” | Original user task, attacker-controlled instruction, precomputed synthetic banner. |
| 0:25–0:50 | Show the content firewall, parser boundary, original intent contract, and deterministic tool gate. | “SENTINEL PI screens content first. Every side effect then crosses a separate gate that checks the host task, tool schema, customer, approval, budget, and host-bound source context.” | Two boundaries and no-live-model disclosure. |
| 0:50–1:20 | Select the indirect-injection trace and compare the unprotected baseline with the protected path. | “This is a deterministic content-triggered simulator, not a live AI run. The baseline executes one mock email. The protected parser receives no flagged page content, and the authorized task still creates a ticket.” | Baseline mock email; protected no-email; synthetic ticket from the customer record. |
| 1:20–1:45 | Expand the synthetic task checks; show the separate provenance-laundering gate result. | “The ticket uses the issue returned by the authorized customer search. The contract sets action authority. A proposal that claims `user-task` while the trusted caller supplies an external page as its source context is denied.” | Six support-task predicates; one provenance test denied without effect; caller-context limitation. |
| 1:45–2:05 | Select answer contamination; compare baseline and protected text. | “The output guard redacts the canary and two exact unsupported phrases in this fixture. A paraphrase can pass, so the guard is lexical rather than semantic.” | One canary redaction, two exact phrase redactions, lexical limitation. |
| 2:05–2:40 | Show corpus metrics and accepted candidate comparison. | “The public development set has 18 attack and 12 benign cases, 49 expected labels, and 54 predicted labels. The accepted candidate changes five quarantine actions to block. All 18 cases were already contained, so it newly contains zero attacks and does not lower unauthorized side effects.” | Denominators, 13 block / 5 quarantine, 5 severity-only changes, 0 newly contained, 0 unauthorized side-effect change. |
| 2:40–3:00 | Close on limitations and business value. | “The architecture offers a reviewable way to keep task authority separate from retrieved content. We have not measured business impact, live-model performance, unseen-traffic reliability, or independent red-team results.” | D1/F3 public-fixture caveat, no production claim, no deployment claim. |

## Recording and edit checks

- Keep “precomputed synthetic traces” visible or repeat the disclosure when describing a trace.
- Leave enough time for the 30-case denominator and severity-versus-containment distinction to be read.
- Keep the original task, trust boundary, ticket checks, side-effect count, and candidate comparison unobscured.
- Captions must say “precomputed trace”, “deterministic simulator”, and “no live model”.
- Inspect the exported video for timing, readability, audio, privacy, and factual accuracy before submission.

## Recording status

The script and storyboard are prepared. No video file has been recorded or reviewed.
