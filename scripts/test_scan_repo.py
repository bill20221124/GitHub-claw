#!/usr/bin/env python3
"""Unit tests for scripts/scan_repo.py — T-005

Run with:
    python -m unittest scripts/test_scan_repo.py

Coverage requirements (T-005 spec):
    - watchlist.yml reading correct (enabled filtering)
    - stale-goals: in-progress + overdue → finding; done → skip
    - missing-reflections: ticket count > R count → finding; equal → pass
    - open-questions: open Q → finding; none → pass
    - audit-overrun: over threshold → finding; under → pass
    - missing files silently skipped (no crash)
    - exit 0 / exit 1 behaviour correct
"""

from __future__ import annotations

import pathlib
import sys
import tempfile
import textwrap
import unittest
from datetime import date, timedelta

# Make sure the scripts directory is importable
_SCRIPTS_DIR = pathlib.Path(__file__).parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from scan_repo import (  # noqa: E402
    _count_archived_tickets,
    _count_reflection_files,
    _parse_last_advanced_date,
    _parse_questions_section,
    _read_daily_budget,
    _sum_audit_tokens,
    build_report,
    check_audit_overrun,
    check_missing_reflections,
    check_open_questions,
    check_stale_goals,
    load_watchlist,
    main,
    run_checks,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")


def _make_goal(root: pathlib.Path, name: str, status: str, last_advanced_date: str | None) -> None:
    """Create a minimal G-NNN.md under root/goals/."""
    la_section = ""
    if last_advanced_date:
        la_section = f"\n## Last advanced\n\n- {last_advanced_date} by @Copilot: some work\n"
    else:
        la_section = "\n## Last advanced\n\n(none)\n"
    content = f"""\
---
id: {name}
title: Test Goal {name}
status: {status}
priority: P0
owner: "@Architect"
created: 2026-01-01
updated: 2026-01-01
---

# Goal: {name}
{la_section}
"""
    _write(root / "goals" / f"{name}.md", content)


# ---------------------------------------------------------------------------
# Test: load_watchlist
# ---------------------------------------------------------------------------


class TestLoadWatchlist(unittest.TestCase):
    def test_load_returns_enabled_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            wl_path = pathlib.Path(tmpdir) / "watchlist.yml"
            _write(
                wl_path,
                """\
                checks:
                  stale-goals:
                    id: stale-goals
                    enabled: true
                    threshold_days: 7
                    description: "stale goals check"
                  disabled-check:
                    id: disabled-check
                    enabled: false
                    description: "disabled"
                """,
            )
            wl = load_watchlist(wl_path)
            self.assertIn("stale-goals", wl)
            self.assertIn("disabled-check", wl)
            self.assertTrue(wl["stale-goals"]["enabled"])
            self.assertFalse(wl["disabled-check"]["enabled"])

    def test_missing_file_returns_empty(self) -> None:
        wl = load_watchlist(pathlib.Path("/nonexistent/watchlist.yml"))
        self.assertEqual(wl, {})

    def test_enabled_filter_in_run_checks(self) -> None:
        """run_checks skips disabled entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            watchlist = {
                "stale-goals": {"enabled": False, "threshold_days": 7},
            }
            results = run_checks(watchlist, root)
            # disabled check should not appear in results
            self.assertNotIn("stale-goals", results)


# ---------------------------------------------------------------------------
# Test: stale-goals
# ---------------------------------------------------------------------------


class TestStaleGoals(unittest.TestCase):
    def test_inprogress_overdue_is_finding(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            old_date = (date.today() - timedelta(days=10)).isoformat()
            _make_goal(root, "G-001", "in-progress", old_date)
            findings = check_stale_goals({"threshold_days": 7}, root)
            self.assertEqual(len(findings), 1)
            self.assertIn("G-001.md", findings[0])

    def test_inprogress_recent_is_not_finding(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            recent_date = (date.today() - timedelta(days=3)).isoformat()
            _make_goal(root, "G-001", "in-progress", recent_date)
            findings = check_stale_goals({"threshold_days": 7}, root)
            self.assertEqual(len(findings), 0)

    def test_done_status_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            old_date = (date.today() - timedelta(days=30)).isoformat()
            _make_goal(root, "G-001", "done", old_date)
            findings = check_stale_goals({"threshold_days": 7}, root)
            self.assertEqual(len(findings), 0)

    def test_missing_goals_dir_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            # no goals/ dir
            findings = check_stale_goals({"threshold_days": 7}, root)
            self.assertEqual(findings, [])


# ---------------------------------------------------------------------------
# Test: missing-reflections
# ---------------------------------------------------------------------------


class TestMissingReflections(unittest.TestCase):
    def _make_collab(self, root: pathlib.Path, ticket_count: int) -> None:
        """Create a fake AGENT-COLLAB.md with ticket_count archived tickets."""
        rows = "".join(
            f"| T-{i:03d} | Title {i} | G-001 | — |\n" for i in range(1, ticket_count + 1)
        )
        content = f"""\
# AGENT-COLLAB.md

## 9. Archived Tickets

| Ticket | Title | Goal | PR |
|---|---|---|---|
{rows}
"""
        _write(root / "AGENT-COLLAB.md", content)

    def _make_reflections(self, root: pathlib.Path, count: int) -> None:
        reflections_dir = root / "reflections"
        reflections_dir.mkdir(parents=True, exist_ok=True)
        for i in range(1, count + 1):
            _write(reflections_dir / f"R-{i:03d}.md", f"# Reflection R-{i:03d}\n")

    def test_more_tickets_than_reflections_is_finding(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            self._make_collab(root, 3)
            self._make_reflections(root, 1)
            findings = check_missing_reflections({}, root)
            self.assertEqual(len(findings), 1)
            self.assertIn("missing", findings[0])

    def test_equal_counts_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            self._make_collab(root, 2)
            self._make_reflections(root, 2)
            findings = check_missing_reflections({}, root)
            self.assertEqual(len(findings), 0)

    def test_missing_collab_file_skips_silently(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            self._make_reflections(root, 2)
            findings = check_missing_reflections({}, root)
            self.assertEqual(len(findings), 0)


# ---------------------------------------------------------------------------
# Test: open-questions
# ---------------------------------------------------------------------------


class TestOpenQuestions(unittest.TestCase):
    def _make_collab_with_questions(
        self, root: pathlib.Path, questions: list[tuple[str, str, str]]
    ) -> None:
        """questions: list of (id, date_str, status)."""
        rows = "".join(
            f"| {q[0]} | {q[1]} | Question text | @A | @B | {q[2]} |\n"
            for q in questions
        )
        content = f"""\
# AGENT-COLLAB.md

## 5. Open Questions

| ID | 提出时间 | 问题 | 提问者 | 待答者 | 状态 |
|---|---|---|---|---|---|
{rows}
"""
        _write(root / "AGENT-COLLAB.md", content)

    def test_open_old_question_is_finding(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            old = (date.today() - timedelta(days=10)).isoformat()
            self._make_collab_with_questions(root, [("Q-001", old, "open")])
            findings = check_open_questions({"threshold_days": 7}, root)
            self.assertEqual(len(findings), 1)
            self.assertIn("Q-001", findings[0])

    def test_open_recent_question_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            recent = (date.today() - timedelta(days=3)).isoformat()
            self._make_collab_with_questions(root, [("Q-001", recent, "open")])
            findings = check_open_questions({"threshold_days": 7}, root)
            self.assertEqual(len(findings), 0)

    def test_answered_question_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            old = (date.today() - timedelta(days=30)).isoformat()
            self._make_collab_with_questions(root, [("Q-001", old, "answered")])
            findings = check_open_questions({"threshold_days": 7}, root)
            self.assertEqual(len(findings), 0)

    def test_missing_collab_file_skips_silently(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            findings = check_open_questions({"threshold_days": 7}, root)
            self.assertEqual(len(findings), 0)


# ---------------------------------------------------------------------------
# Test: audit-overrun
# ---------------------------------------------------------------------------


class TestAuditOverrun(unittest.TestCase):
    def _make_budget(self, root: pathlib.Path, daily_tokens: int) -> None:
        _write(
            root / "policies" / "budget.md",
            f"daily_tokens: {daily_tokens}\n",
        )

    def _make_audit(self, root: pathlib.Path, token_rows: list[int]) -> None:
        today_str = date.today().isoformat()
        header = "| Time | Phase | Skill | Status | Tokens | Run |\n|---|---|---|---|---|---|\n"
        rows = "".join(
            f"| 2026-04-29T10:00Z | finish | summarize | success | {t} | 123 |\n"
            for t in token_rows
        )
        _write(root / "memory" / "audit" / f"{today_str}.md", header + rows)

    def test_over_threshold_is_finding(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            self._make_budget(root, 200000)
            self._make_audit(root, [170000])  # 85% > 80% threshold
            findings = check_audit_overrun({"threshold_pct": 80}, root)
            self.assertEqual(len(findings), 1)
            self.assertIn("170,000", findings[0])

    def test_under_threshold_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            self._make_budget(root, 200000)
            self._make_audit(root, [100000])  # 50% < 80%
            findings = check_audit_overrun({"threshold_pct": 80}, root)
            self.assertEqual(len(findings), 0)

    def test_missing_budget_file_skips_silently(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            self._make_audit(root, [999999])
            findings = check_audit_overrun({"threshold_pct": 80}, root)
            self.assertEqual(len(findings), 0)

    def test_missing_audit_file_treated_as_zero_usage(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            self._make_budget(root, 200000)
            # no audit file created
            findings = check_audit_overrun({"threshold_pct": 80}, root)
            self.assertEqual(len(findings), 0)


# ---------------------------------------------------------------------------
# Test: exit codes (main)
# ---------------------------------------------------------------------------


class TestExitCodes(unittest.TestCase):
    def test_exit_0_when_all_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            wl_path = root / "watchlist.yml"
            _write(
                wl_path,
                """\
                checks:
                  stale-goals:
                    id: stale-goals
                    enabled: true
                    threshold_days: 7
                    description: "stale"
                """,
            )
            # goals dir exists but is empty → no findings
            (root / "goals").mkdir()
            code = main(["--watchlist", str(wl_path), "--repo-root", str(root)])
            self.assertEqual(code, 0)

    def test_exit_1_when_finding_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            wl_path = root / "watchlist.yml"
            _write(
                wl_path,
                """\
                checks:
                  stale-goals:
                    id: stale-goals
                    enabled: true
                    threshold_days: 7
                    description: "stale"
                """,
            )
            old_date = (date.today() - timedelta(days=15)).isoformat()
            _make_goal(root, "G-001", "in-progress", old_date)
            code = main(["--watchlist", str(wl_path), "--repo-root", str(root)])
            self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
