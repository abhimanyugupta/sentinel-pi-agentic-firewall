# SENTINEL PI Static Replay Lab

This folder is a self-contained, read-only static demonstration. It includes precomputed synthetic deterministic traces and public development evaluation evidence. Its nested `gemma3/index.html` page displays separately recorded real local Gemma 3 pilot evidence, including the actual poisoned-ticket proposal and denial. Both pages make no model calls, external requests, API writes, or real tool actions; the Gemma page is not live inference. The source for the optional isolated local adapter is in `experiments/model_pilot/` in the curated source export and is not present in this static bundle.

The current source and static archives are publication candidates only. Check the public branches and Pages deployment separately before treating a hosted version as current. The player exposes the actual proposal text prominently and keeps complete captured requests and responses in expandable, text-only evidence details.

The root page is the deterministic replay; follow its supplemental link to inspect the recorded model pilot. The default site works from its included HTML, CSS, JavaScript, and data files. To rebuild the deterministic trace data from the project root, run `python -m sentinel_pi public-demo`; this also creates an audited `artifacts/public-demo.zip` that can be extracted into the root of a dedicated static-site repository.

## GitHub Pages deployment

For a future approved update, extract the audited current `artifacts/public-demo.zip` into the dedicated public repository containing only the static demo bundle. The archive includes the nested recorded Gemma player and a manifest. In that repository, open **Settings → Pages**, select **Deploy from a branch**, choose `gh-pages` and the repository root folder, then save. The site URL follows the repository's GitHub Pages project-site URL pattern.

Do not configure Pages on the canonical private development repository. GitHub Pages sites are publicly accessible even when their source repository is private, and publishing from the source repository root would expose more than this demo bundle. GitHub documents that branch publishing uses either the repository root or `/docs`, and that Pages sites are public on the internet: [GitHub Pages overview](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages) and [publishing source configuration](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

The site is technically compatible with GitHub Pages. Confirm the published branch and archive hash after each approved update. The canonical development repository remains private, and its unauthenticated API server must stay on loopback.
