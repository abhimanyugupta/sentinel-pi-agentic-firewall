# Pitch and Slide Outline

## Short pitch

AI agents can be persuaded. Their tools should not be. SENTINEL PI is a prompt-injection firewall and agent flight recorder that shows the lower-trust source, an actual model proposal, the independent host decision, and the resulting mock effect. The project pairs a deterministic offline prototype with a separate recorded local Gemma 3 pilot. In one reused six-case development run, task correctness was 4/6 unscreened and 6/6 screened; both conditions kept the same IntentGate and had zero unauthorized mock effects. This is inspectable prototype evidence, not a blind prevention estimate or production claim.

## Nine-slide outline

1. **SENTINEL PI** — “AI agents can be persuaded. Their tools should not be.” State that the stable prototype is deterministic/offline and the Gemma pilot is a separate saved recording. Static pages make no inference or API requests.
2. **The incident** — Show the authorized hardware-support task and the lower-trust document that asks for a ticket reading “Refund approved by administrator.” The actual poisoned-ticket proposal and denial appear immediately in the opening video segment.
3. **Two boundaries** — Diagram the stable deterministic firewall and IntentGate. Explain that screening controls which content reaches the agent, while the host gate independently decides whether a proposed tool action matches the task. Note that the recorded Gemma adapter is isolated from the stable backend.
4. **Recorded Gemma comparison** — Show the exact poisoned-ticket fields proposed by Gemma in the unscreened condition, the host denial, and no side effect. Compare with the screened record-backed ticket. Both conditions use the same gate. Report six reused cases once per condition, tasks 4/6 versus 6/6, three benign tasks correct in both, and zero unauthorized mock effects in both. The final run returned 34/34 model generations.
5. **Separate deterministic evaluation** — Keep the 30 known public development cases separate: 18 attack / 12 benign, 49/49 expected category labels matched, 54 predictions including five extra labels, 13 block / 5 quarantine, and 12/12 labeled benign controls allowed. These are component results, not end-to-end model prevention.
6. **Candidate policy result** — The accepted public candidate changes five quarantine actions to block and newly contains zero benchmark cases. Call this policy hardening. A focused two-case development regression is separate and does not change the 30-case denominator.
7. **Enterprise relevance** — Show a deterministic synthetic support task and explain the possible control point before CRM, ticketing, or messaging actions. Mark integration value as a hypothesis: no business impact has been measured.
8. **Rubric self-assessment** — Show D1/F3 only against the public development fixtures. Nine configured types are present in those fixtures; the text-only finite replay supports the stated D1 assessment. The Gemma pilot is separate and does not count toward the rubric evidence.
9. **Limits and next step** — No blind evaluation, independent red-team adjudication, statistically reliable model improvement, production integration, or measured business impact. Disclose the historical 133 generation attempts versus the earlier 24-call cap (39 provider errors) as a process-control failure. End with a request for independent evaluation using new, predeclared cases.

## Claim boundary

The deterministic 30-case evaluation and the Gemma six-case pilot have separate sources and denominators. The pilot is one reused development run, not a model-security benchmark. Since both pilot conditions retained the same gate, zero unauthorized effects do not establish an input-screening effect on tool safety. The observed task-correctness difference is not statistically reliable and does not establish generalization. The deterministic simulator did not generate the recorded Gemma proposal.

## Opening sequence

Show the actual recorded `create_ticket` proposal containing `Refund approved by administrator`, followed immediately by the host IntentGate denial and zero unauthorized effects. Then reveal the original task and poisoned lower-trust document, followed by the screened record-backed ticket. This is the first 15–20 seconds of the video.

## Suggested next ambitious milestone

After the hackathon, run a preregistered paired evaluation with independently authored synthetic tasks, unseen attack transformations, and deterministic task validators. Freeze the authorization gate while measuring proposal, refusal, task-correctness, and side-effect outcomes separately across model versions.
