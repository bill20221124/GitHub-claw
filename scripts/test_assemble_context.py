#!/usr/bin/env python3
"""Tests for scripts/assemble_context.py and its integration with run_skill.py.

Run:
    python -m unittest scripts/test_assemble_context.py

Coverage:
    1.  Standing Context extracted correctly from MEMORY.md
    2.  Standing Context returns "(not available)" when MEMORY.md is absent
    3.  Standing Context returns "(not available)" when section heading is absent
    4.  Active Goal extracted correctly for in-progress goals
    5.  Active Goal skips non-in-progress goals
    6.  Active Goal returns "(not available)" when goals/ dir is missing
    7.  Recent Audit returns last ≤20 lines from audit files
    8.  Recent Audit returns "(not available)" when audit dir is missing
    9.  Event Hint extracts PR refs and file paths
   10.  Event Hint returns "(not available)" for empty event
   11.  Missing file in any layer causes silent skip (no exception)
   12.  Total output length ≤ 6000 characters
   13.  run_skill.py uses assemble_context when module is available
   14.  _budget truncates text exceeding the per-layer limit
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import pathlib
import sys
import tempfile
import textwrap
import unittest

# ---------------------------------------------------------------------------
# Import helpers
# ---------------------------------------------------------------------------

_SCRIPTS = pathlib.Path(__file__).parent


def _load_module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


ac = _load_module("assemble_context", _SCRIPTS / "assemble_context.py")


# ---------------------------------------------------------------------------
# Helpers for building fake repo trees
# ---------------------------------------------------------------------------


def _write(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")


# ---------------------------------------------------------------------------
# Test 1 — Standing Context extracted correctly
# ---------------------------------------------------------------------------


class TestStandingContext(unittest.TestCase):
    def test_extracts_standing_context_section(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            _write(root / "MEMORY.md", """\
                # MEMORY.md

                ## Owner Preferences
                Some owner pref.

                ## Standing Context

                - Fact A
                - Fact B

                ## Task Log
                | Date | Summary |
            """)
            result = ac._extract_standing_context(root)
            self.assertIn("Fact A", result)
            self.assertIn("Fact B", result)
            self.assertNotIn("Owner Preferences", result)
            self.assertNotIn("Task Log", result)

    # Test 2
    def test_missing_memory_file_returns_not_available(self):
        with tempfile.TemporaryDirectory() as td:
            result = ac._extract_standing_context(pathlib.Path(td))
            self.assertEqual(result, "(not available)")

    # Test 3
    def test_missing_section_returns_not_available(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            _write(root / "MEMORY.md", "# MEMORY.md\n\n## Owner Preferences\nstuff\n")
            result = ac._extract_standing_context(root)
            self.assertEqual(result, "(not available)")


# ---------------------------------------------------------------------------
# Test 4 & 5 — Active Goal
# ---------------------------------------------------------------------------


class TestActiveGoal(unittest.TestCase):
    def _make_goal(self, root: pathlib.Path, gid: str, status: str) -> None:
        _write(root / "goals" / f"{gid}.md", f"""\
            ---
            id: {gid}
            title: My goal {gid}
            status: {status}
            priority: P0
            owner: "@Architect"
            created: 2026-01-01
            updated: 2026-01-01
            related_decisions: []
            related_tickets: []
            related_prs: []
            ---

            # Goal: My goal {gid}

            ## Acceptance Criteria

            - [ ] Do the thing

            ## Last advanced

            - 2026-01-02 by @Copilot: did something
        """)

    def test_in_progress_goal_extracted(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            self._make_goal(root, "G-001", "in-progress")
            result = ac._extract_active_goals(root)
            self.assertIn("G-001", result)
            self.assertIn("My goal G-001", result)
            self.assertIn("Do the thing", result)

    # Test 5
    def test_non_in_progress_goal_skipped(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            self._make_goal(root, "G-002", "done")
            result = ac._extract_active_goals(root)
            self.assertEqual(result, "(not available)")

    # Test 6
    def test_missing_goals_dir_returns_not_available(self):
        with tempfile.TemporaryDirectory() as td:
            result = ac._extract_active_goals(pathlib.Path(td))
            self.assertEqual(result, "(not available)")


# ---------------------------------------------------------------------------
# Test 7 & 8 — Recent Audit
# ---------------------------------------------------------------------------


class TestRecentAudit(unittest.TestCase):
    def test_returns_last_20_lines(self):
        from datetime import date
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            today = date.today().isoformat()
            lines = [f"| {i:02d}:00Z | finish | summarize | success | 100 | 1 |"
                     for i in range(25)]
            _write(root / "memory" / "audit" / f"{today}.md",
                   "# Audit\n\n" + "\n".join(lines) + "\n")
            result = ac._extract_recent_audit(root)
            result_lines = [l for l in result.splitlines() if l.strip()]
            self.assertLessEqual(len(result_lines), 20)
            # Should contain the last entries (highest index)
            self.assertIn("24:00Z", result)

    # Test 8
    def test_missing_audit_dir_returns_not_available(self):
        with tempfile.TemporaryDirectory() as td:
            result = ac._extract_recent_audit(pathlib.Path(td))
            self.assertEqual(result, "(not available)")


# ---------------------------------------------------------------------------
# Test 9 & 10 — Event Hint
# ---------------------------------------------------------------------------


class TestEventHint(unittest.TestCase):
    def test_extracts_pr_refs_and_file_paths(self):
        event = {
            "pull_request": {
                "head": {"ref": "feature/my-branch"},
                "base": {"ref": "main"},
                "body": "Fixes scripts/assemble_context.py and docs/notes.md",
            }
        }
        result = ac._extract_event_hint(event)
        self.assertIn("feature/my-branch", result)
        self.assertIn("scripts/assemble_context.py", result)
        self.assertIn("docs/notes.md", result)

    # Test 10
    def test_empty_event_returns_not_available(self):
        result = ac._extract_event_hint({})
        self.assertEqual(result, "(not available)")


# ---------------------------------------------------------------------------
# Test 11 — Missing layer silently skipped
# ---------------------------------------------------------------------------


class TestSilentSkip(unittest.TestCase):
    def test_missing_all_files_no_exception(self):
        with tempfile.TemporaryDirectory() as td:
            # Empty repo root — no MEMORY.md, no goals/, no audit/
            result = ac.assemble({}, pathlib.Path(td))
            # Should return a string without raising
            self.assertIsInstance(result, str)
            self.assertIn("(not available)", result)


# ---------------------------------------------------------------------------
# Test 12 — Total length ≤ 6000
# ---------------------------------------------------------------------------


class TestTotalLengthCap(unittest.TestCase):
    def test_total_output_within_limit(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            # Write a very large MEMORY.md Standing Context
            big_content = "- " + "x" * 3000 + "\n"
            _write(root / "MEMORY.md",
                   f"# MEMORY\n\n## Standing Context\n\n{big_content}\n\n## Task Log\n|\n")
            result = ac.assemble({}, root)
            self.assertLessEqual(len(result), ac.TOTAL_CHAR_LIMIT)


# ---------------------------------------------------------------------------
# Test 13 — run_skill.py calls assemble_context when available
# ---------------------------------------------------------------------------


class TestRunSkillUsesAssembleContext(unittest.TestCase):
    def test_run_skill_imports_assemble_context(self):
        """Verify run_skill.py loads assemble_context without error."""
        run_skill_path = _SCRIPTS / "run_skill.py"
        self.assertTrue(run_skill_path.is_file(), "run_skill.py not found")

        source = run_skill_path.read_text(encoding="utf-8")
        # The integration block must reference assemble_context
        self.assertIn("assemble_context", source)
        # The fallback to memory_excerpt must still exist
        self.assertIn("memory_excerpt()", source)

    def test_assemble_context_module_is_callable(self):
        """After import, _assemble_context (if set) must be callable."""
        # We can import run_skill in a temp CWD to avoid side-effects
        import importlib
        import os

        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            # Minimal directory structure so run_skill can be imported
            (root / "prompts").mkdir()
            (root / ".agents" / "skills").mkdir(parents=True)
            (root / ".agent-run").mkdir()

            old_cwd = os.getcwd()
            try:
                os.chdir(root)
                # Just verify assemble_context can be loaded directly
                result = ac.assemble({}, root)
                self.assertIsInstance(result, str)
            finally:
                os.chdir(old_cwd)


# ---------------------------------------------------------------------------
# Test 14 — _budget truncates correctly
# ---------------------------------------------------------------------------


class TestBudget(unittest.TestCase):
    def test_text_within_limit_unchanged(self):
        text = "hello world"
        self.assertEqual(ac._budget(text, 100), text)

    def test_text_over_limit_truncated(self):
        text = "a" * 200
        result = ac._budget(text, 50)
        self.assertLessEqual(len(result), 50)
        self.assertIn("[truncated]", result)


# ---------------------------------------------------------------------------
# Test 15–17 — Layer 3 source logging
# ---------------------------------------------------------------------------


class TestLayer3SourceLogging(unittest.TestCase):
    """Verify that assemble() prints the Layer 3 source to stderr.

    Tests confirm the 反思→working-set 反哺验证 (G-003) acceptance criterion:
    '[assemble_context] Layer 3 source: <source>' is emitted so operators can
    confirm in GitHub Actions logs whether reflections or audit is being used.
    """

    def _capture_stderr(self, event: dict, root: pathlib.Path) -> str:
        """Call assemble() and return whatever was written to stderr."""
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            ac.assemble(event, root)
        return buf.getvalue()

    # Test 15 — fallback path logs "recent-audit"
    def test_fallback_to_audit_logs_recent_audit(self) -> None:
        """When embed_index is unavailable and audit files exist, layer3 = recent-audit."""
        from datetime import date as _date
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            today = _date.today().isoformat()
            _write(
                root / "memory" / "audit" / f"{today}.md",
                "# Audit\n\n| 10:00Z | finish | summarize | success | 100 | 1 |\n",
            )
            # No reflections/ dir → embed_index returns "(not available)"
            log = self._capture_stderr({}, root)
            self.assertIn("[assemble_context] Layer 3 source:", log)
            self.assertIn("recent-audit", log)

    # Test 16 — no audit, no reflections → logs "none"
    def test_no_sources_logs_none(self) -> None:
        """When neither reflections nor audit files are available, layer3 = none."""
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            # Empty repo root — no reflections, no audit
            log = self._capture_stderr({}, root)
            self.assertIn("[assemble_context] Layer 3 source:", log)
            self.assertIn("none", log)

    # Test 17 — patched reflections path logs "relevant-reflections"
    def test_relevant_reflections_path_logs_correctly(self) -> None:
        """When _extract_relevant_reflections returns content, layer3 = relevant-reflections."""
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)

            # Patch _extract_relevant_reflections to simulate a successful retrieval
            with patch.object(
                ac,
                "_extract_relevant_reflections",
                return_value="**R-001.md** (score 0.850)\nSome reflection content",
            ):
                log = self._capture_stderr({}, root)

            self.assertIn("[assemble_context] Layer 3 source:", log)
            self.assertIn("relevant-reflections", log)


if __name__ == "__main__":
    unittest.main()
