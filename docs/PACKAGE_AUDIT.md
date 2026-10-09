# Curated Packages and Privacy Audit

## Source release archive

`python -m sentinel_pi package` builds `artifacts/submission.zip` from an explicit allowlist: source, tests, public fixtures, dashboard and static-demo files, product specification, submission documentation, editable pitch deck, PDF export, and the two curated public evidence snapshots under `evidence/`. It excludes Git metadata, internal plan/status/decision and agent handoff files, the private `docs/INDEPENDENT_RELEASE_REVIEW.md` gate report, generated runtime output under `artifacts/`, virtual environments, databases, key files, and paths whose names identify private, blind, or holdout material. The private review report records the export's outer SHA-256, so it is intentionally outside that export; the ZIP manifest still hashes every included member.

The packager accepts UTF-8 text plus one explicitly named PowerPoint file and one PDF under the project directory. It scans PowerPoint XML, rejects external relationships and embedded media, and parses the nine-page deck PDF with `pypdf`. The PDF check rejects encryption, annotations/links, forms, embedded files, JavaScript, open actions, and unsafe content. Both deck formats and text files are scanned for secret-like credential patterns, non-synthetic email domains, and local machine paths. `pypdf` is pinned in `requirements-release.txt` for release audits and packaging tests; the application runtime itself uses only the Python standard library.

The deterministic source archive has a SHA-256 manifest, then reopens and verifies every member and its manifest. The manifest covers each archive member except itself. The exact generated ZIP is also tested after clean extraction. The repository tracks `artifacts/submission.zip` as the current curated release candidate; the separate `artifacts/public-demo.zip` remains generated output and is ignored by Git by default.

## Static Pages archive

`python -m sentinel_pi public-demo` writes the precomputed `public-demo/data.js` snapshot and creates `artifacts/public-demo.zip`. This separate archive has exactly six site assets (`.nojekyll`, `README.md`, `index.html`, `app.js`, `styles.css`, and `data.js`) plus its SHA-256 manifest. Its audit rejects missing or unexpected files and scans each asset. It contains no application server, tests, full fixtures, credentials, model provider, external dependency, or API/write capability.

## Scope and limits

All selected content is code, documentation, public development fixtures, evidence, or the pitch materials. There are no real customer records, real contact details, credentials, or blind evaluation cases. The demo uses a reserved `.invalid` email address and a synthetic canary. The mechanical audits are a useful gate, not a substitute for human review of future allowlist changes or the final public URLs.
