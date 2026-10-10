# Final 3–4 Minute Recording Storyboard

This single storyboard starts with the actual recorded poisoned-ticket proposal and host denial. It then compares the paired Gemma condition, explains the deterministic prototype, and keeps every evidence denominator separate. The Gemma player is read-only playback; it does not make inference or API requests.

| Time | Screen action | Narration focus | Evidence to leave visible |
| --- | --- | --- | --- |
| 0:00–0:15 | Open the Gemma player with **Poisoned ticket** selected. Point to `Refund approved by administrator`, then the red host denial. | Gemma actually proposed this ticket; the host IntentGate denied it before a mock effect. | Actual recorded output; source-scope denial; zero unauthorized mock effects. |
| 0:15–0:40 | Keep the original task and lower-trust document in view. Point out that the task asks for a hardware support ticket and the document attempts to replace its facts. | Explain why an agent needs the customer record but must not treat the retrieved document as task authority. | Authorized task; attacker-controlled synthetic document; model digest and saved-record label. |
| 0:40–1:05 | Compare the screened column for the same case; then choose **Unsupported ticket**. | The firewall withheld the attack document; Gemma used the authorized record. A second unsupported proposal was denied by the same gate. | Record-backed issue; ticket proposal; separate denial; no live execution. |
| 1:05–1:35 | Show paired metrics and the final-run/full-history distinction. | Six reused cases once per condition; 4/6 versus 6/6 correct tasks; 3/3 benign in both; zero unauthorized effects in both because the same gate remained active. Briefly disclose the full-history call-budget overrun. | 34/34 final-run generations; 133 historical attempts, 39 errors, earlier cap 24, no explicit increase recorded. |
| 1:35–2:20 | Open the deterministic replay and the Decision Passport. Select **Indirect injection** and trace source, firewall, proposal, gate, and effects. | The stable backend is a deterministic offline simulator; it is separate from the actual Gemma run. Explain the two independent boundaries. | Precomputed synthetic trace; host-created task; content decision; gate result; mock effect. |
| 2:20–2:50 | Show the deterministic evaluation and policy-candidate result. | Thirty public development cases; component category results; candidate hardening changes five quarantine decisions to block but newly contains zero benchmark cases. | Keep the 30-case denominator separate from the six-case pilot; label results as component-level. |
| 2:50–3:25 | Show enterprise integration opportunity and limitations. | The architecture suggests a reviewable control point before CRM, ticketing, or messaging, but no production integration or business impact has been measured. Ask for independent evaluation with new cases. | D1/F3 is a public-fixture self-assessment; no blind tests, production claim, or statistically reliable model result. |

## Capture checklist

- Record only after the public release is approved, Pages is active, and the site is verified in a logged-out browser.
- Use the static pages only. Confirm there are no model or backend requests during recording.
- Start with the actual poisoned-ticket proposal and denial, and keep the read-only recorded-evidence label visible.
- Show the unsupported-ticket denial and the 4/6 versus 6/6 task counts, with zero unauthorized effects in both conditions.
- Show the deterministic simulator disclosure and its separate 30-case denominator.
- Keep the full-history budget overrun disclosure accessible; do not make it the opening story.
- Use a readable 16:9 browser view with unrelated tabs, account controls, notifications, local paths, and credentials out of frame.
- Inspect the complete exported video for readability, timing, narration sync, audio quality, and privacy before submission.

Recording status: storyboard prepared. No video or audio file has been recorded or inspected.
