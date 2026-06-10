# PHASE 1 — Backend Security + Mission (daanaa_api.py, api/main.py) — 2026-06-09

## Verdict: solid foundation, two HIGH auth issues, mission constraints clean on the live API.

## What's clean (verified, not assumed)
- **SQL injection:** all f-string SQL interpolations are whitelist-guarded
  (`allowed_sorts` at :744, `_VALID_SOURCES/_VALID_STATUSES` waitlist filters, hardcoded
  `cols`, `?` placeholder lists). User values always travel via params. No injection path found.
- **Mission — no revenue-default ranking:** `/api/organizations` defaults to
  `merit_score desc` (:745-747); `total_revenue` is an explicit opt-in sort. Search ranks by
  bm25/semantic fusion. ✔ principle upheld on the live API.
- **Claude API boundary:** zero anthropic imports in the API itself. Claude scripts
  (generate_missions_haiku.py, enrich_cause_tags_claude.py) SELECT only public registry
  fields (EIN, name, NTEE, city, state, mission); no waitlist/feedback/claims/email
  tables referenced. ✔ public-data-only boundary holds.
- **Auth hygiene:** `hmac.compare_digest` on all secret comparisons (8 sites); admin key
  fails closed when unset (:334); claim PIN wrapped in HMAC token so PIN never in URLs.
- **Hardening:** CORS restricted to 12 known origins (:232), Flask-Limiter with per-route
  limits (default 200/min), `debug=False`, real-IP keying behind Cloudflare.

## Findings

### HIGH
1. **RESEARCH_PASSCODE hardcoded fallback** — `daanaa_api.py:2322`
   `RESEARCH_PASSCODE = os.getenv('RESEARCH_PASSCODE', 'daanaa2026')  # Hardcoded for testing`.
   A working passcode is in source. Fix: fail closed — disable research routes if env unset.
2. **Research auth exempt from rate limiting** — `daanaa_api.py:2352`
   `/api/research/auth` is `@limiter.exempt` → unlimited passcode brute force, which makes
   finding #1 trivially exploitable. Fix: remove exempt, add `@limiter.limit("5 per minute")`.

### MED
3. **Claim secret dev fallback** — `daanaa_api.py:312-315` — `_CLAIM_SECRET` silently falls
   back to `"daanaa-dev-claim-secret"` if both env vars missing → forgeable claim-verify
   tokens. Fix: raise at startup when `DAANAA_PROD` set and no secret provided.
4. **Dormant revenue-DESC endpoints** — `api/main.py:90,114` — `/ntee` and `/search` ORDER BY
   total_revenue DESC (mission violation) but the FastAPI app is **not running** (verified
   via ps). Latent, not live. Fix: archive api/main.py or change sort before any deploy.

### LOW
5. **Raw exception text in responses** — `daanaa_api.py:1537` returns `str(e)` in a 500
   (also :1938, truncated). Fix: generic message to client, full detail to log.
6. **Unguarded int() casts** — 5 sites (:1590, :1683, :1684, :2071, :2098) — `?limit=abc`
   raises ValueError → bare 500. Fix: small `_int_arg(name, default, max)` helper.
7. **Bind 0.0.0.0** — `restart_api.sh:22` — deliberate (LAN access at 192.168.1.73 + Cloudflare
   Tunnel), but no `@app.errorhandler` and full LAN exposure means the firewall is the only
   guard. Document the assumption; consider ufw allowlist.

## Not checked here (deferred)
- IP retention in gunicorn access log format → Phase 5 (privacy invariant 3).
- Embedding-call timeout → Phase 4.
