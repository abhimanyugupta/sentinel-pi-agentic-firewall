# Curated Packages and Privacy Audit

## Source release archive

`python -m sentinel_pi package` builds `artifacts/submission.zip` from the public allowlist: stable application source, tests, public synthetic fixtures and evidence, product documentation, static replay assets, the supplemental sanitized Gemma recording and review, an explicit 13-file experimental adapter allowlist with offline tests and budget records, and the final pitch deck/PDF. The archive must be audited after each rebuild; its SHA-256 manifest records every payload file, while the full ZIP hash is provided in the release handoff. It does not include Git metadata/history, experimental raw run ledgers, obsolete player captures, model weights/cache, internal status and handoff files, private review reports, generated runtime output, credentials, private holdouts, or unrelated workspace files.

The model evidence in the public candidate is an allowlist-transformed synthetic record with source/response hashes and host-gate outcomes. Its supplementary player is generated as a self-contained static page. The static page has a restrictive Content Security Policy (`connect-src 'none'`) and inserts untrusted strings as text. The source archive includes the isolated Ollama client and host-controlled agent loop for inspection; offline tests use mocks only. The static Pages archive contains neither adapter nor inference code. The source runner's persistent budget is exhausted and no inference is authorized by this release.

The packager accepts UTF-8 text plus one explicitly named final PowerPoint file and one PDF under the project directory. It scans PowerPoint XML, rejects external relationships and embedded media, and parses the nine-page deck PDF with `pypdf`. The PDF check rejects encryption, annotations/links, forms, embedded files, JavaScript, open actions, and unsafe content. All text, deck and PDF material is checked for credential-like patterns, non-synthetic email domains and local machine paths. The stable application runtime uses only the Python standard library.

The deterministic source archive writes a SHA-256 manifest over each payload member, then reopens and verifies every member, the manifest, paths and privacy checks. The exact ZIP is tested after clean extraction. The repository tracks `artifacts/submission.zip` as the current source candidate; `artifacts/public-demo.zip` is generated output and ignored by Git by default.

## Static Pages archive

`python -m sentinel_pi public-demo` creates `artifacts/public-demo.zip` from exactly seven static assets (`.nojekyll`, `README.md`, `index.html`, `app.js`, `styles.css`, `data.js`, and `gemma3/index.html`) plus its SHA-256 manifest. The root entry point is `index.html`. It contains the precomputed deterministic replay and the nested recorded Gemma player, but no Python backend, model client, external dependency, writable service, or API endpoint. The archive audit rejects missing or unexpected files, scans all assets, and checks that the nested page forbids runtime connections.

Both final archives are extracted into new staging directories without Git metadata. Clean-room verification runs the original deterministic suite and the separately packaged offline pilot tests. The static site is served from an ordinary loopback-only static-file server; the four deterministic scenarios and six recorded cases are exercised through their controls. The pages are static recordings and make no inference or API requests.

## Scope and limits

Selected content is code, documentation, public synthetic fixtures, audited evidence and presentation material. The audit found zero secret-pattern hits and zero private/holdout paths; non-synthetic email addresses and local machine paths are rejected by the scanner. No real customer records, credentials, blind evaluation cases, model weights, personal paths or unrelated projects are included. These mechanical checks support, but do not replace, human review of the final archive and public URLs.
