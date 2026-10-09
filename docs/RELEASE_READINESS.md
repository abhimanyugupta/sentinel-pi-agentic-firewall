# Independent Release Readiness

Audit date: 2026-10-09. This review covers the private development branch, the deterministic backend, the Pages-compatible static replay, evaluation evidence, and the local submission artifacts. See [`INDEPENDENT_RELEASE_REVIEW.md`](INDEPENDENT_RELEASE_REVIEW.md) for reproductions and command evidence.

## Current assessment

The repaired prototype is ready for private independent review. The public static demo bundle is safe to publish as a separate static-only export after a human approves its destination. No public repository, site, release, or Unstop submission was created in this review.

The evidence is intentionally scoped. The attack proposal comes from a transparent deterministic content-triggered simulator, not a live model. The 30-case public development corpus records classifier and firewall component results; all 18 attack cases were already blocked or quarantined. The accepted policy candidate changes five quarantine actions to block, with zero newly contained attacks and no decrease in protected unauthorized side effects. Do not call that candidate an attack-resistance improvement.

The protected synthetic support task uses the returned customer-record issue and passes six ticket-correctness checks in one fixed scenario. Its task facts and action authority are separate: the host-created contract constrains the action, but source IDs are not cryptographically authenticated. The answer guard catches the planted canary and exact fixture phrases; paraphrased unsupported claims can pass.

## Verified materials

- The static lab is local HTML, CSS, JavaScript, and precomputed synthetic data. Its CSP disallows network connections, no write or model APIs are present, and the UI inserts fixture strings using `textContent`. Browser review verified the four scenario choices, baseline/protected traces, ticket predicates, candidate comparison, and expanded per-case table from a loopback-only static server.
- The public evaluation denominator remains 30 cases: 18 attack and 12 benign. The latest recorded figures and separate end-to-end checks are in [`../evidence/evaluation-public.json`](../evidence/evaluation-public.json) and [`EVALUATION.md`](EVALUATION.md).
- Candidate-policy reports distinguish policy severity from containment, unauthorized side effects, benign preservation, and task correctness. A rollback stack restores complete policy snapshots and consumes discarded versions rather than reviving a discarded branch.
- The updated nine-slide PPTX passes Artifact Tool import/render and independent package and layout validators: nine slides, 16:9 dimensions, 158 text runs in Aptos, no validator findings. Microsoft PowerPoint itself was not opened during this review because its automation endpoint returned access denied.
- The nine-page PDF was rendered from the final slide images and visually checked at full size. It is image-only, so its text is not selectable or searchable. It has no JavaScript, forms, links, annotations, or encryption. Use it as the visually verified submission copy; open the PPTX in PowerPoint locally if native-app compatibility must be confirmed.
- No live model, external retrieval, sealed holdout, independent red-team evaluation, real tool effect, or recorded video exists.

## Safe public-demo deployment

`python -m sentinel_pi public-demo` rebuilds `public-demo/data.js` from the recorded synthetic scenarios and creates the static-only `artifacts/public-demo.zip`. The archive contains only the allowlisted HTML, CSS, JavaScript, snapshot, `.nojekyll`, README, and SHA-256 manifest. It has no application server, secrets, model calls, or side-effect endpoint. The demo can be hosted on GitHub Pages or another ordinary static host with relative paths.

Do not expose the unauthenticated loopback backend. A public interactive inference service would require a separate synthetic-only deployment configuration, authentication or abuse controls as appropriate, rate limits, isolation, logging policy, and a fresh security review. No hosted service is prepared or deployed.

## Submission gates still open

1. Human review and approval of the public source export and its exact destination.
2. Publish the curated source archive to a separate public repository; keep the canonical development repository private.
3. Deploy only the static demo archive to an approved public static host and verify it from a logged-out browser.
4. Record and inspect a 2–4 minute video. The script and storyboard exist; no recording exists.
5. Confirm the current Unstop form, deadline, URLs, accepted file formats, and team fields; submit manually and retain the receipt.

No production claims, measured business-impact claims, live-model results, blind-set results, or independent validation claims are supported.
