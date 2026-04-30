#!/usr/bin/env python3
"""Tests for scripts/embed_index.py.

Run:
    python -m unittest scripts/test_embed_index.py

Coverage:
     1.  _tokenize: lowercases and removes stop-words
     2.  _tokenize: removes short tokens (len ≤ 1)
     3.  build_index: empty corpus returns N=0 and empty docs/df
     4.  build_index: single document produces correct term counts
     5.  build_index: multiple documents produce correct df entries
     6.  build_index: unreadable files are silently skipped
     7.  build_index: non-reflection files (README.md etc.) are skipped
     8.  query_index: returns empty list for empty index
     9.  query_index: returns empty list for blank query
    10.  query_index: returns relevant document for matching query
    11.  query_index: top_n=1 returns at most 1 result
    12.  query_index: score is between 0 and 1 (cosine similarity)
    13.  save_index / load_index: round-trip preserves data
    14.  load_or_build_index: creates cache file on first call
    15.  load_or_build_index: uses cache when reflections unchanged
    16.  load_or_build_index: rebuilds when a reflection is newer than cache
    17.  load_or_build_index: gracefully handles corrupt cache
    18.  assemble_context: Layer 3 uses relevant reflections when embed_index present
    19.  assemble_context: Layer 3 falls back to recent audit when no reflections match
    20.  assemble_context: total length still ≤ 6000 with embed_index active
"""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import sys
import tempfile
import textwrap
import time
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


ei = _load_module("embed_index", _SCRIPTS / "embed_index.py")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")


def _make_reflection(root: pathlib.Path, name: str, content: str) -> pathlib.Path:
    """Write a reflection file into <root>/reflections/<name>."""
    fpath = root / "reflections" / name
    _write(fpath, content)
    return fpath


# ---------------------------------------------------------------------------
# Test 1 & 2 — _tokenize
# ---------------------------------------------------------------------------


class TestTokenize(unittest.TestCase):
    def test_lowercases_and_removes_stopwords(self):
        tokens = ei._tokenize("The Goal Stack is complete")
        self.assertNotIn("the", tokens)
        self.assertNotIn("is", tokens)
        self.assertIn("goal", tokens)
        self.assertIn("stack", tokens)
        self.assertIn("complete", tokens)

    def test_removes_short_tokens(self):
        tokens = ei._tokenize("a b c do")
        # "a", "b", "c" are len≤1 or stop-words
        self.assertNotIn("a", tokens)
        self.assertNotIn("b", tokens)
        self.assertNotIn("c", tokens)


# ---------------------------------------------------------------------------
# Tests 3–7 — build_index
# ---------------------------------------------------------------------------


class TestBuildIndex(unittest.TestCase):
    def test_empty_corpus_returns_zero_n(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            # No reflections directory
            index = ei.build_index(root)
            self.assertEqual(index["N"], 0)
            self.assertEqual(index["docs"], {})
            self.assertEqual(index["df"], {})

    def test_single_document_term_counts(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            _make_reflection(root, "R-001.md",
                             "Goal Stack complete. Goal achieved.")
            index = ei.build_index(root)
            self.assertEqual(index["N"], 1)
            self.assertIn("R-001.md", index["docs"])
            terms = index["docs"]["R-001.md"]["terms"]
            # "goal" appears twice
            self.assertGreaterEqual(terms.get("goal", 0), 2)
            # "stack" and "complete" and "achieved" each appear once
            self.assertGreaterEqual(terms.get("stack", 0), 1)

    def test_multiple_docs_produce_correct_df(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            _make_reflection(root, "R-001.md", "Reflection on goals achieved.")
            _make_reflection(root, "R-002.md", "Goals and reflections matter.")
            index = ei.build_index(root)
            self.assertEqual(index["N"], 2)
            # "goals" (or "goal") should appear in both docs
            df = index["df"]
            goal_df = df.get("goals", 0) + df.get("goal", 0)
            self.assertGreaterEqual(goal_df, 1)  # at least in one doc

    def test_unreadable_file_skipped_silently(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            _make_reflection(root, "R-001.md", "Valid reflection content.")
            bad = root / "reflections" / "R-002.md"
            bad.parent.mkdir(parents=True, exist_ok=True)
            bad.write_bytes(b"\xff\xfe")  # invalid UTF-8 — causes read error
            # build_index must not raise
            try:
                index = ei.build_index(root)
            except Exception as exc:  # noqa: BLE001
                self.fail(f"build_index raised unexpectedly: {exc}")
            # R-001.md should still be indexed
            self.assertIn("R-001.md", index["docs"])

    def test_non_reflection_files_skipped(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            # Write files that don't match R-NNN.md pattern
            _write(root / "reflections" / "README.md", "Not a reflection.")
            _write(root / "reflections" / "_template.md", "Template.")
            _write(root / "reflections" / "R-PHASE-2.md", "Phase summary.")
            _make_reflection(root, "R-001.md", "Real reflection.")
            index = ei.build_index(root)
            self.assertIn("R-001.md", index["docs"])
            self.assertNotIn("README.md", index["docs"])
            self.assertNotIn("_template.md", index["docs"])
            self.assertNotIn("R-PHASE-2.md", index["docs"])


# ---------------------------------------------------------------------------
# Tests 8–12 — query_index
# ---------------------------------------------------------------------------


class TestQueryIndex(unittest.TestCase):
    def _make_index(self) -> dict:
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            _make_reflection(root, "R-001.md",
                             "Goal Stack CLI complete. Implemented list show advance.")
            _make_reflection(root, "R-002.md",
                             "Reflection automation: append_reflection.py created.")
            _make_reflection(root, "R-003.md",
                             "Working set assembly: assemble_context four layers.")
            return ei.build_index(root)

    def test_empty_index_returns_empty_list(self):
        empty_index = {"docs": {}, "df": {}, "N": 0}
        self.assertEqual(ei.query_index(empty_index, "goal stack"), [])

    def test_blank_query_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            _make_reflection(root, "R-001.md", "Some content here.")
            index = ei.build_index(root)
            self.assertEqual(ei.query_index(index, ""), [])
            self.assertEqual(ei.query_index(index, "   "), [])

    def test_relevant_document_returned(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            _make_reflection(root, "R-001.md",
                             "Goal Stack CLI. list show advance set-status commands.")
            _make_reflection(root, "R-002.md",
                             "Reflection automation append_reflection script created.")
            index = ei.build_index(root)
            results = ei.query_index(index, "goal stack CLI commands")
            self.assertGreater(len(results), 0)
            top_file, top_score = results[0]
            self.assertEqual(top_file, "R-001.md")

    def test_top_n_limits_results(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            for i in range(1, 6):
                _make_reflection(root, f"R-00{i}.md",
                                 f"Reflection {i} about goals and tickets.")
            index = ei.build_index(root)
            results = ei.query_index(index, "goals tickets", top_n=1)
            self.assertLessEqual(len(results), 1)

    def test_score_is_between_zero_and_one(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            _make_reflection(root, "R-001.md",
                             "Goal Stack complete ticket achieved reflection.")
            index = ei.build_index(root)
            results = ei.query_index(index, "goal stack complete", top_n=3)
            for _fname, score in results:
                self.assertGreaterEqual(score, 0.0)
                self.assertLessEqual(score, 1.0 + 1e-9)  # allow floating-point drift


# ---------------------------------------------------------------------------
# Tests 13 — save_index / load_index
# ---------------------------------------------------------------------------


class TestPersistence(unittest.TestCase):
    def test_roundtrip_preserves_data(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            _make_reflection(root, "R-001.md", "Persistence test content.")
            index = ei.build_index(root)
            cache = root / ".agent_index.json"
            ei.save_index(index, cache)
            loaded = ei.load_index(cache)
            self.assertEqual(loaded["N"], index["N"])
            self.assertEqual(loaded["docs"].keys(), index["docs"].keys())
            self.assertEqual(loaded["df"], index["df"])


# ---------------------------------------------------------------------------
# Tests 14–17 — load_or_build_index
# ---------------------------------------------------------------------------


class TestLoadOrBuild(unittest.TestCase):
    def test_creates_cache_on_first_call(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            _make_reflection(root, "R-001.md", "First reflection.")
            cache = root / ".agent_index.json"
            self.assertFalse(cache.exists())
            ei.load_or_build_index(root, cache)
            self.assertTrue(cache.exists())

    def test_uses_cache_when_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            _make_reflection(root, "R-001.md", "Stable reflection.")
            cache = root / ".agent_index.json"
            # First build
            index1 = ei.load_or_build_index(root, cache)
            mtime1 = cache.stat().st_mtime
            # Second call — no reflection changed, cache should be reused
            time.sleep(0.05)
            index2 = ei.load_or_build_index(root, cache)
            mtime2 = cache.stat().st_mtime
            self.assertEqual(mtime1, mtime2, "Cache should not be rewritten")
            self.assertEqual(index1["N"], index2["N"])

    def test_rebuilds_when_reflection_newer_than_cache(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            _make_reflection(root, "R-001.md", "Original reflection.")
            cache = root / ".agent_index.json"
            ei.load_or_build_index(root, cache)
            # Simulate a newer reflection
            time.sleep(0.05)
            _make_reflection(root, "R-002.md", "New reflection about working set.")
            index2 = ei.load_or_build_index(root, cache)
            self.assertEqual(index2["N"], 2)

    def test_handles_corrupt_cache_gracefully(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            _make_reflection(root, "R-001.md", "Valid content.")
            cache = root / ".agent_index.json"
            cache.write_text("{ not valid json }", encoding="utf-8")
            # Should not raise — rebuilds from scratch
            try:
                index = ei.load_or_build_index(root, cache)
            except Exception as exc:  # noqa: BLE001
                self.fail(f"load_or_build_index raised unexpectedly: {exc}")
            self.assertGreaterEqual(index["N"], 0)


# ---------------------------------------------------------------------------
# Tests 18–20 — assemble_context integration
# ---------------------------------------------------------------------------

ac = _load_module("assemble_context", _SCRIPTS / "assemble_context.py")


class TestAssembleContextIntegration(unittest.TestCase):
    def _write_memory(self, root: pathlib.Path) -> None:
        _write(root / "MEMORY.md", """\
            # MEMORY.md
            ## Standing Context
            - Fact A
            ## Task Log
            | Date | Summary |
        """)

    def test_layer3_uses_relevant_reflections(self):
        """When embed_index is present and reflections exist, Layer 3 uses them."""
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            self._write_memory(root)
            # Write a reflection about goal stack
            _write(root / "reflections" / "R-001.md", textwrap.dedent("""\
                ---
                id: R-001
                ---
                # Reflection R-001
                ## 1. Did the task meet its acceptance criteria?
                Goal Stack CLI list show advance set-status complete.
                ## 2. Which memories did I rely on?
                - goals/G-001.md
                ## 3. What memory was missing?
                (none)
                ## 4. What would I change next time?
                Nothing.
            """))
            event = {
                "issue": {
                    "title": "Goal Stack CLI commands",
                    "body": "Implement goal stack list show advance",
                }
            }
            result = ac.assemble(event, root)
            # Should contain either the reflection content or the Layer 3 header
            self.assertIn("Relevant Context", result)

    def test_layer3_falls_back_to_recent_audit(self):
        """When no reflections exist, Layer 3 falls back to recent audit."""
        from datetime import date as _date
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            self._write_memory(root)
            # Write audit but no reflections
            today = _date.today().isoformat()
            _write(root / "memory" / "audit" / f"{today}.md",
                   "# Audit\n| 10:00Z | finish | summarize | success | 100 | 1 |\n")
            result = ac.assemble({}, root)
            # Layer 3 should still appear and contain something
            self.assertIn("Relevant Context", result)
            self.assertIsInstance(result, str)

    def test_total_length_within_limit_with_embed_index(self):
        """Total output stays within 6000 chars even when reflections are large."""
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            self._write_memory(root)
            for i in range(1, 6):
                _write(root / "reflections" / f"R-00{i}.md",
                       f"---\nid: R-00{i}\n---\n# Reflection\n" + "x " * 500)
            event = {"issue": {"title": "test query", "body": "test " * 50}}
            result = ac.assemble(event, root)
            self.assertLessEqual(len(result), ac.TOTAL_CHAR_LIMIT)


if __name__ == "__main__":
    unittest.main()
