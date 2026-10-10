# Public Static Demo Plan

## Static-only experience

`public-demo/` is the root page for a precomputed deterministic replay lab. It includes four scenario choices, synthetic baseline/protected traces, and public development evaluation evidence. Its nested `gemma3/index.html` route presents six paired cases from a separate, already-recorded local Gemma 3 pilot. The player displays the exact observed model responses and host gate outcomes; it performs no inference and is not a live model demo.

Both routes are static-only. The Gemma page embeds sanitized run-010 evidence and uses `connect-src 'none'`. The deterministic page uses same-origin static assets and `connect-src 'none'`. Both display untrusted text as text nodes. No API server, write API, credentials, external request, live model, or real tool side effect is present. The unauthenticated Python API server must remain loopback-only.

The deterministic data can be rebuilt with `python -m sentinel_pi public-demo`; that command also produces an audited `artifacts/public-demo.zip` with the supplemental page. The public release candidate must be generated and verified from the curated source export so the branch root receives only the archive's static files and manifest.

## Proposed publication

The user has identified a dedicated public release repository and authorized preparation only. This checkpoint does not push or deploy. Before a later approved publication:

1. Inspect the public repository identity, visibility, and current `main`/`gh-pages` ancestry. If either branch has unexpected commits, stop and reconcile without overwriting.
2. Extract only the audited source archive into a clean source tree; do not copy the private checkout or its Git history.
3. Extract only the audited static archive into a separate `gh-pages` tree. Its root must contain `index.html`; it must not contain the backend, model adapter, private reports, or experimental runtime.
4. Push only the authorized public branches with normal non-force pushes after a separate action-time approval.
5. If Pages is not active, configure **Settings → Pages → Deploy from a branch → `gh-pages` → `/ (root)` → Save** after approval.
6. Verify the unauthenticated repository, Pages URL, all four deterministic scenarios, all six paired model cases, relative navigation, browser errors, and no network calls.

GitHub Pages publishes a public website. Never configure it to serve the private development repository root. Official references: [GitHub Pages overview](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages) and [publishing source configuration](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-github-pages).

## Remaining work

- Verify archive contents and checksums from a clean extraction.
- Obtain explicit publication approval after reviewing this checkpoint.
- After publication, record the final 3–4 minute video using [`DEMO_STORYBOARD.md`](DEMO_STORYBOARD.md), and inspect the exported file.
