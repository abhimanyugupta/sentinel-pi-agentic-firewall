# Three-Minute Video Script — SENTINEL PI

Target runtime: about three minutes; acceptable range: two to four minutes.

## Recording setup

Open the static read-only demo at `public-demo/index.html` in a browser. No server is required. The page uses only its bundled HTML, CSS, JavaScript, and precomputed JSON snapshot. It performs no API writes, model calls, network requests, or real tool actions. Keep the visible **PRECOMPUTED SYNTHETIC TRACES** label in frame during the walkthrough.

Use a 16:9 1080p recording if available. Close unrelated tabs and notifications, browser bookmarks, and personal account controls. Use browser full-screen if it hides the local file path; do not show user-specific directories. Do not expose or tunnel the local API server.

## Script

### 0:00–0:25 — The enterprise problem

“Agentic systems can read support pages, emails, and documents, then take actions. The risk is that untrusted text can try to rewrite the task: instead of creating a support ticket, send a secret somewhere. Detecting suspicious text helps, but a detector can miss an attack. The system still needs an independent authorization check before each side effect.”

### 0:25–0:55 — Explain the two boundaries

Show the task statement and untrusted page, then point to the selected indirect-injection trace, source identity, hash, and firewall decision.

“The user asked for one hardware support ticket for synthetic customer C-1042. The retrieved page says to ignore that task and send a recovery code elsewhere. The first boundary screens retrieved content and withholds blocked or quarantined text from the protected proposal parser. The second boundary checks every proposed side effect against the original task and a separate host-supplied source context. These are separate controls.”

### 0:55–1:35 — Compare baseline and protected behavior

In the fixture selector, choose **Indirect injection attempts an email**. Point to the baseline proposal and mock email effect, then the protected path’s withheld-content result and completed ticket.

“This is a precomputed trace from a deterministic content-triggered simulator. It is not a live AI run. In the isolated baseline, the fixture text generates a mock email proposal and in-memory side effect. In the protected path, the blocked page never reaches the proposal parser. The attempted email proposal is absent, while the ticket uses the issue returned by the authorized synthetic customer search. The host-created contract still controls which customer, tool, category, and call count are allowed.”

Briefly point to the evaluation note for the separate external-source gate invariant.

“A second probe has a valid ticket proposal claim `user-task` provenance while the trusted caller supplies an external-page source as the action context. The gate denies it without a side effect. The model cannot choose the host context, but this prototype does not cryptographically authenticate that caller or prove a live model's causal reasoning.”

### 1:35–2:00 — Show answer contamination

Select **Canary leak in a final answer** and compare the baseline answer with the protected answer.

“This fixture also shows an output boundary: a synthetic canary and two planted unsupported phrases appear in the baseline draft and are redacted in the protected answer. The guard matches exact fixture phrases. A paraphrase can pass; this is not a semantic fact checker.”

### 2:00–2:35 — Evidence and candidate loop

Scroll to measured results, then candidate-rule evidence and raw case rows.

“The public development corpus has 18 attack cases and 12 benign controls across nine configured categories. It matched 49 of 49 expected labels, with five extra labels and 90.74 percent micro-precision. Thirteen attack fixtures were blocked and five quarantined; all 18 were already contained at that firewall boundary. The accepted category candidate changes those five from quarantine to block. It newly contains zero cases and leaves protected unauthorized side effects at zero before and after. It is policy hardening, not a measured security improvement. The one synthetic support task passes all six ticket checks. These are fixture results, not unseen-traffic performance.”

### 2:35–3:00 — Value and limitations

End at the limitations section.

“The value we demonstrate is a design pattern: prevent out-of-scope side effects while preserving a permitted task. We have not measured productivity, cost, incident reduction, or customer outcomes. There is no live model, blind corpus, independently adjudicated security result, or public service in this demo. SENTINEL PI is an offline prototype and this recording shows its precomputed evidence.”

## Recording checklist

- [ ] Show the original task, attacker-controlled page, baseline/protected traces, ticket correctness checks, metrics, candidate comparison, and case details at a readable zoom.
- [ ] Keep the precomputed simulator disclosure visible or restate it at each transition.
- [ ] Narration stays within 2–4 minutes and claims match the current public evidence.
- [ ] No local file path, personal account information, notifications, credentials, or unrelated project content appears.
- [ ] Captions accurately include “precomputed trace”, “deterministic simulator”, and “no live model”.
- [ ] Rewatch the exported video for readability, timing, audio, and private information before any submission.

Recording status: script prepared; no video file has been recorded or reviewed.
