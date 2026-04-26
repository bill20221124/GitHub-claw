#!/usr/bin/env python3
"""
Minimal self-tests for scripts/goal_stack.py.

Run with:
  python -m unittest scripts/test_goal_stack.py
  python scripts/test_goal_stack.py
"""

import os
import sys
import tempfile
import textwrap
import unittest

# Allow running from repo root or from scripts/
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from goal_stack import (
    advance_goal,
    list_goals,
    parse_front_matter,
    set_status,
    show_goal,
    update_front_matter_field,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SAMPLE_GOAL = textwrap.dedent("""\
    ---
    id: G-099
    title: Test goal for unit tests
    status: backlog
    priority: P1
    owner: "@Copilot"
    created: 2026-01-01
    updated: 2026-01-01
    related_decisions: [D-001]
    related_tickets: [T-001]
    related_prs: []
    ---

    # Goal: Test goal for unit tests

    ## One-sentence statement

    A synthetic goal used only by the test suite.

    ## Acceptance Criteria

    - [ ] Tests pass

    ## Subtasks

    - [ ] Write tests

    ## Blockers

    (none)

    ## Last advanced

    - 2026-01-01 by @Architect: created goal.

    ## Lessons learned

    (none yet)
""")


def _write_goal(tmpdir, content=_SAMPLE_GOAL, name='G-099.md'):
    path = os.path.join(tmpdir, name)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(content)
    return path

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestParseFrontMatter(unittest.TestCase):

    def test_parses_scalar_fields(self):
        fm, _ = parse_front_matter(_SAMPLE_GOAL)
        self.assertEqual(fm['id'], 'G-099')
        self.assertEqual(fm['status'], 'backlog')
        self.assertEqual(fm['priority'], 'P1')

    def test_parses_list_fields(self):
        fm, _ = parse_front_matter(_SAMPLE_GOAL)
        self.assertIn('D-001', fm.get('related_decisions', []))

    def test_returns_empty_dict_on_no_frontmatter(self):
        fm, body = parse_front_matter('# Just a heading\n')
        self.assertEqual(fm, {})
        self.assertIn('Just a heading', body)


class TestUpdateFrontMatterField(unittest.TestCase):

    def test_replaces_existing_field(self):
        result = update_front_matter_field(_SAMPLE_GOAL, 'status', 'in-progress')
        fm, _ = parse_front_matter(result)
        self.assertEqual(fm['status'], 'in-progress')

    def test_does_not_affect_other_fields(self):
        result = update_front_matter_field(_SAMPLE_GOAL, 'status', 'in-progress')
        fm, _ = parse_front_matter(result)
        self.assertEqual(fm['id'], 'G-099')
        self.assertEqual(fm['priority'], 'P1')


class TestListGoals(unittest.TestCase):

    def test_list_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            import io
            from contextlib import redirect_stdout
            buf = io.StringIO()
            with redirect_stdout(buf):
                list_goals(tmpdir)
            self.assertIn('no goals', buf.getvalue())

    def test_list_shows_goal_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_goal(tmpdir)
            import io
            from contextlib import redirect_stdout
            buf = io.StringIO()
            with redirect_stdout(buf):
                list_goals(tmpdir)
            self.assertIn('G-099', buf.getvalue())


class TestShowGoal(unittest.TestCase):

    def test_show_prints_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_goal(tmpdir)
            import io
            from contextlib import redirect_stdout
            buf = io.StringIO()
            with redirect_stdout(buf):
                show_goal(tmpdir, 'G-099')
            self.assertIn('Test goal for unit tests', buf.getvalue())

    def test_show_missing_goal_exits(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(SystemExit) as ctx:
                show_goal(tmpdir, 'G-999')
            self.assertNotEqual(ctx.exception.code, 0)


class TestAdvanceGoal(unittest.TestCase):

    def test_advance_prepends_new_line(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _write_goal(tmpdir)
            advance_goal(tmpdir, 'G-099', 'completed sub-task', author='@Copilot')
            with open(path, encoding='utf-8') as fh:
                content = fh.read()
            # New line should appear before the original entry
            new_idx = content.index('completed sub-task')
            old_idx = content.index('created goal')
            self.assertLess(new_idx, old_idx)

    def test_advance_updates_updated_field(self):
        from datetime import date
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_goal(tmpdir)
            advance_goal(tmpdir, 'G-099', 'some progress', author='@Copilot')
            path = os.path.join(tmpdir, 'G-099.md')
            with open(path, encoding='utf-8') as fh:
                fm, _ = parse_front_matter(fh.read())
            self.assertEqual(str(fm['updated']), date.today().isoformat())

    def test_advance_uses_goal_author_env(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _write_goal(tmpdir)
            os.environ['GOAL_AUTHOR'] = 'EnvAuthor'
            try:
                advance_goal(tmpdir, 'G-099', 'env author test')
            finally:
                del os.environ['GOAL_AUTHOR']
            with open(path, encoding='utf-8') as fh:
                content = fh.read()
            self.assertIn('@EnvAuthor', content)


class TestSetStatus(unittest.TestCase):

    def _goal_with_status(self, tmpdir, status):
        content = _SAMPLE_GOAL.replace('status: backlog', f'status: {status}')
        _write_goal(tmpdir, content=content)

    def test_valid_transition_backlog_to_in_progress(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_goal(tmpdir)
            set_status(tmpdir, 'G-099', 'in-progress')
            path = os.path.join(tmpdir, 'G-099.md')
            with open(path, encoding='utf-8') as fh:
                fm, _ = parse_front_matter(fh.read())
            self.assertEqual(fm['status'], 'in-progress')

    def test_valid_transition_in_progress_to_done(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._goal_with_status(tmpdir, 'in-progress')
            set_status(tmpdir, 'G-099', 'done')
            path = os.path.join(tmpdir, 'G-099.md')
            with open(path, encoding='utf-8') as fh:
                fm, _ = parse_front_matter(fh.read())
            self.assertEqual(fm['status'], 'done')

    def test_illegal_transition_backlog_to_done_exits(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_goal(tmpdir)
            with self.assertRaises(SystemExit) as ctx:
                set_status(tmpdir, 'G-099', 'done')
            self.assertNotEqual(ctx.exception.code, 0)

    def test_illegal_transition_from_terminal_done_exits(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._goal_with_status(tmpdir, 'done')
            with self.assertRaises(SystemExit) as ctx:
                set_status(tmpdir, 'G-099', 'in-progress')
            self.assertNotEqual(ctx.exception.code, 0)

    def test_illegal_transition_from_terminal_abandoned_exits(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._goal_with_status(tmpdir, 'abandoned')
            with self.assertRaises(SystemExit) as ctx:
                set_status(tmpdir, 'G-099', 'in-progress')
            self.assertNotEqual(ctx.exception.code, 0)

    def test_noop_when_already_at_target_status(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_goal(tmpdir)
            # Should not raise or exit non-zero
            set_status(tmpdir, 'G-099', 'backlog')

    def test_in_progress_to_blocked(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._goal_with_status(tmpdir, 'in-progress')
            set_status(tmpdir, 'G-099', 'blocked')
            path = os.path.join(tmpdir, 'G-099.md')
            with open(path, encoding='utf-8') as fh:
                fm, _ = parse_front_matter(fh.read())
            self.assertEqual(fm['status'], 'blocked')

    def test_blocked_to_abandoned(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._goal_with_status(tmpdir, 'blocked')
            set_status(tmpdir, 'G-099', 'abandoned')
            path = os.path.join(tmpdir, 'G-099.md')
            with open(path, encoding='utf-8') as fh:
                fm, _ = parse_front_matter(fh.read())
            self.assertEqual(fm['status'], 'abandoned')


if __name__ == '__main__':
    unittest.main()
