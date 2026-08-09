# Daanaa Search — Claude Code Audit Prompt

**How to use:** Place `daanaa_search_architecture.md` (the plan) somewhere in your repo — e.g. `docs/search_architecture.md`. Then open Claude Code in the project root and paste the prompt below. Adjust the one path if you put the file elsewhere.

This is a **read-only** diagnostic. It does not modify data, pipeline code, install packages, or write files unless you explicitly ask it to afterward.

---

## The prompt

> Audit the Daanaa search pipeline against its plan, and measure search quality. **Read `docs/search_architecture.md` in this repo first** — that document is the plan (the seven-step build order, the fair-ranking rules, the forbidden ranking inputs, the four-tier honesty model). Audit against what it actually specifies, not against assumptions.
>
> This is a **read-only** inspection: do not modify data or pipeline code, do not install anything, do not create files. Report findings as a checklist with ✅ / ⚠️ / ❌ per item.
>
> **Step 0 — Discover the real entry points.** Inspect the repo to find: the search function (takes a query string, returns ranked orgs), the DuckDB file path, and the org table with its revenue-band / NTEE / location columns. Adapt to the actual names and signatures in the code — do not assume function names or schema.
>
> **Step 1 — Find or flag the labeled query set.** Search for a file or table pairing queries with expected org EINs (try names like `queries`, `eval`, `labeled`, `ground_truth`, `test_queries`; check `.json` / `.csv` / `.yaml` and DuckDB tables). Report whether one exists and how many labeled queries it contains. If none exists, say so plainly and continue with the label-free checks — do not fabricate ground truth.
>
> **Step 2 — Run a query batch through the LIVE pipeline.** Use the labeled queries if found; otherwise use this starter batch: `["food bank near Houston", "after school programs for kids", "help homeless veterans", "animal rescue", "mental health support for teens", "disaster relief", "literacy programs", "environmental conservation", "refugee resettlement", "cancer research"]`. For each query, capture the top-10 ranked results with each org's revenue band, NTEE code, location, and four-tier label.
>
> **Step 3 — Compute label-free metrics:**
> - **Fairness invariant (CRITICAL):** within each result list, detect any case where a higher-revenue org outranks a lower-revenue org that matches the query intent at least as well (approximate "matches as well" using the pipeline's own relevance score when no labels exist; note this is approximate). Report every violation with the query and the two orgs. Per the plan, ranking must NEVER favor org size — revenue must not be a sort input. Flag loudly if it is.
> - **Small-org surfacing rate:** % of top-10 results that are sub-$50K / 990-N filers, per query and overall.
> - **Geographic diversity:** distinct states/cities represented in top-10 — are results concentrated in a few metros or spread out?
> - **Four-tier completeness mix:** distribution of Full / Strong / Financial-Only / Listed-Only across results.
>
> **Step 4 — Compute label-dependent metrics ONLY if a labeled set was found:** Recall@10 and mean reciprocal rank, per query and overall.
>
> **Step 5 — Verdict.** Map findings to the seven-step build order in the architecture doc and state: (a) does ranking respect the no-size-bias rule — pass/fail with evidence; (b) are small orgs surfacing; (c) whether correctness is measurable yet or a labeled set must be built first; (d) which build-order step we're actually on and the single next action. Be honest — if something is missing, say missing; do not infer it exists.

---

## Notes & caveats

- **The starter query batch is a stopgap**, not a real evaluation set. Ten generic queries can't measure search quality properly. If this confirms no labeled set exists, building one (~100 queries paired with the orgs that *should* surface, authored from your own knowledge of the data) is the highest-value next task.
- **The fairness check has a soft spot when unlabeled:** judging "matches intent at least as well" without ground truth leans on the pipeline's own relevance score, which is mildly circular. It reliably catches egregious size bias; subtle cases need the labeled set to confirm.
- **Recall is the only metric that strictly requires labels** — everything in Step 3 runs today regardless.
