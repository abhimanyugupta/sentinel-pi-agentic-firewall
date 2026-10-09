# Final Submission Checklist

Review date: 2026-10-09. Deadline supplied for this mission: October 11, 2026, 11:59 PM IST. Confirm the live Unstop form and its current fields before submission.

## Complete and verified for private review

- [x] The development branch contains the source, tests, public synthetic fixtures, documentation, evidence, and reviewed pitch artifacts.
- [x] The static replay lab uses a bundled precomputed snapshot. The UI was opened on a loopback-only static server and checked across all four scenarios, candidate results, ticket-correctness predicates, and per-case evidence.
- [x] Static page scripts contain no network or write API calls. Content Security Policy sets `connect-src 'none'`; untrusted text is inserted using `textContent`.
- [x] The development evaluation denominator remains 30 cases (18 attack, 12 benign). Category metrics, firewall actions, end-to-end simulator effects, support-task checks, and the separate provenance invariant are reported separately.
- [x] Candidate policy comparison reports five quarantine-to-block severity changes, zero newly contained attacks, and zero protected unauthorized side effects before and after. The candidate is policy hardening only.
- [x] PPTX imports and renders in Artifact Tool. Package integrity and layout validators report nine slides, exact 16:9 dimensions, Aptos text, and zero findings. Actual Microsoft PowerPoint opening was not verified in this environment because automation returned access denied.
- [x] The updated PDF has nine pages and was rendered and visually reviewed. It is image-only and therefore not searchable/selectable. It contains no encryption, JavaScript, form fields, links, or annotations.
- [x] No model-backed run, blind holdout, independent red-team result, public deployment, or recorded video is claimed.

## Final local verification commands

```console
python -m unittest discover -s tests -v
python -m compileall -q sentinel_pi tests
node --check web/app.js
node --check public-demo/app.js
python -m sentinel_pi demo --scenario indirect_injection
python -m sentinel_pi demo --scenario legitimate_support
python -m sentinel_pi eval
python -m sentinel_pi candidate
python -m sentinel_pi public-demo
python -m sentinel_pi package
```

Extract `artifacts/submission.zip` to a fresh directory and run the full test suite there. Verify its `MANIFEST.sha256`; inspect that only source, public fixtures, docs, tests, evidence, the reviewed PPTX, and the reviewed PDF are present. Verify `artifacts/public-demo.zip` separately: it should contain only its static allowlist plus manifest. Never expose the loopback API server.

## Incomplete before a valid public submission

- [ ] Approve the exact clean source export and publish it to a separate public repository. Do not change the canonical repository's private visibility.
- [ ] Approve a public static hosting destination, publish only the audited static demo, and inspect the URL in a logged-out browser.
- [ ] Record the 2–4 minute video from [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) and [`DEMO_STORYBOARD.md`](DEMO_STORYBOARD.md); inspect the actual file for timing, audio, legibility, and privacy. No video file currently exists.
- [ ] If submitting the editable deck, open the final PPTX in PowerPoint and confirm native-app rendering. The nine-page PDF is visually verified but image-only.
- [ ] Recheck current Unstop requirements and team fields, submit the exact materials manually, and retain the submission receipt.

## Human approval required

- [ ] Public repository destination and export contents.
- [ ] Public static-demo hosting destination and public accessibility.
- [ ] Final Unstop submission after confirming links, files, deadline, and form fields.

The optional model investigator remains deferred: no provider, real credentials, cost authorization, or successful live-model execution is available.
