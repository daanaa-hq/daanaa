"""Governance registry and conservative authority resolution."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .models import Contradiction, GovernanceDocument


REQUIRED = (
    "CLAUDE.md", "STEWARDSHIP.md", "PRIVACY-INVARIANTS.md", "DECISIONS.md",
    "LESSONS.md", "institution/README.md", "institution/CONSTITUTION.md",
    "institution/AUTHORITY.md", "institution/CURRENT_STATE.md", "institution/state.json",
)


@dataclass(frozen=True)
class GovernanceStatus:
    restricted: bool
    missing: tuple[str, ...]
    contradictions: tuple[Contradiction, ...]
    reason: str


class GovernanceRegistry:
    def __init__(self, root: Path, required: Iterable[str] = REQUIRED) -> None:
        self.root = root
        self.required = tuple(required)

    def inventory(self) -> tuple[GovernanceDocument, ...]:
        docs = []
        for rank, path in enumerate(self.required):
            absolute = self.root / path
            exists = absolute.is_file()
            digest = hashlib.sha256(absolute.read_bytes()).hexdigest() if exists else ""
            docs.append(GovernanceDocument(path, rank, digest, exists, "required"))
        return tuple(docs)

    def status(self) -> GovernanceStatus:
        inventory = self.inventory()
        missing = tuple(doc.path for doc in inventory if not doc.exists)
        contradictions: list[Contradiction] = []
        # The private authority name was requested by the operator but is not a
        # filesystem dependency of the product. Keep the discrepancy explicit.
        private_path = self.root.parent / "daanaa-hq"
        if not private_path.exists():
            contradictions.append(Contradiction(
                "authoritative_repository_provenance",
                ("operator_request", str(private_path)),
                "Requested private daanaa-hq repository is not present locally; in-repo authority remains the verified source.",
            ))
        restricted = bool(missing)
        reason = "required governance documents are missing" if missing else "required governance documents present"
        if contradictions:
            reason += "; provenance discrepancy recorded"
        return GovernanceStatus(restricted, missing, tuple(contradictions), reason)

    def resolve(self, subject: str, candidates: dict[str, str]) -> str | None:
        """Resolve by explicit authority order; refuse ties rather than guessing."""
        if not candidates:
            return None
        ranked = {doc.path: doc.authority_rank for doc in self.inventory()}
        ordered = sorted(candidates, key=lambda path: ranked.get(path, 10_000))
        winner = ordered[0]
        tied = [path for path in ordered if ranked.get(path, 10_000) == ranked.get(winner, 10_000)]
        if len(tied) > 1 and len({candidates[path] for path in tied}) > 1:
            raise ValueError(f"unresolved governance contradiction for {subject}: {tied}")
        return candidates[winner]
