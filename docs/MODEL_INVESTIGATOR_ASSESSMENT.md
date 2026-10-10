# Model-Backed Scope and Mitigation Investigator

## Current disposition

A separate, real local Ollama Gemma 3 agent pilot was completed and is retained only as a supplemental recorded experiment. Its source/evidence review is in [`GEMMA3_PILOT_REVIEW.md`](GEMMA3_PILOT_REVIEW.md), with sanitized machine-readable evidence in [`gemma3_pilot_evidence.json`](gemma3_pilot_evidence.json). The static player is in [`../supplemental/gemma3-pilot/`](../supplemental/gemma3-pilot/). The pilot is not merged into the stable backend, does not change the frozen deterministic evaluation, and makes no inference request when the player is opened.

The recorded model output included an attacker-targeted poisoned-ticket proposal and a separate unsupported-ticket proposal. The host IntentGate denied both. In the six-case paired development run, the screened condition completed 6/6 tasks and the unscreened condition 4/6; both conditions kept the gate active and had zero unauthorized effects. This is one reused development sample, not a prevention-rate estimate or generalized security result. The full development history exceeded the prior 24-generation authorization; no later explicit increase is recorded. That process-control failure and the persistent cumulative guard are disclosed in [`GEMMA3_PILOT_BUDGET_DEVIATION.md`](GEMMA3_PILOT_BUDGET_DEVIATION.md).

## Mitigation investigator status

An LLM-based incident investigator and model-proposed policy pipeline are **not implemented**. The recorded pilot does not propose, evaluate, or promote a mitigation. Existing deterministic candidate-policy logic remains in the stable prototype. Its accepted public category candidate changes severity only and is not represented as newly contained attacks; a separate focused regression demonstrates one synthetic containment improvement without changing the public denominator.

If an investigator is considered after the competition, keep its model output untrusted: permit only a narrow explanation and a restricted candidate proposal, submit every rule to the existing independent regression evaluator, require operator approval for activation, preserve rollback, and never allow the model to edit tools, permissions, provenance, or budget controls.

## Evidence boundaries

- The pilot uses six disclosed, reused synthetic cases and a recorded local model digest. It is neither blind nor independently adjudicated.
- The public static page displays saved evidence and cannot call the model, backend, or tools.
- Both pilot conditions retain the host gate; they do not compare against real ungated side effects.
- The deterministic 30-case development benchmark and its F/D self-assessment remain unchanged and are not pooled with the pilot.
- No production readiness, autonomous learning, statistical significance, or business impact is claimed.
