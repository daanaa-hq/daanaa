# 2026-08-13 — Charter-Safe Product Roadmap Handoff

**Date:** 2026-08-13  
**Owner:** Codex  
**Primary task:** `institution/tasks/T-2026-08-13-002-charter-safe-product-roadmap.md`

---

## Executive Summary

Codex has started autonomous shadow work on a charter-safe product program.

This is not a production push yet. It is a controlled execution model:

1. build only what is clearly allowed now
2. document approval gates before crossing them
3. keep provenance, privacy, and visibility neutrality intact

The immediate thesis is:

- Daanaa already has the right data and mission
- the main problem is fragmented user journeys
- the next product work should unify discovery, decision support, nonprofit clarity, opportunities, and retention

---

## What Can Start Now

### 1. Discovery UX and IA
- homepage intent paths
- directory search/filter cleanup
- mobile scanability
- local and cause-first discovery improvements

### 2. Organization Page Rework
- stronger summary header
- clearer evidence hierarchy
- provenance-safe separation:
  - public record
  - nonprofit-provided
  - inferred / AI-assisted

### 3. Nonprofit Clarity Layer
- better claim/edit flow structure
- structured nonprofit-supplied sections
- clearer correction and attestation flows

### 4. Opportunities, Volunteer, and Action Layer
- elevate giving and volunteering as first-class paths
- support claimed nonprofits publishing structured opportunities
- default to unrestricted support plus volunteer / skilled-help / in-kind needs
- keep restricted-purpose opportunities behind tighter review

### 5. Retention Without Becoming A Newsletter
- build return value from relevance, saved intent, and fresh opportunities
- avoid spam, guilt loops, and surveillance-heavy retention

### 6. Quality Hardening
- accessibility remediation
- live-path QC
- performance work on priority routes

---

## What Must Stop At Specification

Do not activate these without explicit founder approval:

1. ranking or visibility logic changes
2. public scoring, badges, or evaluative methodology changes
3. monetization that touches exposure or treatment
4. new AI-generated judgments that can be read as ratings
5. production migrations
6. deployments
7. private nonprofit data expansion outside current stewardship boundaries
8. activation of restricted-purpose opportunities without approved policy

---

## Recommended Working Order

### Batch 1
- `frontend/src/pages/Home.tsx`
- `frontend/src/pages/Directory.tsx`
- `frontend/src/components/SearchBar.tsx`

Goal:
- improve first-time discovery clarity and remove avoidable friction

### Batch 2
- `frontend/src/pages/OrganizationDetail.tsx`
- org-detail child components

Goal:
- convert the org page into a decision page with explicit provenance

### Batch 3
- claim/editor/nonprofit-facing surfaces

Goal:
- make nonprofit value real, visible, and stewardship-safe

### Batch 4
- volunteer routes and action pathways
- opportunity publishing surfaces

Goal:
- make action-taking more visible without turning Daanaa into a transaction processor or crowdfunding host

### Batch 5
- return-loop and retention surfaces

Goal:
- make the product worth revisiting without turning it into a newsletter, feed, or pressure engine

---

## Guardrails For Claude Code

Treat these as hard rules:

- no pay-to-win mechanics
- no merged truth layers
- no deployment
- no migration
- no methodology drift hidden inside UX work
- no restricted-opportunity launch without explicit policy approval
- no claim that external plugin work is complete unless directly verified

When in doubt:
- implement Track A work
- document Track B work
- stop before public-behavior changes that imply governance decisions

---

## Current Codex Position

Codex has enough context to proceed without more product discovery questions.

Expected next moves:

1. begin Batch 1 shadow work
2. draft an evidence-backed opportunities and retention model
3. keep repo-visible documentation current
4. surface approval gates only when a change crosses governance, migration, deployment, or methodology boundaries

---

## Requested Claude Response Mode

If Claude is coordinating parallel work, the cleanest split is:

- Claude executes implementation chunks from Batch 1 or Batch 2
- Codex keeps skeptical review on stewardship, quality, provenance, and user-journey coherence
- both sides update repo-visible task/handoff records instead of relying on chat-only status
