# AI Memory Migration — Security and Scope Exclusions

**Date:** 2026-07-11  
**Authority:** Founder Ruling 2026-07-11, item 2  
**Standard:** "Do not directly copy the complete contents of ~/.claude/projects/meritgiving/memory/ into git."

---

## Categories of Content Excluded from institution/ai-memory/

This document explains what types of information are NOT migrated and why.

### 1. Raw Conversational History

**What:** Full transcripts of conversations between founder and Claude.

**Why excluded:**
- Contains transactional details (clarifying questions, attempts, dead ends)
- No durable institutional value (process, not knowledge)
- Reduces signal-to-noise for future readers
- Successor needs decisions and lessons, not debate

**Preserved instead:** Extracted decision (final reasoned choice), reasoning, and any overruled alternatives worth remembering.

**Example:** A 40-message thread that converged on "use local Vulkan for embeddings" → Reduced to:
```
Decision: Local Vulkan embedding server (port 11436)
Reasoning: Cloud APIs cost; local batch processing efficient; self-hosted keeps inference auditable
Date: 2026-06-15
Status: Live
```

---

### 2. Credentials and Access Tokens

**What:** Any API keys, SSH keys, passwords, service-account JSON, tokens, secrets.

**Why excluded:**
- Security exposure if repo is ever public
- Rotation makes them outdated within weeks
- Belong in env/secrets management, never in history

**Preserved instead:** Reference to which system uses the credential type, and *where* the current value is stored (e.g., "Twilio auth in ~/meritgiving/.env").

---

### 3. Personal Information (PII)

**What:** Nonprofit donor names, addresses, phone numbers, email; founder personal email (non-daanaa.org); personal health/financial data.

**Why excluded:**
- STEWARDSHIP.md Principle 2: Privacy is structural
- Violates PRIVACY-INVARIANTS.md
- Harmful if disclosed; no institutional value

**Preserved instead:** Aggregate patterns (e.g., "123 nonprofits had contact-email typos; developed validation rule to catch them").

---

### 4. Vendor-Specific Artifacts

**What:** Chroma vector database files, mempalace embeddings, proprietary model outputs, vendor-specific formats.

**Why excluded:**
- Non-portable (depend on specific vendor or model version)
- Rebuildable from source
- Become stale if vendor changes
- Belong in caches, not institutional memory

**Preserved instead:** Decision log explaining *why* we use that vendor, *how* to rebuild if needed.

---

### 5. Machine-Specific Configuration

**What:** Home server paths (/home/akbar), hardware MAC addresses, local port numbers, internal IP addresses, deployment-specific tuning, ~/.bashrc snippets.

**Why excluded:**
- Not portable to another server
- Successor may have different environment
- Clutters the institutional record with transient details

**Preserved instead:** Portable explanation (e.g., "local inference runs on port 11436" becomes "embeddings server listens on $EMBEDDING_PORT, defined in .env").

---

### 6. Transient Tool State

**What:** Checkpoint metadata, JSONL records with timestamps, workflow-tool-specific structures, checkpoint numbers.

**Why excluded:**
- Tool state is temporal (gstack format may change)
- Not readable in 50 years
- Source repo + git log are the canonical record

**Preserved instead:** High-level outcome (e.g., "completed Phase 3 backend," not "checkpoint 20260711-131810").

---

### 7. Unverified Hypotheses

**What:** Ideas explored but never validated, theories, brainstorms.

**Why excluded:**
- Founder Ruling 2026-07-11 (Resolution 8): "Nothing enters the Constitution without first maturing through research and repeated evidence"
- Premature hardening of speculation looks like institutional wisdom

**Preserved instead:** Validated patterns only; open questions get OPEN_QUESTIONS.md (explicitly marked as unresolved).

---

### 8. Duplicate Content

**What:** Information already committed to root DECISIONS.md, LESSONS.md, or codebase comments.

**Why excluded:**
- Reduces maintenance burden (one source of truth)
- Links have lower chance of diverging

**Preserved instead:** Cross-reference with "see also: commit XYZ, DECISIONS.md line YYY".

---

## What IS Preserved

### Content Type: Decision Records

**Format:**
```
Decision: [Brief title]
Date: YYYY-MM-DD
Context: [What problem or question drove this?]
Reasoning: [Why this choice?]
Alternatives Considered: [What we ruled out and why]
Evidence: [Concrete examples, metrics, or links]
Status: [Live | Deprecated | Under Review]
Governance: [Which principle, if any, governs this decision]
```

**Example:** Preserved (→ DECISIONS.md)

---

### Content Type: Incident Root Causes

**Format:**
```
Incident: [Title]
Date: YYYY-MM-DD
Symptoms: [What users/operators saw]
Root Cause: [What actually happened]
Resolution: [How we fixed it]
Prevention: [What rule or process prevents recurrence]
Post-Mortem Link: [Reference to incident post-mortem if detailed external review exists]
```

**Example:** Preserved (→ INCIDENTS.md)

---

### Content Type: Standing Constraints

**Format:**
```
Constraint: [Statement of the rule]
Since: [When we learned/adopted it]
Rationale: [Why is this true]
Violates: [What happens if you break this rule]
Example: [Concrete case where violation caused damage]
Current Status: [Actively enforced | Legacy | Planned removal]
```

**Example:** Preserved (→ STANDING_CONSTRAINTS.md)

---

### Content Type: Lessons Learned

**Format:**
```
Lesson: [What we discovered]
Evidence: [How we know this is true]
When: [Date first observed; dates of repeated occurrences]
Impact: [What harm if we ignore this]
Action: [How we prevent this going forward]
Governance: [STEWARDSHIP.md principle or DECISIONS.md it validates]
```

**Example:** Preserved (→ LESSONS.md)

---

### Content Type: Reference Pointers

**Format:**
```
Resource: [Name]
Location: [URL or path]
Purpose: [Why Daanaa needs this]
Maintained By: [Who owns it]
Reliability: [Stable | Evolving | Deprecated]
```

**Example:** Preserved as-is (→ OPEN_QUESTIONS.md references, or MEMORY_MANIFEST.md)

---

## Security Validation Before Git Commit

**Pre-commit scan:**
```bash
# Fail if any secret patterns found
grep -r -E '(AKIA|ghp_|Bearer|api_key|password|secret|token|credential|@gmail|ssh-rsa)' institution/ai-memory/ && exit 1

# Fail if any home paths with username
grep -r '/home/akbar/' institution/ai-memory/ | grep -v 'meritgiving' && exit 1

# Fail if any timestamps that look like vendor-specific artifact names
grep -r '[0-9]\{12\}-[0-9a-f]\{8\}' institution/ai-memory/ && exit 1
```

---

## Migration Integrity Check

**To run after migration completes:**

1. Verify each file in `institution/ai-memory/` has an author (date), source link, and governance reference
2. Spot-audit 10 random incidents: can a successor diagnose and prevent recurrence from the record?
3. Spot-audit 10 random decisions: can a successor understand *why* the system is designed this way?
4. Count: how many open questions exist? Are they actionable?
5. Security scan (above) passes with no findings

**Sign-off:** If all checks pass, migration is approved for git commit.

---

**Goal:** Institution/ai-memory/ should be readable, trustworthy, and durable. It should help successors become wiser, not just informed.
