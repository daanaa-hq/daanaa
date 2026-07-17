# Architecture Overview

## High-level shape

Daanaa is a split architecture:

- The full backend handles the richer, mutable, authenticated, and operationally sensitive flows.
- The droplet backend serves the public browse/search/detail experience from precomputed files and a lean SQLite search database.
- The frontend is a React/Vite single-page app that talks to backend APIs and keeps privacy-sensitive wallet state local or account-scoped as implemented.

## Trust boundaries

- Public browsing is separate from authenticated claim, wallet, and admin paths.
- The repository explicitly treats donor funds as out of scope for the platform.
- AI-assisted enrichment is separated from deterministic calculation in both governance language and code comments.

## Confirmed user-facing surfaces

- Donor discovery through homepage, directory, search, comparison, and organization detail pages.
- Nonprofit-facing claim and dashboard pages.
- Admin and governance pages.
- Research and methodology pages.

## Architecture notes

- The repo contains evidence of both live API and precomputed/static delivery models.
- The droplet API caches search connections per worker and reopens on inode change, which is a deliberate production optimization.
- The codebase contains several overlapping naming systems:
  - `merit_score`, `merit_tier`, `merit_band`
  - v4 financial health language
  - v5 financial context language
  - cohort context language
  - hidden gem / visibility tiers
  These should be harmonized in the public vocabulary layer.

