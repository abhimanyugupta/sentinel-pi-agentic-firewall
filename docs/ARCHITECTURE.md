# Architecture and Security Boundaries

## Design objective

Keep untrusted-content detection informative but non-authoritative. A detector may miss an attack, so every proposed action must still pass an independent deterministic authorization check against the original task contract.

```mermaid
flowchart LR
  U[User intent contract] --> A[Agent proposes typed calls]
  U --> H[Trusted host action context]
  X[Untrusted content] --> P[Bounded preprocessor]
  P --> C[Classifier interface]
  C --> F[Firewall decision and provenance]
  F -->|allow only| A
  F -->|block or quarantine| D
  A --> G{Intent gate}
  H --> G
  G -->|allow| T[Mock tool runtime]
  G -->|deny| D[No side effect]
  G -->|require approval| Q[Approval required · no side effect]
  T --> O[Answer contamination guard]
  O --> R[Protected answer]
  F --> E[Evaluation and dashboard trace]
  G --> E
  O --> E
```

## Data path

1. A `ContentEnvelope` binds text to a supported source type, source identifier, and trust bit. The original text is bounded to 100,000 characters.
2. `Preprocessor` preserves a source hash and provenance. It removes invisible format controls, applies per-character Unicode NFKC normalization with an index map, and examines at most 32 bounded Base64 candidates. Decoded data is text-only, limited to 4 KiB, and is never executed.
3. `RuleClassifier` produces structured categories, spans, and short rationale. `parse_classification` enforces a closed schema, known categories, span bounds, and output-size limits. A classifier exception or invalid output triggers quarantine; it cannot turn into an allow decision.
4. `Firewall` combines category severity and a risk threshold to choose allow, sanitize, quarantine, or block. Blocked and quarantined text is withheld from the protected proposal parser. This prototype has no sanitizer, so `sanitize` also withholds the original text. Allow is a content-handling result, never tool authorization.
5. The offline `DeterministicAgentSimulator` makes the public attack trace reproducible by matching action, secret, and synthetic destination text in the input. It is explicitly not a live model or model-behavior measurement. For block or quarantine, its protected parser receives no external text.
6. `IntentGate` checks the proposed tool against the immutable `IntentContract`: permitted tool, exact tool schema, allowed customer or recipient, ticket category, action-source provenance, lengths, per-task call budget, approval, and synthetic-canary egress. Side-effect calls require the host caller to pass a separate `host_source_ids` tuple. The proposal's source IDs must exactly match that tuple, and every source must also be allowed by the contract. A model cannot authorize itself merely by writing `user-task` into its proposal.
   The host-supplied context is a scoped validation seam in this deterministic prototype, not cryptographic provenance, a protected execution capability, or proof of a live model's causal reasoning. A production host must mint the context from trusted orchestration and evidence handling outside model-generated text.
7. `MockToolRuntime` invokes the gate immediately before each side effect. A `require_approval` result records a pending-approval status and returns without a side effect. The only tools are synthetic customer search, ticket creation, and email. Writes are stored in memory for the current run.
8. `OutputGuard` searches the proposed final answer for known synthetic canaries and curated phrases labeled unsupported by the scenario evidence. It redacts matches and fails closed if claim metadata is malformed. The evaluator records canary and claim outcomes separately. This is lexical scenario containment, not general semantic fact verification.

## Baseline versus protected workflow

The baseline exists to make the threat visible. It uses the same fictional support task and mock tools, but deliberately bypasses authorization. The labeled deterministic simulator parses the public indirect-injection text and proposes one mock recovery-code email. This path also creates a synthetic answer draft containing the planted canary and unsupported claims. It is never connected to a real tool and is not a live-model trace.

The protected path inspects the same lower-trust page and withholds it from the proposal parser after the firewall selects `block` or `quarantine`; the email proposal is not generated on that path. The support workflow reads the record returned by the authorized customer search, uses its issue field as a task fact, and builds a ticket. The host-created task contract controls the customer, tool, category, and ticket budget; the returned record does not grant new action authority. A host-bound provenance probe presents an otherwise valid ticket proposal that claims `user-task` while the host context names an external page; the gate denies it before the mock side effect, independently of the firewall. The answer-contamination case separately feeds a labeled synthetic adversarial draft to the output guard, which redacts the canary and two fixture-labeled claims. Other protected runs draft from the validated ticket summary and do not inherit the baseline's false action claim.

## Candidate-policy loop

Candidate input is a closed schema that can add at most three known block categories or three literal indicators. It cannot edit tools, schemas, trust, thresholds, or authorization. A candidate is compared using separate attack detection, block-versus-quarantine severity, containment, escaped-case, benign-control, false-positive, end-to-end side-effect, support-task, and gate-invariant measures. The current accepted category candidate changes five attack fixtures from quarantine to block; all 18 were already blocked or quarantined, so it demonstrates policy hardening only, with zero newly contained cases and no change in protected unauthorized side effects. Acceptance is not labeled an attack-resistance improvement.

Accepted literal indicators are stored in the complete active `FirewallPolicy`, applied by subsequent replays in the current process, and serialized in policy snapshots and version history. Rejected candidates do not alter active state. A rollback stack restores one complete prior policy state at a time; a later candidate starts a new branch and cannot resurrect discarded policies. The snapshot file is currently audit output only: a new process starts from the default policy and does not restore a previously promoted candidate.

## Application boundary

`python -m sentinel_pi serve` binds to `127.0.0.1:8765` and serves the static dashboard and JSON API from the same process. The API body limit is 64 KiB. The page uses same-origin requests, a restrictive Content Security Policy, and DOM text nodes for untrusted content. There is no authentication because the server is a loopback-only synthetic demonstration; it must not be exposed to a network.

The separate `public-demo/` site is static-only. `python -m sentinel_pi public-demo` generates a data file from the deterministic simulator traces and the saved public evaluation/candidate reports, then creates a minimal Pages archive. The site contains no API client, input form, write operation, model provider, or real tool capability. `connect-src 'none'` prevents browser network connections; untrusted fixture values are inserted as text nodes. Every trace and measurement is precomputed and labeled as such. This display surface does not execute a new replay when a visitor changes scenarios.

## What is deliberately absent

No live model provider, external retrieval, browser automation, credentials, real customer data, real messaging, persistence database, cloud deployment, or production integration is included. The structured classifier protocol is an integration seam, not evidence that a provider has been tested. Deterministic rules are suitable for a transparent demo and regression loop, not a universal prompt-injection detector.
