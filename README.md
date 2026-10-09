# SENTINEL PI Static Replay Lab

This folder is a self-contained, read-only static demonstration. It includes precomputed synthetic traces and public development evaluation evidence. It makes no model calls, external requests, API writes, or real tool actions.

The default site works from its included HTML, CSS, JavaScript, and data files. To rebuild the recorded trace data from the project root, run `python -m sentinel_pi public-demo`; this also creates an audited `artifacts/public-demo.zip` that can be extracted into the root of a dedicated static-site repository.

## GitHub Pages deployment

After the public export and destination have been approved, extract `artifacts/public-demo.zip` into a dedicated public repository containing only the static demo bundle. In that repository, open **Settings → Pages**, select **Deploy from a branch**, choose the intended publishing branch and the repository root folder, then save. The site URL follows the repository's GitHub Pages project-site URL pattern.

Do not configure Pages on the canonical private development repository. GitHub Pages sites are publicly accessible even when their source repository is private, and publishing from the source repository root would expose more than this demo bundle. GitHub documents that branch publishing uses either the repository root or `/docs`, and that Pages sites are public on the internet: [GitHub Pages overview](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages) and [publishing source configuration](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

The site is technically compatible with GitHub Pages. Account-plan access and any public repository creation or deployment still require a human to verify and approve them. The current private source repository remains unchanged.
