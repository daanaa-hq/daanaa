#!/bin/bash
#
# privacy_check.sh — Stewardship-aligned security gate (pre-commit hook)
#
# Enforces Principle #2 (Privacy is structural) + Principle #3 (Evidence-based):
# - No credentials in code (API keys, tokens, passwords)
# - No log statements that leak private data
# - No env var fallbacks to hardcoded secrets
# - No clipboard exfiltration or shell injection vectors
# - No unverified claims mixed with public data
#
# Bind to git pre-commit hook:
#   ln -s ../../privacy_check.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
#
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
STAGED_FILES=$(git diff --cached --name-only)

VIOLATIONS=0

die() {
  echo "🚨 PRIVACY CHECK FAILED: $*" >&2
  exit 1
}

warn() {
  echo "⚠️  WARNING: $*" >&2
  VIOLATIONS=$((VIOLATIONS + 1))
}

pass() {
  echo "✓ $*"
}

# Excluded patterns (temporary allow-lists, must be documented)
EXCLUDE_PATTERNS=(
  "docs/"
  "archive/"
  ".git/"
  "node_modules/"
  "venv/"
  "__pycache__/"
  ".pytest_cache/"
  ".json"
  "privacy_check.sh"
  "CLAUDE.md"
  "README"
  ".md"
)

exclude_filter() {
  local file="$1"
  local pattern   # MUST be local: unscoped, this clobbered each GATE's $pattern
  for pattern in "${EXCLUDE_PATTERNS[@]}"; do
    if [[ "$file" == *"$pattern"* ]]; then
      return 0  # Excluded
    fi
  done
  return 1  # Not excluded
}

# Emit ONLY the lines this commit adds to a file (staged diff, '+' lines minus
# the '+++' header). A pre-commit gate should judge what the commit introduces,
# not re-scan pre-existing content on every touch — scanning whole files via
# `git show ":$file"` produced ~130 false positives on benign UI .tsx content
# (2026-06-22). Detection strength on introduced secrets is unchanged.
staged_added_lines() {
  git diff --cached --no-color -- "$1" 2>/dev/null | grep -E '^\+' | grep -vE '^\+\+\+'
}

echo "Running Stewardship-aligned privacy checks..."

# ============================================================
# GATE 1: Token-Shaped Credentials
# ============================================================
# AWS Access Key, GitHub Personal, OpenAI Secret, Google API, etc.
echo ""
echo "GATE 1: Token Pattern Detection"

TOKEN_PATTERNS=(
  'AKIA[0-9A-Z]\{16\}'
  'ghp_[a-zA-Z0-9_]\{36\}'
  'ghu_[a-zA-Z0-9_]\{36\}'
  'ghs_[a-zA-Z0-9_]\{36\}'
  'gho_[a-zA-Z0-9_]\{36\}'
  'sk-[a-zA-Z0-9]\{20,\}'
  'AIza[0-9A-Za-z_-]\{35\}'
  'ASIAR[0-9A-Z]\{16\}'
)

for pattern in "${TOKEN_PATTERNS[@]}"; do
  while IFS= read -r file; do
    if exclude_filter "$file"; then continue; fi

    added="$(staged_added_lines "$file" || true)"
    if [ -n "$added" ] && grep -q "$pattern" <<< "$added"; then
      warn "Token pattern detected in $file"
      VIOLATIONS=$((VIOLATIONS + 1))
    fi
  done <<< "$STAGED_FILES"
done

if [ $VIOLATIONS -eq 0 ]; then
  pass "No token patterns detected"
fi

# ============================================================
# GATE 2: Log/Print Leakage
# ============================================================
# print(password), console.log(token), log(api_key), etc.
echo ""
echo "GATE 2: Log Leakage Detection"

LEAKAGE_PATTERNS=(
  'print\s*\([^)]*\b(password|token|secret|key|api_key|apikey|auth|bearer|credential)\b'
  'console\.log\s*\([^)]*\b(password|token|secret|key|api_key|apikey|auth|bearer|credential)\b'
  'logger\.(debug|info|warn|error)\s*\([^)]*\b(password|token|secret|key|api_key|apikey|auth|bearer|credential)\b'
  'log\s*\([^)]*\b(password|token|secret|key|api_key|apikey|auth|bearer|credential)\b'
  'logging\.(debug|info|warn|error)\s*\([^)]*\b(password|token|secret|key|api_key|apikey|auth|bearer|credential)\b'
)

LEAKAGE_VIOLATIONS=0
for pattern in "${LEAKAGE_PATTERNS[@]}"; do
  while IFS= read -r file; do
    if exclude_filter "$file"; then continue; fi
    if [[ ! "$file" =~ \.(py|js|ts|tsx|jsx)$ ]]; then continue; fi

    added="$(staged_added_lines "$file" || true)"
    if [ -n "$added" ] && grep -qiE "$pattern" <<< "$added"; then
      warn "Log leakage pattern detected in $file: $pattern"
      LEAKAGE_VIOLATIONS=$((LEAKAGE_VIOLATIONS + 1))
    fi
  done <<< "$STAGED_FILES"
done

if [ $LEAKAGE_VIOLATIONS -eq 0 ]; then
  pass "No log leakage detected"
else
  VIOLATIONS=$((VIOLATIONS + LEAKAGE_VIOLATIONS))
fi

# ============================================================
# GATE 3: Env Var Fallbacks to Hardcoded Secrets
# ============================================================
# getenv('KEY') or 'hardcoded_secret'
echo ""
echo "GATE 3: Env Var Fallback Detection"

FALLBACK_VIOLATIONS=0
while IFS= read -r file; do
  if exclude_filter "$file"; then continue; fi
  if [[ ! "$file" =~ \.(py|js|ts)$ ]]; then continue; fi

  if git show ":$file" 2>/dev/null | grep -qE "(getenv|process\.env|os\.environ)\s*\(['\"][^'\"]+['\"]\s*\)\s*(or|??|//)\s*['\"](.*)?['\"]\s*$"; then
    warn "Env var fallback to hardcoded value detected in $file"
    FALLBACK_VIOLATIONS=$((FALLBACK_VIOLATIONS + 1))
  fi
done <<< "$STAGED_FILES"

if [ $FALLBACK_VIOLATIONS -eq 0 ]; then
  pass "No env var fallbacks to hardcoded values"
else
  VIOLATIONS=$((VIOLATIONS + FALLBACK_VIOLATIONS))
fi

# ============================================================
# GATE 4: Clipboard Exfiltration / Shell Injection
# ============================================================
# pyperclip.copy(), xclip, writes to /tmp, system(user_input), etc.
echo ""
echo "GATE 4: Exfiltration & Injection Vector Detection"

EXFIL_PATTERNS=(
  'pyperclip\.(copy|paste)'
  'xclip|xsel'
  'os\.system\s*\('
  'subprocess\.(call|run|Popen)\s*\(\s*[^[]*[^[]'  # Unquoted system calls
  'shell\s*=\s*True'                                 # Dangerous shell=True
)

EXFIL_VIOLATIONS=0
for pattern in "${EXFIL_PATTERNS[@]}"; do
  while IFS= read -r file; do
    if exclude_filter "$file"; then continue; fi
    if [[ ! "$file" =~ \.(py|js|ts)$ ]]; then continue; fi

    if git show ":$file" 2>/dev/null | grep -qE "$pattern"; then
      warn "Exfiltration/injection vector '$pattern' found in $file"
      EXFIL_VIOLATIONS=$((EXFIL_VIOLATIONS + 1))
    fi
  done <<< "$STAGED_FILES"
done

if [ $EXFIL_VIOLATIONS -eq 0 ]; then
  pass "No exfiltration or injection vectors detected"
else
  VIOLATIONS=$((VIOLATIONS + EXFIL_VIOLATIONS))
fi

# ============================================================
# GATE 5: Unverified Claims Mixed with Public Data
# ============================================================
# Stewardship Principle #3: Evidence-based signals only
# Flag if self-reported data is mixed with IRS/public data without clear boundaries
echo ""
echo "GATE 5: Data Source Boundary Check"

# Look for new claim-related code that doesn't distinguish public vs claimed data
CLAIMS_VIOLATIONS=0
while IFS= read -r file; do
  if exclude_filter "$file"; then continue; fi
  if [[ ! "$file" =~ \.(py|js|ts|tsx)$ ]]; then continue; fi

  # Check for API responses that mix org (public) + claim (self-reported) without source markers
  if git show ":$file" 2>/dev/null | grep -qE 'return.*org.*claim|mission.*donate_url.*claim'; then
    if ! git show ":$file" 2>/dev/null | grep -qE 'source.*public|source.*claimed|verified.*public|verified.*claimed'; then
      warn "Data returned mixes public + claimed fields without source markers in $file"
      CLAIMS_VIOLATIONS=$((CLAIMS_VIOLATIONS + 1))
    fi
  fi
done <<< "$STAGED_FILES"

if [ $CLAIMS_VIOLATIONS -eq 0 ]; then
  pass "Public and claimed data boundaries are clear"
else
  VIOLATIONS=$((VIOLATIONS + CLAIMS_VIOLATIONS))
fi

# ============================================================
# GATE 6: .env and Secrets Files Not in Index
# ============================================================
echo ""
echo "GATE 6: Config File Safety"

SECRETS_VIOLATIONS=0

# Any staged .env* file is blocked, EXCEPT .env*.example templates (which must
# hold no real values). This catches .env.claim / .env.production / etc. by
# filename — the exact class that leaked on 2026-06-16 because the hook was not
# yet installed. Matching is on the basename, anchored, so paths like
# deploy/environment.md do not false-positive.
# Only added/modified (A/M) secret files are violations — deleting/untracking a
# secret file (D) is the desired remediation and must not be blocked.
while IFS=$'\t' read -r status staged; do
  case "$status" in D*) continue ;; esac
  base="$(basename "$staged")"
  case "$base" in
    *.example) continue ;;                 # templates allowed
    .env|.env.*)
      warn "Secret/config file '$staged' in staging area (.env* files must never be committed)"
      SECRETS_VIOLATIONS=$((SECRETS_VIOLATIONS + 1))
      ;;
  esac
done < <(git diff --cached --name-status)

# Non-.env secret file conventions
for pattern in 'secrets\.json' 'config/production\.' 'credentials\.' 'private_key'; do
  if git diff --cached --name-only | grep -qE "$pattern"; then
    warn "Secret/config file matching '$pattern' in staging area"
    SECRETS_VIOLATIONS=$((SECRETS_VIOLATIONS + 1))
  fi
done

if [ $SECRETS_VIOLATIONS -eq 0 ]; then
  pass "No secret/config files in staging"
else
  VIOLATIONS=$((VIOLATIONS + SECRETS_VIOLATIONS))
fi

# ============================================================
# GATE 7: Privacy-Invariants Compliance
# ============================================================
echo ""
echo "GATE 7: PRIVACY-INVARIANTS Compliance"

if [ -f "$REPO_ROOT/PRIVACY-INVARIANTS.md" ]; then
  # Check that any new wallet/claim code respects invariants
  INVARIANT_VIOLATIONS=0
  while IFS= read -r file; do
    if exclude_filter "$file"; then continue; fi
    if [[ "$file" =~ wallet|claim|private ]]; then
      # These are sensitive; log for human review
      echo "  ℹ️  Manual review needed: $file (wallet/claim/private code)"
    fi
  done <<< "$STAGED_FILES"
  pass "PRIVACY-INVARIANTS file exists (manual review flagged)"
else
  warn "PRIVACY-INVARIANTS.md not found"
  VIOLATIONS=$((VIOLATIONS + 1))
fi

# ============================================================
# GATE 8: Tier 2 Entity Firewall (Library Document 011)
# ============================================================
# Entrusted data (org_claims contact/behavioral fields, waitlist, wallet,
# feedback) may never feed prospecting/outreach/consulting code paths, and
# may never be sent to external AI services (local inference only).
echo ""
echo "GATE 8: Tier 2 Entity Firewall"

TIER2_VIOLATIONS=0

# Tier 2 stores and columns (keep in sync with institution/library/011_data_classification.md)
TIER2_REFS='org_claims|volunteer_contact_|donor_contact_|call_notes|rep_name|rep_title|contact_preference|wallet_analytics|waitlist|checkin_sent_at|nudge_sent_at'

# 8a: Prospecting/outreach/consulting-named code must not touch Tier 2 stores.
# Matched on filename — a file named for commercial outreach that reads
# entrusted data is exactly the drift this gate exists to stop.
while IFS= read -r file; do
  if exclude_filter "$file"; then continue; fi
  if [[ ! "$file" =~ \.(py|js|ts|tsx|sh)$ ]]; then continue; fi
  base="$(basename "$file")"
  if [[ "$base" =~ (prospect|outreach|marketing|leads|sales|ecomargins|consult|campaign) ]]; then
    if git show ":$file" 2>/dev/null | grep -qE "$TIER2_REFS"; then
      warn "Tier 2 firewall: '$file' (commercial-path filename) references entrusted data stores"
      TIER2_VIOLATIONS=$((TIER2_VIOLATIONS + 1))
    fi
  fi
done <<< "$STAGED_FILES"

# 8b: Tier 2 data must never flow to external AI services. Flag added lines
# that reference both a Tier 2 store and an external AI host. Local inference
# (localhost:11434/11436/11437) is the sanctioned path.
EXTERNAL_AI_HOSTS='api\.openai\.com|api\.anthropic\.com|generativelanguage\.googleapis|api\.mistral\.ai|api\.together\.xyz|api\.groq\.com|openrouter\.ai'
while IFS= read -r file; do
  if exclude_filter "$file"; then continue; fi
  if [[ ! "$file" =~ \.(py|js|ts|tsx)$ ]]; then continue; fi

  added="$(staged_added_lines "$file" || true)"
  if [ -n "$added" ] && grep -qE "$EXTERNAL_AI_HOSTS" <<< "$added" \
     && git show ":$file" 2>/dev/null | grep -qE "$TIER2_REFS"; then
    warn "Tier 2 firewall: '$file' touches entrusted data AND an external AI host (local inference only)"
    TIER2_VIOLATIONS=$((TIER2_VIOLATIONS + 1))
  fi
done <<< "$STAGED_FILES"

# 8c: Wallet data must not be sent to external APIs
# Flag any code that sends wallet bookmarks or giving intent outside localhost
while IFS= read -r file; do
  if exclude_filter "$file"; then continue; fi
  if [[ ! "$file" =~ \.(ts|tsx|py|js)$ ]]; then continue; fi

  if git show ":$file" 2>/dev/null | grep -qE "wallet|giving.*intent"; then
    # Check if it also has external fetch/API calls (not localhost)
    if git show ":$file" 2>/dev/null | grep -qE "fetch|axios|requests|http" | grep -v "localhost|127.0.0.1|/api/"; then
      # Warn if both wallet data and external API calls are present
      if git show ":$file" 2>/dev/null | grep -E "wallet|giving.*intent" | grep -qE "fetch|axios"; then
        warn "Tier 2 data flow: '$file' may send wallet data to external API (verify localhost-only)"
        TIER2_VIOLATIONS=$((TIER2_VIOLATIONS + 1))
      fi
    fi
  fi
done <<< "$STAGED_FILES"

# 8d: Sensitive org data (revenue, donor info) must not be logged publicly
# Flag console.log, print(), or warning() calls that reference sensitive fields
SENSITIVE_FIELDS='donate_url|revenue|donation|program_revenue|donor|contribution_amount'
while IFS= read -r file; do
  if exclude_filter "$file"; then continue; fi
  if [[ ! "$file" =~ \.(ts|tsx|py|js)$ ]]; then continue; fi

  added="$(staged_added_lines "$file" || true)"
  if [ -n "$added" ] && grep -qE "(console\.log|print\(|logger\.|log\()" <<< "$added"; then
    # Check if the same file references sensitive org data
    if git show ":$file" 2>/dev/null | grep -qE "$SENSITIVE_FIELDS"; then
      warn "Sensitive data logging: '$file' has logging calls and references sensitive org fields (verify no data leaks)"
      TIER2_VIOLATIONS=$((TIER2_VIOLATIONS + 1))
    fi
  fi
done <<< "$STAGED_FILES"

# 8e: Search endpoint must not track user identity
# Flag if /api/search accepts or logs user_id, session_id, or auth tokens
while IFS= read -r file; do
  if exclude_filter "$file"; then continue; fi
  if [[ "$file" =~ (search|api.*search) ]]; then
    if [[ ! "$file" =~ \.(py|js|ts)$ ]]; then continue; fi

    if git show ":$file" 2>/dev/null | grep -qE "user_id|session_id|auth.*token|Authorization|visitor_id"; then
      warn "Search tracking: '$file' (search endpoint) may track user identity (verify P2 compliance)"
      TIER2_VIOLATIONS=$((TIER2_VIOLATIONS + 1))
    fi
  fi
done <<< "$STAGED_FILES"

if [ $TIER2_VIOLATIONS -eq 0 ]; then
  pass "Tier 2 entity firewall intact (gates 8a-8e all pass)"
else
  VIOLATIONS=$((VIOLATIONS + TIER2_VIOLATIONS))
fi

# ============================================================
# SUMMARY
# ============================================================
echo ""
if [ $VIOLATIONS -gt 0 ]; then
  die "Found $VIOLATIONS privacy/security violation(s). Fix before committing."
else
  echo "✅ All privacy gates passed. Stewardship-aligned commit."
  exit 0
fi
