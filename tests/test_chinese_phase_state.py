"""
Deterministic tests for scripts/chinese_phase_state.py.

No LLM is used to decide pass/fail anywhere in this file - every assertion is
a plain Python comparison against known inputs.
"""

import importlib.util
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "chinese_phase_state", REPO_ROOT / "scripts" / "chinese_phase_state.py"
)
cps = importlib.util.module_from_spec(SPEC)
sys.modules["chinese_phase_state"] = cps
SPEC.loader.exec_module(cps)


@pytest.fixture
def tmp_repo(tmp_path, monkeypatch):
    """Isolated fake repo layout so tests never touch the real repository."""
    plan_dir = tmp_path / ".claude" / "autonomous"
    plan_dir.mkdir(parents=True)
    plan = {
        "phase": "CHINESE_LAUNCH",
        "checkpoints": [
            {
                "week": 1,
                "date": "2026-08-16",
                "milestone": "Partnerships + Marketing Launch",
                "required_outcomes": ["2+ academic partnerships confirmed"],
            },
            {
                "week": 8,
                "date": "2026-01-01",  # deliberately in the past for BLOCKED test
                "milestone": "Phase 2 Complete",
                "required_outcomes": ["2+ academic partnerships confirmed"],
            },
        ],
    }
    plan_path = plan_dir / "CHINESE_PHASE_PLAN.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    db_path = tmp_path / "data" / "merit_registry.db"
    db_path.parent.mkdir(parents=True)
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE pilot_invitations (id TEXT, signup_completed BOOLEAN)"
    )
    conn.commit()
    conn.close()

    partnerships_dir = tmp_path / "docs" / "partnerships" / "chinese"
    papers_dir = tmp_path / "docs" / "papers"

    monkeypatch.setattr(cps, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(cps, "PLAN_PATH", plan_path)
    monkeypatch.setattr(cps, "DB_PATH", db_path)
    monkeypatch.setattr(cps, "OUTPUT_PATH", plan_dir / "chinese-phase-status.json")
    monkeypatch.setattr(cps, "PARTNERSHIPS_DIR", partnerships_dir)
    monkeypatch.setattr(cps, "PAPERS_DIR", papers_dir)
    monkeypatch.delenv("WECHAT_API_KEY", raising=False)
    monkeypatch.delenv("BILIBILI_API_KEY", raising=False)
    monkeypatch.delenv("ZHIHU_API_KEY", raising=False)

    return {
        "root": tmp_path,
        "db_path": db_path,
        "partnerships_dir": partnerships_dir,
        "papers_dir": papers_dir,
        "output_path": plan_dir / "chinese-phase-status.json",
    }


def test_missing_source_dirs_report_unknown_not_zero(tmp_repo):
    """A directory that doesn't exist at all is UNKNOWN, not a measured 0
    (Codex review 2026-08-10: absence of the source is not evidence it was
    checked and found empty)."""
    state = cps.generate()
    assert state["metrics"]["academic_partnerships"]["value"] is None
    assert state["metrics"]["academic_partnerships"]["status"] == "UNKNOWN"
    assert state["metrics"]["papers_submitted"]["value"] is None
    assert state["metrics"]["papers_submitted"]["status"] == "UNKNOWN"


def test_existing_empty_dir_reports_measured_zero(tmp_repo):
    """A directory that DOES exist with zero matching files is a genuine
    measured 0 - distinct from the absent-directory UNKNOWN case above."""
    tmp_repo["partnerships_dir"].mkdir(parents=True)
    state = cps.generate()
    assert state["metrics"]["academic_partnerships"]["value"] == 0
    assert state["metrics"]["academic_partnerships"]["status"] == "MEASURED"


def test_confirmed_partnership_file_is_counted(tmp_repo):
    tmp_repo["partnerships_dir"].mkdir(parents=True)
    (tmp_repo["partnerships_dir"] / "tsinghua.confirmed.md").write_text("ok")
    (tmp_repo["partnerships_dir"] / "hku.confirmed.md").write_text("ok")
    (tmp_repo["partnerships_dir"] / "draft-only.md").write_text("not counted")

    state = cps.generate()
    assert state["metrics"]["academic_partnerships"]["value"] == 2


def test_submitted_paper_requires_status_line(tmp_repo):
    tmp_repo["papers_dir"].mkdir(parents=True)
    submitted = tmp_repo["papers_dir"] / "chinese-phase-paper-1.md"
    submitted.write_text("STATUS: SUBMITTED\n\nbody")
    draft = tmp_repo["papers_dir"] / "chinese-phase-paper-2.md"
    draft.write_text("STATUS: DRAFT\n\nbody")

    state = cps.generate()
    assert state["metrics"]["papers_submitted"]["value"] == 1
    assert "chinese-phase-paper-1.md" in state["metrics"]["papers_submitted"]["files"]


def test_pilot_organizations_is_unknown_not_zero(tmp_repo):
    """The table exists and is readable (0 rows), but because it has no
    phase column, this metric must stay UNKNOWN, not be reported as 0."""
    state = cps.generate()
    assert state["metrics"]["pilot_organizations"]["status"] == "UNKNOWN"
    assert state["metrics"]["pilot_organizations"]["value"] is None
    assert "unattributed_total_all_phases" in state["metrics"]["pilot_organizations"]


def test_social_followers_unknown_without_credentials(tmp_repo):
    state = cps.generate()
    for metric in ("wechat_followers", "bilibili_subscribers", "zhihu_followers"):
        assert state["metrics"]["social_followers"][metric]["status"] == "UNKNOWN"
        assert state["metrics"]["social_followers"][metric]["value"] is None


def test_social_followers_still_unknown_with_credential_but_no_client(tmp_repo, monkeypatch):
    """A credential being present must not fabricate a follower count - there's
    still no API client implemented, so it must stay UNKNOWN."""
    monkeypatch.setenv("WECHAT_API_KEY", "fake-key-for-test")
    state = cps.generate()
    assert state["metrics"]["social_followers"]["wechat_followers"]["status"] == "UNKNOWN"
    assert state["metrics"]["social_followers"]["wechat_followers"]["value"] is None


def test_missing_database_fails_closed(tmp_repo):
    tmp_repo["db_path"].unlink()
    with pytest.raises(cps.SourceUnavailable):
        cps.generate()


def test_missing_plan_file_fails_closed(tmp_repo):
    cps.PLAN_PATH.unlink()
    with pytest.raises(cps.SourceUnavailable):
        cps.generate()


def test_failed_run_does_not_overwrite_previous_valid_state(tmp_repo, monkeypatch, capsys):
    """End-to-end via main(): a good run writes state; a subsequent broken run
    must leave that state file byte-for-byte untouched."""
    assert cps.main() == 0
    good_content = tmp_repo["output_path"].read_bytes()

    tmp_repo["db_path"].unlink()
    exit_code = cps.main()
    assert exit_code == 1

    assert tmp_repo["output_path"].read_bytes() == good_content
    assert "FAIL-CLOSED" in capsys.readouterr().err


def test_idempotent_across_repeated_runs(tmp_repo):
    state1 = cps.generate()
    state2 = cps.generate()
    state1.pop("generated_at")
    state2.pop("generated_at")
    assert state1 == state2


def test_checkpoints_never_compute_a_verdict(tmp_repo):
    """Codex review (2026-08-10): the generator must not compute
    ON_TRACK/OFF_TRACK/BLOCKED from partial requirement text-matching. Every
    checkpoint must report verdict NOT_EVALUATED regardless of how many
    metrics are measured, past-due, or fully unmeasured."""
    tmp_repo["partnerships_dir"].mkdir(parents=True)
    (tmp_repo["partnerships_dir"] / "tsinghua.confirmed.md").write_text("ok")
    (tmp_repo["partnerships_dir"] / "hku.confirmed.md").write_text("ok")

    state = cps.generate()
    for checkpoint in state["checkpoints"]:
        assert checkpoint["verdict"] == "NOT_EVALUATED"
        assert "verdict_reason" in checkpoint


def test_checkpoint_days_remaining_future(tmp_repo):
    """Week 1 (2026-08-16) is future relative to the fixture's clock context;
    days_remaining must be positive and computed from calendar dates."""
    state = cps.generate()
    week1 = next(c for c in state["checkpoints"] if c["week"] == 1)
    assert week1["days_remaining"] > 0


def test_checkpoint_days_remaining_past(tmp_repo):
    """Week 8 is deliberately dated in the past by the fixture."""
    state = cps.generate()
    week8 = next(c for c in state["checkpoints"] if c["week"] == 8)
    assert week8["days_remaining"] < 0


def test_checkpoint_days_remaining_is_calendar_date_boundary_safe(tmp_repo):
    """Codex review (2026-08-10): comparing timezone-aware datetimes at
    midnight UTC made a checkpoint appear past_due immediately after UTC
    midnight on its own stated date. Verify days_remaining == 0 on the exact
    checkpoint date regardless of time-of-day, using calendar-date math
    directly rather than the full generate() pipeline's now_utc.now() clock."""
    from datetime import date

    checkpoint = {"date": "2026-08-16", "week": 1, "milestone": "test"}
    today = date(2026, 8, 16)
    assert cps.checkpoint_days_remaining(checkpoint, today) == 0

    today_before = date(2026, 8, 15)
    assert cps.checkpoint_days_remaining(checkpoint, today_before) == 1

    today_after = date(2026, 8, 17)
    assert cps.checkpoint_days_remaining(checkpoint, today_after) == -1


def test_checkpoint_required_outcomes_preserved_as_facts(tmp_repo):
    """The plan's free-text required_outcomes must be passed through verbatim
    for a human/Claude to interpret later - not parsed or judged here."""
    state = cps.generate()
    week1 = next(c for c in state["checkpoints"] if c["week"] == 1)
    assert week1["required_outcomes"] == ["2+ academic partnerships confirmed"]


def test_no_writes_outside_output_path(tmp_repo):
    """Guard against accidental writes anywhere but the declared output file."""
    before = {p for p in tmp_repo["root"].rglob("*") if p.is_file()}
    cps.main()
    after = {p for p in tmp_repo["root"].rglob("*") if p.is_file()}
    new_files = after - before
    assert new_files == {tmp_repo["output_path"]}


def test_no_network_or_git_calls(monkeypatch, tmp_repo):
    """The module must not import subprocess/socket/requests-style network or
    git invocation machinery. Static guard on the module's own namespace."""
    forbidden = {"subprocess", "socket", "requests", "urllib", "git"}
    module_globals = set(vars(cps).keys())
    # only flag if imported as a top-level name (e.g. `import subprocess`)
    assert not (forbidden & module_globals), (
        f"chinese_phase_state.py imports forbidden modules: "
        f"{forbidden & module_globals}"
    )
