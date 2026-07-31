# Local Model Routing

`stewardship_core.routing.ModelRouter` is provider-neutral and local-only. It
routes protected data only to explicitly registered local adapters. Unsupported
context sizes fall back to deterministic processing for structured tasks or
manual review for interpretation/drafting. Results below the request confidence
threshold become `needs_review`.

No external provider is configured. Gmail and Calendar are not connected.
