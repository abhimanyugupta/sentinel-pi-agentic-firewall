# Final Competition Submission Checklist

## Release candidate — complete

- [x] Curated source ZIP rebuilt from the reviewed tree, hashed, manifested and privacy-audited.
- [x] Static Pages ZIP contains the deterministic replay and recorded Gemma player only, with a root `index.html`, verified manifest, no backend/model client, no external connection and no write capability.
- [x] The frozen deterministic benchmark remains 30 cases; its original labels and denominator are unchanged.
- [x] The six-case model pilot is presented separately as one reused development run: 4/6 unscreened versus 6/6 screened, with the mandatory gate retained and zero unauthorized mock effects in both conditions.
- [x] The full development history discloses 133 attempts, 94 responses, 39 errors, two separate warm-ups, the earlier 24-call cap, and the 109-attempt overrun as a process-control failure.
- [x] A persistent cumulative budget guard imports observed history and blocks further requests by default; this release preparation made zero model calls.
- [x] README, architecture, evaluation, dashboard, pitch, PDF, narration and demo storyboard use the same denominators and claim limits.
- [x] Source export includes the isolated model adapter and offline tests, but no raw run ledgers. Both exports exclude private Git history, model weights/cache, credentials, `.env` values, personal paths, blind holdouts and unrelated workspace files. The Pages archive contains no Python/backend code.
- [x] Current offline deterministic suite passed 74/74; the experimental offline suite passed 27/27. The clean-room extracted source archive also passed 74/74 + 27/27. Python/JavaScript syntax checks and the run-010 evidence integrity audit passed.
- [x] Current package privacy/manifest audits passed: source has 86 payload files (including the allowlisted experimental adapter) and static demo has seven payload assets; no `.git` metadata, secret-pattern hits, private/holdout paths or backend are included.
- [x] All four static replay scenarios and all six recorded model cases were selectable on the clean-room archive over a loopback static HTTP host. Browser requests observed were local static GETs only; CSP forbids connections. Desktop views at 1280×720 and 1440×810 were inspected without console errors. 768×375 visual rendering remains unverified.
- [x] Updated nine-slide PPTX passed available Artifact Tool import/render and layout validation. Nine-page PDF passed structural checks and visual inspection; it is image-rendered. Native PowerPoint opening remains unverified.

## Human publication and deployment — pending

- [ ] Review the final source ZIP and static Pages ZIP, manifests, SHA-256 values, claim boundaries and call-budget deviation.
- [ ] Approve publication to the exact public repository and branches: curated source to `main`, static-only assets to `gh-pages`.
- [ ] Before pushing, fetch and verify repository identity/visibility and both branch histories. Stop on unexpected remote changes; never force-push or publish private Git history.
- [ ] Push the approved archives normally and verify remote commit SHAs and trees.
- [ ] If necessary, configure GitHub Pages: **Settings → Pages → Build and deployment → Deploy from a branch → `gh-pages` → `/ (root)` → Save**. Verify the live site logged out. The local backend must remain private and loopback-only.

## Video and submission — pending

- [ ] After publication and logged-out page verification, open the Gemma player on the poisoned-ticket case and the deterministic replay in a clean window.
- [ ] Record the 3–4 minute storyboard using Windows Snipping Tool. Keep the precomputed disclosure, both proposal denials, both separate denominators and budget deviation visible.
- [ ] Generate narration from `DEMO_NARRATION_TTS.md`, synchronize the audio, and inspect the actual video for timing, legibility, audio, privacy and factual accuracy. No video or TTS audio currently exists.
- [ ] Open the PPTX in native PowerPoint if available; native PowerPoint compatibility has not been confirmed by this checkpoint.
- [ ] Confirm the current hackathon deadline, form fields, URLs, file types and size limits, then submit manually and retain the receipt. No submission has occurred.

## Reproducible offline commands

Run from the project root with Python 3.10+, Node.js and the release audit dependency available:

```console
python -m unittest discover -s tests -v
python -m unittest discover -s experiments/model_pilot/tests -v
python -m compileall -q sentinel_pi tests experiments supplemental/gemma3-pilot
node --check public-demo/app.js
node --check supplemental/gemma3-pilot/app.js
python supplemental/gemma3-pilot/verify_evidence.py
python -m experiments.model_pilot.budget status
python -m sentinel_pi demo --scenario indirect_injection
python -m sentinel_pi demo --scenario legitimate_support
python -m sentinel_pi eval
python -m sentinel_pi candidate
python -m sentinel_pi public-demo
python -m sentinel_pi package
```

Audit both generated ZIPs, verify their manifests, extract into new directories without Git metadata, and rerun the original source suite. These checks use saved evidence and offline mocks; do not invoke the live model pilot. See `RELEASE_READINESS.md` for current results and remaining limits.
