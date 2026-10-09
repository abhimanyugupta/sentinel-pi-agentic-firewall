# Optional Model-Backed Investigator Assessment

## Decision

Do not add or claim model-backed investigation for this release candidate. No provider, approved credential, or cost authorization is available in this task. There is no safe way to verify an actual model response without crossing those boundaries, and a mocked provider would demonstrate only plumbing, not AI behavior.

The project therefore preserves the offline deterministic mode. It does not read machine credentials, make outbound model requests, or add a provider dependency.

## Feasible narrow design

If model access is approved later, keep the model as an untrusted incident analyst with a typed input and output boundary:

1. Host code supplies a bounded structured incident: detector outcome, suspicious spans, source hashes, fixture identity, current policy summary, and fixed regression-evaluator results. The model receives no tool credentials and no write-capable capability.
2. The response uses a closed schema with an explanation and one candidate patch: up to three known attack categories and three literal indicator phrases. Reject unknown fields, oversized strings, unsupported categories, duplicate entries, and any attempt to specify tools or permissions.
3. Present the explanation as untrusted text. Pass only the validated candidate patch to the existing `PolicyManager` candidate evaluator.
4. Promote a patch only if the current attack, benign-regression, and fixed tool-gate checks accept it. The model cannot call the activation or rollback API directly; the deterministic evaluator and normal operator path remain in control.
5. Store the model identifier, provider/version, request hash, response hash, schema result, candidate evaluation, and approval state without storing credentials or unnecessary raw incident content.

## Verification required before claiming this feature

- An approved provider, explicit credential handling, and an authorized cost ceiling.
- A real model call against synthetic evidence, with the model/version and exact output captured in a privacy-reviewed artifact.
- Tests for malformed and adversarial model output, schema rejection, evaluator rejection, and confirmation that failed candidates leave active policy unchanged.
- A successful accepted-candidate path proving that only the existing evaluator can promote the rule.
- Clear separation between a live-model incident-analysis result and the offline deterministic security traces.

Until those steps occur, describe the capability as a proposed integration boundary, not an implemented AI investigator. It is not a release blocker for the static precomputed replay demo.
