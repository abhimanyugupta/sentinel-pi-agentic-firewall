# SENTINEL PI — Incident-First Experience and Competitive Product Brief

Status: **private design proposal**, not a verified release, public deployment, or claim of new security efficacy.

## The product promise

**AI agents can be persuaded. Their tools shouldn't be.**

SENTINEL PI is a prototype **agent flight recorder and authorization boundary**: it makes an attacker's lower-trust instruction, a model-generated proposal, the independent host decision, and the resulting mock effect legible as one auditable incident. The prototype's distinctive story is not that a keyword filter is perfect. It is that an enterprise can separate agent proposals from action authority, inspect failures, and preserve the legitimate task.

The evidence supports a recorded local Gemma 3 pilot and an independent host IntentGate, not cryptographically signed provenance, a production incident-response platform, or general prompt-injection immunity.

## Design change on this branch

This branch changes only the **static public-demo presentation** and this design document. It does not modify the stable backend, deterministic fixtures, recorded model evidence, experimental model adapter, or public repositories.

- `public-demo/index.html`: replaces the generic metric-first landing header with a focused dark hero, actual model incident preview, prominent recording CTA, and a paired comparison with clear limitations. Adds a **Decision Passport** to the deterministic trace explorer.
- `public-demo/styles.css`: establishes a restrained midnight / mint / warm-risk visual system with deliberate typography, generous whitespace, strong focus states, and responsive layouts. No external fonts, images, scripts, or network requests.
- `public-demo/app.js`: builds the Decision Passport from the selected synthetic trace via `textContent` only. It shows source ID and content SHA-256, admission action, host gate decisions, and mock effects. It is a **trace view**, not a signed security certificate.

The homepage deliberately leads with **actual recorded Gemma output** while marking the underlying customer and tool environment as fictional and the playback as read-only. The subsequent 30-case replay lab remains explicitly deterministic.

## The interaction a judge should remember

1. **A malicious document** tried to rewrite a hardware-support ticket.
2. **Actual Gemma 3** proposed the attacker-targeted subject, `Refund approved by administrator`.
3. **The host gate denied** the proposed ticket because its facts were not trusted-record-backed.
4. **With screening**, the model instead used the authorized record and completed the correct ticket.
5. **The gate was present in both conditions**: zero unauthorized mock effects in both. The six-case paired observation was 4/6 correct unscreened and 6/6 screened. This is a reused development sample, not a statistical result.

The deterministic Decision Passport is a separate illustration of the trust boundary, not the source of those real-model observations. Do not combine its 30-case denominator with the Gemma six-case denominator.

## Design quality bar before release

- First screen at 1440px should show the product promise, a legible real-model incident, and an unmistakable recording CTA. No giant dashboard of decontextualized metrics.
- The actual Gemma recording should remain one click away, and the static replay should be immediately reachable by keyboard and mouse.
- At 375px mobile width, no horizontal scroll, clipped status labels, inaccessible buttons, or unreadable raw evidence. At 768px, the incident comparison and passport should stack cleanly.
- Keyboard tab order, visible focus, semantic headings, `prefers-reduced-motion`, contrast, and meaningful link labels must be checked.
- No third-party fonts, trackers, runtime API calls, DOM HTML injection, or animated fake "live" indicators.
- Ensure the generated `public-demo.zip` includes the changed files and its SHA-256 manifest matches. Confirm all public demo and packaging tests pass.
- Review in a real browser at 1440px, 768px and 375px. This branch was authored by GitHub connector and has **not** been browser-rendered or test-executed by the author.

## Signature innovation to consider, if it can be done offline before submission

**Paired recorded Decision Passport:** from one frozen incident, show what differs between the unscreened and screened recordings at four checkpoints: document admission, actual model proposal, host gate decision, and legitimate-task completion. The user can compare the two **recorded** paths without new inference. Derive cards directly from the existing sanitized evidence; do not invent a simulated attack or claim causal certainty beyond the observed input difference.

This is the highest-value optional UI enhancement because it transforms a log into an understandable trust-boundary debugger. If there is insufficient time, ship the existing paired Gemma player and the new incident-first homepage instead.

## Research-informed positioning, not copied research

- **CaMeL, "Defeating Prompt Injections by Design"** (arXiv:2503.18813): motivates the separation of trusted control flow, untrusted data, and capability-checked actions. SENTINEL PI does **not** implement CaMeL's proof system or inherit its guarantees.
- **AgentDojo** (arXiv:2406.13352): motivates reporting legitimate task utility alongside attack outcomes.
- **AutoDojo** (arXiv:2606.15057): shows why fixed attack fixtures and underspecified user actions remain problematic; do not claim general robustness from the small development sample.
- **PromptArmor** (arXiv:2507.15219): a reminder that filtering is an established baseline, so our differentiated claim should be observable, host-governed tool execution rather than classifier novelty.

## Do not sacrifice submission readiness

No new model calls without new explicit approval. No public publication, Pages deployment, repository visibility changes, or Unstop submission without explicit human authorization. Avoid adding a new backend or attempting a large adaptive benchmark before the deadline. Finish evidence UI, video, deck consistency, and submission first.
