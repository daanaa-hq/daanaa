# Plausible Overlay Analytics Design

## Goal

Measure discovery traffic on `data.daanaa.org` and journeys to `daanaa.org` using the existing Plausible `daanaa.org` property without changing the main application.

## Design

The overlay build adds the standard Plausible script to every generated HTML document after all page generators complete. The injector is idempotent, operates only on `.html` files under `visibility/public`, and leaves XML, JSON, CSV, and text discovery assets unchanged.

Plausible uses the existing `daanaa.org` site property, which supports the main domain and subdomains in one visitor journey. Page paths and hostnames distinguish overlay traffic. Automatic outbound-link measurement is enabled in Plausible's Site Installation settings so clicks from discovery pages to canonical nonprofit profiles can be measured.

## Verification

Automated tests verify insertion, idempotency, and non-HTML isolation. The overlay validator and live deployment checks remain required before release.

## Guardrails

- No cookies or identity tracking are introduced.
- Analytics does not affect rankings, nonprofit ordering, or claim logic.
- No droplet application files are changed.
- A failed analytics request cannot prevent page content or links from loading.
