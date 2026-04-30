#!/usr/bin/env python3
"""Reflection keyword index (TF-IDF) — scripts/embed_index.py

Builds a lightweight TF-IDF index over all reflections/R-NNN.md files so that
the Working Set assembler can retrieve the *most relevant* reflections for the
current event instead of the most recent audit rows.

Public API
----------
    build_index(repo_root)                         -> dict
    query_index(index, query, top_n=3)             -> list[tuple[str, float]]
    save_index(index, path)                        -> None
    load_index(path)                               -> dict
    load_or_build_index(repo_root, cache_path=None) -> dict

Index schema (JSON-serializable)
---------------------------------
    {
      "docs": {
        "R-001.md": {"terms": {"goal": 3, "ticket": 2, ...}, "total": 84},
        ...
      },
      "df":  {"goal": 5, "ticket": 4, ...},   # document frequency
      "N":   8                                  # total documents
    }

TF-IDF details
--------------
    TF(t, d)  = count(t in d) / total_terms(d)
    IDF(t)    = log((N + 1) / (df(t) + 1)) + 1.0   [smooth, sklearn-style]
    score(d)  = cosine_similarity(query_vector, doc_vector)

Constraints (T-007):
    - stdlib only (no new pip dependencies)
    - pure functional style
    - no LLM calls
    - silently skips unreadable files
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import re
import sys

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SCRIPT_DIR = pathlib.Path(__file__).parent
_DEFAULT_REPO_ROOT = (_SCRIPT_DIR / "..").resolve()
_DEFAULT_CACHE_NAME = ".agent_index.json"

_REFLECTION_PATTERN = re.compile(r"^R-\d+\.md$")

# Minimal stop-word list (common English function words + markdown artefacts)
_STOP_WORDS: frozenset[str] = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "not", "no", "nor",
    "this", "that", "these", "those", "it", "its", "i", "we", "you",
    "he", "she", "they", "my", "our", "your", "his", "her", "their",
    "as", "if", "so", "then", "than", "when", "where", "which", "who",
    "what", "how", "all", "each", "every", "some", "any", "both", "few",
    "more", "most", "other", "into", "through", "about", "against", "between",
    "after", "before", "up", "out", "off", "over", "under", "again",
    # Common Markdown/YAML tokens that add no semantic signal
    "md", "yml", "yaml", "py", "true", "false", "null", "none", "yes",
    # Protocol-bus filler words
    "ref", "type", "topic", "body", "next", "action", "by",
})

# ---------------------------------------------------------------------------
# Tokeniser
# ---------------------------------------------------------------------------


def _tokenize(text: str) -> list[str]:
    """Return lowercase alphanumeric tokens (ASCII + CJK), stop-words removed."""
    tokens = re.findall(r"[a-zA-Z\u4e00-\u9fff]+", text.lower())
    return [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]


# ---------------------------------------------------------------------------
# Index construction
# ---------------------------------------------------------------------------


def _read_reflection(path: pathlib.Path) -> str:
    """Read a reflection file, returning empty string on error."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError, ValueError):
        return ""


def build_index(repo_root: pathlib.Path | None = None) -> dict:
    """Build a TF-IDF index from all reflections/R-NNN.md files.

    Args:
        repo_root: Repository root.  Defaults to the parent of scripts/.

    Returns:
        Index dict with keys "docs", "df", "N".
    """
    if repo_root is None:
        repo_root = _DEFAULT_REPO_ROOT

    reflections_dir = repo_root / "reflections"
    docs: dict[str, dict] = {}
    df: dict[str, int] = {}

    if reflections_dir.is_dir():
        try:
            filenames = sorted(
                f for f in reflections_dir.iterdir()
                if _REFLECTION_PATTERN.match(f.name)
            )
        except OSError:
            filenames = []

        for fpath in filenames:
            text = _read_reflection(fpath)
            if not text:
                continue

            tokens = _tokenize(text)
            if not tokens:
                continue

            term_counts: dict[str, int] = {}
            for t in tokens:
                term_counts[t] = term_counts.get(t, 0) + 1

            docs[fpath.name] = {"terms": term_counts, "total": len(tokens)}

            for term in term_counts:
                df[term] = df.get(term, 0) + 1

    return {"docs": docs, "df": df, "N": len(docs)}


# ---------------------------------------------------------------------------
# Querying
# ---------------------------------------------------------------------------


def _tfidf_vector(term_counts: dict[str, int], total: int,
                  df: dict[str, int], N: int) -> dict[str, float]:
    """Compute a TF-IDF vector for a single document."""
    vec: dict[str, float] = {}
    for term, count in term_counts.items():
        tf = count / total if total else 0.0
        idf = math.log((N + 1) / (df.get(term, 0) + 1)) + 1.0
        vec[term] = tf * idf
    return vec


def _dot(a: dict[str, float], b: dict[str, float]) -> float:
    """Dot product of two sparse vectors (dicts)."""
    # Iterate over the smaller dict for efficiency
    if len(a) > len(b):
        a, b = b, a
    return sum(v * b.get(k, 0.0) for k, v in a.items())


def _norm(vec: dict[str, float]) -> float:
    """L2 norm of a sparse vector."""
    return math.sqrt(sum(v * v for v in vec.values())) or 1e-10


def query_index(index: dict, query: str, top_n: int = 3) -> list[tuple[str, float]]:
    """Return the top-N most relevant reflection filenames with their scores.

    Args:
        index:  Index dict produced by ``build_index``.
        query:  Free-text query string.
        top_n:  Maximum number of results to return.

    Returns:
        List of (filename, cosine_score) tuples, sorted descending by score.
        An empty list is returned when the index has no documents or query is
        empty.
    """
    docs = index.get("docs", {})
    df = index.get("df", {})
    N = index.get("N", 0)

    if not docs or not query.strip():
        return []

    # Build query vector
    q_tokens = _tokenize(query)
    if not q_tokens:
        return []

    q_counts: dict[str, int] = {}
    for t in q_tokens:
        q_counts[t] = q_counts.get(t, 0) + 1

    q_vec = _tfidf_vector(q_counts, len(q_tokens), df, N)
    q_norm = _norm(q_vec)

    scores: list[tuple[str, float]] = []
    for filename, doc_data in docs.items():
        d_vec = _tfidf_vector(doc_data["terms"], doc_data["total"], df, N)
        d_norm = _norm(d_vec)
        score = _dot(q_vec, d_vec) / (q_norm * d_norm)
        if score > 0.0:
            scores.append((filename, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_n]


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def save_index(index: dict, path: pathlib.Path) -> None:
    """Serialise index to JSON.  Parent directories are created if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index, ensure_ascii=False, indent=2),
                    encoding="utf-8")


def load_index(path: pathlib.Path) -> dict:
    """Load a previously saved index from JSON.

    Raises:
        OSError:       If the file cannot be read.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    return json.loads(path.read_text(encoding="utf-8"))


def load_or_build_index(
    repo_root: pathlib.Path | None = None,
    cache_path: pathlib.Path | None = None,
) -> dict:
    """Return a cached index if up-to-date, otherwise rebuild and cache.

    The cache is stored at *cache_path* (defaults to
    ``<repo_root>/.agent_index.json``).  The cache is considered stale if any
    ``reflections/R-NNN.md`` file is newer than the cache file.

    Silently falls back to a freshly built (uncached) index on any I/O error.
    """
    if repo_root is None:
        repo_root = _DEFAULT_REPO_ROOT
    if cache_path is None:
        cache_path = repo_root / _DEFAULT_CACHE_NAME

    # Check if cache exists and is fresh
    try:
        cache_mtime = cache_path.stat().st_mtime
        reflections_dir = repo_root / "reflections"
        stale = False
        if reflections_dir.is_dir():
            for fpath in reflections_dir.iterdir():
                if _REFLECTION_PATTERN.match(fpath.name):
                    if fpath.stat().st_mtime > cache_mtime:
                        stale = True
                        break
        if not stale:
            return load_index(cache_path)
    except (OSError, json.JSONDecodeError):
        pass

    # Rebuild
    index = build_index(repo_root)
    try:
        save_index(index, cache_path)
    except OSError:
        pass  # Cache write failure is non-fatal

    return index


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Query the TF-IDF reflection index.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--query", "-q", default="",
                        help="Query text to search for relevant reflections.")
    parser.add_argument("--top-n", "-n", type=int, default=3,
                        help="Number of results to return (default: 3).")
    parser.add_argument("--rebuild", action="store_true",
                        help="Force rebuild the index even if cache is fresh.")
    parser.add_argument(
        "--repo-root", default=None,
        help="Repository root directory (default: parent of scripts/).",
    )
    args = parser.parse_args(argv)

    repo_root = pathlib.Path(args.repo_root).resolve() if args.repo_root else None

    if args.rebuild:
        rr = repo_root or _DEFAULT_REPO_ROOT
        index = build_index(rr)
        cache = rr / _DEFAULT_CACHE_NAME
        try:
            save_index(index, cache)
            print(f"Index rebuilt and saved to {cache}")
        except OSError as exc:
            print(f"Warning: could not save index: {exc}", file=sys.stderr)
    else:
        index = load_or_build_index(repo_root)

    if not args.query.strip():
        print(f"Index contains {index.get('N', 0)} document(s).")
        return 0

    results = query_index(index, args.query, args.top_n)
    if not results:
        print("No relevant reflections found.")
        return 0

    for filename, score in results:
        print(f"{score:.4f}  {filename}")
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
