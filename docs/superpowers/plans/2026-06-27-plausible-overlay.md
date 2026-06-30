# Plausible Overlay Analytics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add isolated Plausible measurement to every generated overlay HTML page.

**Architecture:** Add one idempotent post-generation transform to the existing overlay build. Test the transform independently with temporary files, then run the complete validation pipeline before deployment.

**Tech Stack:** Python standard library, `unittest`, static HTML, Plausible Analytics.

---

### Task 1: Test analytics injection

**Files:**
- Create: `visibility/tests/test_plausible_tracking.py`
- Modify: `visibility/scripts/build_overlay.py`

- [ ] Write a test proving missing snippets are inserted once, existing snippets are not duplicated, and non-HTML files are unchanged.
- [ ] Run the test and confirm it fails because the injector is absent.
- [ ] Implement `inject_plausible_tracking()` using `Path.rglob("*.html")` and insertion immediately before `</head>`.
- [ ] Run the focused test and confirm it passes.

### Task 2: Integrate and validate

**Files:**
- Modify: `visibility/scripts/build_overlay.py`

- [ ] Call the injector after all HTML generators and before overlay validation.
- [ ] Run the full overlay build and stewardship checks.
- [ ] Prepare the Cloudflare Pages artifact and confirm every HTML page contains exactly one snippet.
- [ ] Deploy only after all checks pass.
