# Cloudflare Clean URLs Design

## Goal

Make every URL published by the Cloudflare Pages overlay match the final URL
that returns HTTP 200, without changing the source export layout or the main
Daanaa application.

## Scope

- Normalize references only in `visibility/cloudflare-public`.
- Convert `https://data.daanaa.org/path/page.html` to
  `https://data.daanaa.org/path/page`.
- Convert `https://data.daanaa.org/path/index.html` to
  `https://data.daanaa.org/path/`.
- Apply the same policy to root-relative HTML links.
- Cover HTML, XML, JSON, and text discovery assets.
- Leave profile URLs, external domains, non-HTML assets, and physical filenames
  unchanged.

## Architecture

`visibility/public` remains the file-oriented source build.
`prepare_cloudflare_pages.py` owns hosting-specific transformations, so it
normalizes URL references after copying the source tree and before size
validation. This keeps Cloudflare behavior out of each content generator.

## Verification

Unit tests cover conversion and exclusions. An integration test uses a
temporary output tree to verify traversal and rewriting. Before deployment, the
full visibility tests, overlay build, stewardship check, and Cloudflare
preparation must pass. After deployment, representative canonicals and all
sitemap files must resolve without redirects.

## Deployment Safety

Only the static `daanaa-visibility` Pages project is deployed. No droplet,
database, API, or main frontend behavior changes. The main-site `robots.txt`
sitemap line remains a separate base-team deployment item.
