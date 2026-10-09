# Public Demo Plan

## Prepared now: static replay site

`public-demo/` is a read-only Pages-compatible experience. It presents generated precomputed synthetic traces and the public development evaluation snapshot. Visitors can choose four recorded scenarios, inspect baseline and protected proposals/actions/answers, review per-case classifier evidence, and see candidate acceptance/rejection results.

The static site has no API server, write operations, arbitrary visitor input, external requests, model calls, credentials, or real side effects. The CSP includes `connect-src 'none'`; JavaScript displays values with `textContent`. Its deterministic snapshot can be rebuilt with `python -m sentinel_pi public-demo`, which writes `public-demo/data.js` and a separate static-only archive at `artifacts/public-demo.zip`.

## Deploy after human approval

The canonical development repository must remain private. Do not configure Pages to publish its root. GitHub's documentation says Pages sites are public on the internet, including sites whose source repository is private; publishing only from a private source requires a supported account plan. The Pages branch source selector supports the repository root or a `/docs` folder, not an arbitrary `public-demo/` folder.

Recommended release path:

1. Review `artifacts/public-demo.zip` and its manifest.
2. Create or select a separate public repository explicitly approved for this purpose.
3. Extract the static ZIP into that repository's root. Confirm it contains only `.nojekyll`, `README.md`, `index.html`, `app.js`, `styles.css`, `data.js`, and `MANIFEST.sha256`.
4. In **Settings → Pages**, select **Deploy from a branch**, the intended publishing branch, and `/(root)`. Save only after the files have passed review.
5. Open the published URL in a logged-out browser. Test all four scenario choices, responsive layout, the precomputed/live-model disclosures, denominators, raw rows, and the absence of network/API failures.
6. Record the URL and release-archive hash in the submission package. Any public repository creation, publishing, host access, or external submission is a separate human-approved action.

Official documentation: [What is GitHub Pages?](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages), [configure a publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-github-pages), and [GitHub plans](https://docs.github.com/en/get-started/learning-about-github/githubs-plans).

## Not prepared or claimed

- No public site URL or deployment exists.
- No interactive model inference is included or necessary for this static package.
- The unauthenticated local development server remains loopback-only and must not be tunneled, reverse-proxied, or exposed directly.
- No independent deployment-security review has occurred.
