# T-2026-07-10-001 Frontend Lint Gate

## Document Control

| Field | Value |
|---|---|
| Purpose | Record ownership, scope, validation, and handoff for the first low-risk operating-loop improvement. |
| Responsible role | Stewardship Systems Agent. |
| Authority level | Task record subordinate to `HANDOFF_PROTOCOL.md` and `AUTHORITY.md`. |
| Review trigger | Reopened frontend lint failure or follow-up lint debt work. |
| Editable status | Editable by ordinary agents with append-only history for material updates. |
| Dependencies | `institution/HANDOFF_PROTOCOL.md`, `institution/DECISION_LOG.md`, `frontend/eslint.config.js`. |
| Retirement condition | Retire when superseded by a later task that absorbs this lint-gate scope. |

- Identifier: T-2026-07-10-001
- Date opened: 2026-07-10
- Owner: Codex stewardship layer
- Scope: Restore a working frontend lint command without changing runtime product behavior.
- Affected paths: `frontend/eslint.config.js`
- Higher-authority constraints checked: preserve product behavior; no spending; no deployment; no protected-principle change.
- Status: completed
- Validation plan: `npm run lint`, `npm test -- --runInBand wallet.crypto PassphraseModal WalletContext --no-coverage`, `npm run build`
- Review notes: lint now passes with warnings; warning backlog remains visible and should be addressed by later product-quality work, not hidden.
- Handoff target: Claude Code or product engineering owner for future warning reduction.
- Merge or close-out note: config-only repair completed locally; runtime behavior cross-checked with targeted tests and frontend build.
