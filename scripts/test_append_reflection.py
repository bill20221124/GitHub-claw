#!/usr/bin/env python3
"""
Self-tests for scripts/append_reflection.py and the --reflect hook in run_skill.py.

Run with:
  python -m unittest scripts/test_append_reflection.py
  python scripts/test_append_reflection.py
"""

from __future__ import annotations

import io
import os
import pathlib
import re
import sys
import tempfile
import textwrap
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

# Allow running from repo root or from scripts/
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import append_reflection as ar

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SAMPLE_TEMPLATE = textwrap.dedent("""\
    ---
    id: R-NNN
    date: YYYY-MM-DDThh:mmZ
    author: "@Copilot"
    ticket: T-NNN
    goal: G-NNN
    skill: <skill-id>
    goal_met: yes | partial | no
    duration_minutes: 0
    memories_used: []
    memories_missing: []
    ---

    # Reflection R-NNN

    ## 1. Did the task meet its acceptance criteria?

    <placeholder>

    ## 2. Which memories did I rely on?

    - `<file-path>` — <one-liner>

    ## 3. What memory was missing?

    - <short-desc> → memory-write candidate

    ## 4. What would I change next time?

    - <improvement> → skill update
""")


def _make_reflections_dir(tmpdir: str, existing: dict[str, str] | None = None) -> pathlib.Path:
    """Create a temporary reflections dir with a _template.md and optional existing files."""
    d = pathlib.Path(tmpdir) / "reflections"
    d.mkdir()
    (d / "_template.md").write_text(_SAMPLE_TEMPLATE, encoding="utf-8")
    if existing:
        for name, content in existing.items():
            (d / name).write_text(content, encoding="utf-8")
    return d


def _read_reflection(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Tests: next_reflection_number
# ---------------------------------------------------------------------------

class TestNextReflectionNumber(unittest.TestCase):

    def test_empty_dir_returns_one(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            d = _make_reflections_dir(tmpdir)
            self.assertEqual(ar.next_reflection_number(d), 1)

    def test_increments_past_existing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            d = _make_reflections_dir(tmpdir, {"R-001.md": "x", "R-002.md": "y"})
            self.assertEqual(ar.next_reflection_number(d), 3)

    def test_ignores_non_reflection_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            d = _make_reflections_dir(tmpdir, {"_template.md": "t", "README.md": "r"})
            # Only _template.md and README.md, no R-NNN.md → should return 1
            self.assertEqual(ar.next_reflection_number(d), 1)


# ---------------------------------------------------------------------------
# Tests: find_existing_for_ticket
# ---------------------------------------------------------------------------

class TestFindExistingForTicket(unittest.TestCase):

    def test_returns_none_when_no_match(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            d = _make_reflections_dir(tmpdir)
            self.assertIsNone(ar.find_existing_for_ticket(d, "T-999"))

    def test_finds_matching_ticket(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            content = _SAMPLE_TEMPLATE.replace("ticket: T-NNN", "ticket: T-042")
            d = _make_reflections_dir(tmpdir, {"R-001.md": content})
            result = ar.find_existing_for_ticket(d, "T-042")
            self.assertIsNotNone(result)
            self.assertEqual(result.name, "R-001.md")  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Tests: build_reflection_text
# ---------------------------------------------------------------------------

class TestBuildReflectionText(unittest.TestCase):

    def _build(self, **kwargs):
        defaults = dict(
            template_text=_SAMPLE_TEMPLATE,
            reflection_id="R-005",
            ticket="T-002",
            goal="G-001",
            skill="summarize",
            outcome="yes",
            duration_minutes=30,
            author="@Copilot",
            date_str="2026-04-26T10:00Z",
        )
        defaults.update(kwargs)
        return ar.build_reflection_text(**defaults)

    def test_id_replaced_in_frontmatter(self):
        text = self._build()
        self.assertIn("id: R-005", text)
        self.assertNotIn("id: R-NNN", text)

    def test_heading_updated(self):
        text = self._build()
        self.assertIn("# Reflection R-005", text)
        self.assertNotIn("# Reflection R-NNN", text)

    def test_ticket_replaced(self):
        text = self._build(ticket="T-099")
        self.assertIn("ticket: T-099", text)

    def test_null_fields_written_as_null(self):
        text = self._build(ticket=None, goal=None, skill=None)
        self.assertIn("ticket: null", text)
        self.assertIn("goal: null", text)
        self.assertIn("skill: null", text)

    def test_outcome_written(self):
        text = self._build(outcome="partial")
        self.assertIn("goal_met: partial", text)


# ---------------------------------------------------------------------------
# Tests: create_reflection (integration — file is written)
# ---------------------------------------------------------------------------

class TestCreateReflection(unittest.TestCase):

    def test_file_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            d = _make_reflections_dir(tmpdir)
            out = ar.create_reflection(
                reflections_dir=d,
                ticket="T-002",
                goal="G-001",
                skill="summarize",
                outcome="yes",
                duration_minutes=20,
                author="@Copilot",
            )
            self.assertTrue(out.is_file())
            self.assertEqual(out.name, "R-001.md")

    def test_numbering_increments(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            existing = _SAMPLE_TEMPLATE.replace("ticket: T-NNN", "ticket: T-000")
            d = _make_reflections_dir(tmpdir, {"R-001.md": existing})
            out = ar.create_reflection(
                reflections_dir=d,
                ticket="T-002",
                goal=None,
                skill=None,
                outcome="yes",
                duration_minutes=0,
                author="@Copilot",
            )
            self.assertEqual(out.name, "R-002.md")

    def test_content_contains_ticket(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            d = _make_reflections_dir(tmpdir)
            out = ar.create_reflection(
                reflections_dir=d,
                ticket="T-007",
                goal=None,
                skill=None,
                outcome="yes",
                duration_minutes=0,
                author="@Copilot",
            )
            self.assertIn("ticket: T-007", _read_reflection(out))


# ---------------------------------------------------------------------------
# Tests: main() CLI — idempotency
# ---------------------------------------------------------------------------

class TestMainCLIIdempotency(unittest.TestCase):

    def test_idempotent_same_ticket_skips(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            d = _make_reflections_dir(tmpdir)
            # First call creates R-001.md
            rc1 = ar.main([
                "--ticket", "T-002",
                "--reflections-dir", str(d),
            ])
            self.assertEqual(rc1, 0)
            # Second call for same ticket must exit 0 without creating R-002.md
            stderr_buf = io.StringIO()
            with redirect_stderr(stderr_buf):
                rc2 = ar.main([
                    "--ticket", "T-002",
                    "--reflections-dir", str(d),
                ])
            self.assertEqual(rc2, 0)
            files = [f.name for f in d.iterdir() if re.match(r"R-\d+\.md", f.name)]
            self.assertEqual(len(files), 1, "Should still be only one R-NNN.md")
            self.assertIn("WARNING", stderr_buf.getvalue())

    def test_different_tickets_create_different_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            d = _make_reflections_dir(tmpdir)
            ar.main(["--ticket", "T-001", "--reflections-dir", str(d)])
            ar.main(["--ticket", "T-002", "--reflections-dir", str(d)])
            files = sorted(f.name for f in d.iterdir() if re.match(r"R-\d+\.md", f.name))
            self.assertEqual(files, ["R-001.md", "R-002.md"])


# ---------------------------------------------------------------------------
# Tests: run_skill.py --reflect hook (via subprocess / patching)
# ---------------------------------------------------------------------------

class TestRunSkillReflectHook(unittest.TestCase):
    """Verify that _trigger_reflect is called when --reflect is passed."""

    def _make_env(self):
        env = os.environ.copy()
        env.pop("REFLECT", None)
        env.pop("TICKET", None)
        env.pop("GOAL", None)
        return env

    def test_reflect_flag_triggers_append_reflection(self):
        """When --reflect is passed, _trigger_reflect must be called."""
        # We patch _trigger_reflect to avoid needing a real skill setup
        import run_skill as rs
        called = []

        def fake_trigger(skill_id, ticket, goal):
            called.append((skill_id, ticket, goal))

        with tempfile.TemporaryDirectory() as tmpdir:
            # Build a minimal skill environment
            skills_dir = pathlib.Path(tmpdir) / ".agents" / "skills" / "test-skill"
            skills_dir.mkdir(parents=True)
            (skills_dir / "skill.md").write_text(
                "---\nid: test-skill\nmodel_tier: simple\n---\n# Test skill\n",
                encoding="utf-8",
            )
            prompts_dir = pathlib.Path(tmpdir) / "prompts"
            prompts_dir.mkdir()
            for fname in ("system.md", "safety.md", "skill-wrapper.md"):
                (prompts_dir / fname).write_text("{system}{safety}{skill}{memory_excerpt}{untrusted}", encoding="utf-8")
            run_dir = pathlib.Path(tmpdir) / ".agent-run"

            orig_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                with patch.object(rs, "_trigger_reflect", side_effect=fake_trigger):
                    with patch.object(rs, "call_github_models", return_value="stub"), \
                         patch.object(rs, "call_anthropic", return_value="stub"):
                        rc = rs.main(["--skill", "test-skill", "--reflect",
                                      "--ticket", "T-002", "--goal", "G-001"])
            finally:
                os.chdir(orig_cwd)

        self.assertEqual(rc, 0)
        self.assertEqual(len(called), 1)
        self.assertEqual(called[0], ("test-skill", "T-002", "G-001"))

    def test_no_reflect_flag_does_not_trigger(self):
        """Without --reflect, _trigger_reflect must NOT be called."""
        import run_skill as rs
        called = []

        def fake_trigger(skill_id, ticket, goal):
            called.append((skill_id, ticket, goal))

        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = pathlib.Path(tmpdir) / ".agents" / "skills" / "test-skill"
            skills_dir.mkdir(parents=True)
            (skills_dir / "skill.md").write_text(
                "---\nid: test-skill\nmodel_tier: simple\n---\n# Test skill\n",
                encoding="utf-8",
            )
            prompts_dir = pathlib.Path(tmpdir) / "prompts"
            prompts_dir.mkdir()
            for fname in ("system.md", "safety.md", "skill-wrapper.md"):
                (prompts_dir / fname).write_text("{system}{safety}{skill}{memory_excerpt}{untrusted}", encoding="utf-8")

            orig_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                with patch.object(rs, "_trigger_reflect", side_effect=fake_trigger):
                    with patch.object(rs, "call_github_models", return_value="stub"), \
                         patch.object(rs, "call_anthropic", return_value="stub"):
                        rc = rs.main(["--skill", "test-skill"])
            finally:
                os.chdir(orig_cwd)

        self.assertEqual(rc, 0)
        self.assertEqual(called, [])

    def test_reflect_env_var_triggers(self):
        """REFLECT=1 env var must activate the reflection hook."""
        import run_skill as rs
        called = []

        def fake_trigger(skill_id, ticket, goal):
            called.append((skill_id, ticket, goal))

        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = pathlib.Path(tmpdir) / ".agents" / "skills" / "test-skill"
            skills_dir.mkdir(parents=True)
            (skills_dir / "skill.md").write_text(
                "---\nid: test-skill\nmodel_tier: simple\n---\n# Test skill\n",
                encoding="utf-8",
            )
            prompts_dir = pathlib.Path(tmpdir) / "prompts"
            prompts_dir.mkdir()
            for fname in ("system.md", "safety.md", "skill-wrapper.md"):
                (prompts_dir / fname).write_text("{system}{safety}{skill}{memory_excerpt}{untrusted}", encoding="utf-8")

            orig_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                with patch.dict(os.environ, {"REFLECT": "1", "TICKET": "T-002", "GOAL": "G-001"}):
                    with patch.object(rs, "_trigger_reflect", side_effect=fake_trigger):
                        with patch.object(rs, "call_github_models", return_value="stub"), \
                             patch.object(rs, "call_anthropic", return_value="stub"):
                            rc = rs.main(["--skill", "test-skill"])
            finally:
                os.chdir(orig_cwd)

        self.assertEqual(rc, 0)
        self.assertEqual(len(called), 1)
        self.assertEqual(called[0][0], "test-skill")


if __name__ == "__main__":
    unittest.main()
