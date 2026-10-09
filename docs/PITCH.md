# Pitch and Slide Outline

## Short pitch

An agent asked to create a support ticket may read a page that says to ignore the task and send a recovery code elsewhere. Detecting hostile text helps, but detection alone cannot authorize a tool call. SENTINEL PI places two independent checks in the path: a content firewall with provenance, then a deterministic tool gate bound to the original task and a separate host-supplied action context. In one deterministic synthetic replay, the unprotected baseline executes a mock email while the protected parser receives no flagged page content and still creates a ticket from the customer record. On 30 public development cases, 18/18 were blocked or quarantined. The accepted policy candidate changed five quarantine decisions to block, but newly contained zero cases. These are fixture results, not live-model or independent-test evidence.

## Nine-slide outline

1. **SENTINEL PI** — A second decision boundary for agent tools. Label the prototype offline and deterministic.
2. **The task and the attack** — Show the original support request and the lower-trust instruction to send a recovery code.
3. **Two security boundaries** — Show firewall withholding and the separate host-bound intent gate.
4. **Baseline versus protected trace** — Show the baseline mock email, the protected no-email path, and the ticket built from the returned synthetic customer record.
5. **Measured development evidence** — Show the 30-case denominator, 49 expected labels, 54 predictions, 13 block / 5 quarantine actions, and 12/12 benign controls.
6. **Candidate policy result** — Show five quarantine-to-block severity changes, zero newly contained cases, the unchanged zero protected side effects, and literal-rule/rollback unit-test evidence.
7. **Enterprise value hypothesis** — Explain why separating evidence from authority could help control unintended side effects while preserving permitted work. Label impact unmeasured.
8. **D1/F3 self-assessment** — Explain that F3 is a public-fixture feature-coverage claim across nine configured categories, not an independent score; D1 is the bounded text depth claim.
9. **Limits and next review** — No live model, blind holdout, independent red-team adjudication, production integration, public deployment, or measured business impact.

## Suggested next ambitious milestone

After submission, build an independently adjudicated evaluation workbench with versioned attack transformations, an evaluator-only sealed set, model/provider adapters, and confidence intervals across model versions. Keep the deterministic tool gate fixed while benchmarking. Do not mix private holdout content into public policy proposals.
