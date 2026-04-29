#!/usr/bin/env python3
"""Proactive Watch scan engine — scripts/scan_repo.py

Reads memory/watchlist.yml, executes each enabled health check, and outputs
a structured Markdown report.

CLI:
    python scripts/scan_repo.py [--watchlist PATH] [--repo-root PATH]

Exit codes:
    0 — all checks passed (no findings)
    1 — one or more findings detected

Constraints (T-005):
    - stdlib only (no new pip dependencies)
    - pure functional style, consistent with assemble_context.py / goal_stack.py
    - no LLM calls
    - each check silently skips when its source files are missing (never crashes)
    - PyYAML optional; falls back to regex parser (same convention as goal_stack.py)
"""

from __future__ import annotations

import argparse
import os
import pathlib
import re
import sys
from datetime import date, datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SCRIPT_DIR = pathlib.Path(__file__).parent
_DEFAULT_REPO_ROOT = (_SCRIPT_DIR / "..").resolve()
_DEFAULT_WATCHLIST = _DEFAULT_REPO_ROOT / "memory" / "watchlist.yml"

GOAL_FILE_PATTERN = re.compile(r"^G-\d+\.md$")
REFLECTION_FILE_PATTERN = re.compile(r"^R-\d+\.md$")

# ---------------------------------------------------------------------------
# YAML helpers (no external deps required)
# ---------------------------------------------------------------------------


def _parse_yaml_minimal(text: str) -> dict:
    """Very small YAML parser for the flat key: value / nested structure used here.

    Handles only what watchlist.yml and budget.md require; not a general parser.
    Falls back to PyYAML when available.
    """
    try:
        import yaml  # type: ignore  # noqa: PLC0415
        return yaml.safe_load(text) or {}
    except ImportError:
        pass

    result: dict = {}
    stack: list[tuple[int, dict]] = [(0, result)]  # (indent, dict)
    for raw_line in text.splitlines():
        stripped = raw_line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw_line) - len(stripped)
        if ":" not in stripped:
            continue
        key, sep, val = stripped.partition(":")
        key = key.strip()
        val = val.strip()

        # Pop stack to the right parent level
        while len(stack) > 1 and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1]

        if val == "" or val.startswith("#"):
            # Nested mapping
            child: dict = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            # Scalar — strip inline comment and quotes
            val = val.split("#")[0].strip()
            if val.lower() == "true":
                parent[key] = True
            elif val.lower() == "false":
                parent[key] = False
            else:
                try:
                    parent[key] = int(val)
                except ValueError:
                    try:
                        parent[key] = float(val)
                    except ValueError:
                        # Strip surrounding quotes
                        if (val.startswith('"') and val.endswith('"')) or \
                           (val.startswith("'") and val.endswith("'")):
                            val = val[1:-1]
                        parent[key] = val
    return result


# ---------------------------------------------------------------------------
# Watchlist loader
# ---------------------------------------------------------------------------


def load_watchlist(watchlist_path: pathlib.Path) -> dict[str, dict]:
    """Return {check_id: check_config} for all checks, enabled or not.

    Returns an empty dict when the file is missing or unreadable.
    """
    try:
        text = watchlist_path.read_text(encoding="utf-8")
    except OSError:
        return {}
    data = _parse_yaml_minimal(text)
    checks = data.get("checks") or {}
    if not isinstance(checks, dict):
        return {}
    return checks


# ---------------------------------------------------------------------------
# Front-matter helpers
# ---------------------------------------------------------------------------


def _fm_scalar(text: str, field: str) -> str | None:
    """Extract a scalar front-matter field from a markdown file."""
    m = re.search(rf"^{re.escape(field)}:\s*(.+)$", text, flags=re.MULTILINE)
    if not m:
        return None
    val = m.group(1).strip()
    if (val.startswith('"') and val.endswith('"')) or \
       (val.startswith("'") and val.endswith("'")):
        val = val[1:-1]
    return val


# ---------------------------------------------------------------------------
# Check: stale-goals
# ---------------------------------------------------------------------------


def _parse_last_advanced_date(text: str) -> date | None:
    """Return the most recent date from the ## Last advanced section, or None."""
    section_match = re.search(
        r"^##\s+Last advanced\s*\n(.*?)(?=^##\s|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not section_match:
        return None
    section = section_match.group(1)
    # Match lines starting with "- YYYY-MM-DD"
    dates = re.findall(r"^\s*-\s+(\d{4}-\d{2}-\d{2})", section, flags=re.MULTILINE)
    if not dates:
        return None
    parsed = []
    for d in dates:
        try:
            parsed.append(date.fromisoformat(d))
        except ValueError:
            continue
    return max(parsed) if parsed else None


def check_stale_goals(config: dict, repo_root: pathlib.Path) -> list[str]:
    """Return a list of finding strings for stale in-progress goals.

    A goal is stale when its status is 'in-progress' and the most recent
    'Last advanced' date is older than threshold_days.
    """
    threshold_days: int = int(config.get("threshold_days", 7))
    goals_dir = repo_root / "goals"
    findings: list[str] = []

    try:
        files = sorted(f for f in os.listdir(goals_dir) if GOAL_FILE_PATTERN.match(f))
    except OSError:
        return findings  # silently skip

    today = date.today()
    for filename in files:
        path = goals_dir / filename
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue

        status = _fm_scalar(text, "status")
        if status != "in-progress":
            continue

        last_adv = _parse_last_advanced_date(text)
        if last_adv is None:
            # No advancement recorded at all — treat creation date as last advanced
            created_str = _fm_scalar(text, "created")
            if created_str:
                try:
                    last_adv = date.fromisoformat(created_str)
                except ValueError:
                    pass

        if last_adv is None:
            findings.append(
                f"  - `{filename}`: in-progress, no 'Last advanced' date found"
            )
            continue

        age_days = (today - last_adv).days
        if age_days > threshold_days:
            findings.append(
                f"  - `{filename}`: in-progress, last advanced {last_adv.isoformat()}"
                f" ({age_days} days ago, threshold {threshold_days} days)"
            )

    return findings


# ---------------------------------------------------------------------------
# Check: missing-reflections
# ---------------------------------------------------------------------------


def _count_archived_tickets(repo_root: pathlib.Path) -> int:
    """Count T-NNN entries in the §9 Archived Tickets section of AGENT-COLLAB.md."""
    collab_path = repo_root / "AGENT-COLLAB.md"
    try:
        text = collab_path.read_text(encoding="utf-8")
    except OSError:
        return 0

    # Find the §9 section
    section_match = re.search(
        r"^##\s+9\..*?\n(.*?)(?=^##\s|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not section_match:
        # Fall back: count all T-NNN table rows in the whole file
        section_text = text
    else:
        section_text = section_match.group(1)

    tickets = re.findall(r"^\|\s*T-\d+", section_text, flags=re.MULTILINE)
    return len(tickets)


def _count_reflection_files(repo_root: pathlib.Path) -> int:
    """Count R-NNN.md files in the reflections/ directory."""
    reflections_dir = repo_root / "reflections"
    try:
        files = [f for f in os.listdir(reflections_dir) if REFLECTION_FILE_PATTERN.match(f)]
    except OSError:
        return 0
    return len(files)


def check_missing_reflections(config: dict, repo_root: pathlib.Path) -> list[str]:
    """Return findings when archived ticket count > reflection file count."""
    archived = _count_archived_tickets(repo_root)
    reflections = _count_reflection_files(repo_root)
    findings: list[str] = []

    if archived > reflections:
        findings.append(
            f"  - Archived tickets: {archived}, reflection files (R-NNN.md): {reflections}"
            f" — {archived - reflections} reflection(s) missing"
        )
    return findings


# ---------------------------------------------------------------------------
# Check: open-questions
# ---------------------------------------------------------------------------


def _parse_questions_section(text: str) -> list[dict]:
    """Parse the §5 Open Questions table into a list of row dicts."""
    section_match = re.search(
        r"^##\s+5\..*?\n(.*?)(?=^##\s|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not section_match:
        return []

    section = section_match.group(1)
    rows: list[dict] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        parts = [p.strip() for p in stripped.split("|")]
        parts = [p for p in parts if p]  # drop empty edge items
        # Table header / separator rows
        if len(parts) < 5:
            continue
        if parts[0].upper() == "ID" or set(parts[0]) <= {"-", " "}:
            continue
        # | ID | 提出时间 | 问题 | 提问者 | 待答者 | 状态 |
        # indices after splitting:  0   1         2      3        4       5
        row_id = parts[0]
        date_str = parts[1] if len(parts) > 1 else "—"
        status = parts[5] if len(parts) > 5 else parts[-1]
        rows.append({"id": row_id, "date": date_str, "status": status})
    return rows


def check_open_questions(config: dict, repo_root: pathlib.Path) -> list[str]:
    """Return findings for open questions older than threshold_days."""
    threshold_days: int = int(config.get("threshold_days", 7))
    collab_path = repo_root / "AGENT-COLLAB.md"
    findings: list[str] = []

    try:
        text = collab_path.read_text(encoding="utf-8")
    except OSError:
        return findings  # silently skip

    rows = _parse_questions_section(text)
    today = date.today()

    for row in rows:
        if row["status"].lower() != "open":
            continue
        date_str = row["date"]
        if date_str == "—" or not date_str:
            continue  # placeholder row, skip

        # Try to parse date (YYYY-MM-DD or full ISO)
        try:
            q_date = date.fromisoformat(date_str[:10])
        except ValueError:
            continue

        age_days = (today - q_date).days
        if age_days > threshold_days:
            findings.append(
                f"  - `{row['id']}`: open since {q_date.isoformat()}"
                f" ({age_days} days, threshold {threshold_days} days)"
            )

    return findings


# ---------------------------------------------------------------------------
# Check: audit-overrun
# ---------------------------------------------------------------------------


def _read_daily_budget(repo_root: pathlib.Path) -> int | None:
    """Parse daily_tokens from policies/budget.md."""
    budget_path = repo_root / "policies" / "budget.md"
    try:
        text = budget_path.read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.search(r"^daily_tokens:\s*(\d+)", text, flags=re.MULTILINE)
    if not m:
        return None
    return int(m.group(1))


def _sum_audit_tokens(repo_root: pathlib.Path) -> int:
    """Sum all Tokens column values from today's audit file."""
    today_str = date.today().isoformat()
    audit_path = repo_root / "memory" / "audit" / f"{today_str}.md"
    try:
        text = audit_path.read_text(encoding="utf-8")
    except OSError:
        return 0

    total = 0
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        parts = [p.strip() for p in stripped.split("|")]
        parts = [p for p in parts if p]
        # Row schema: Time | Phase | Skill | Status | Tokens | Run
        # Tokens is index 4 (0-based after filtering empty)
        if len(parts) < 5:
            continue
        token_str = parts[4]
        if token_str.upper() == "TOKENS" or set(token_str) <= {"-", " "}:
            continue
        try:
            total += int(token_str)
        except ValueError:
            continue
    return total


def check_audit_overrun(config: dict, repo_root: pathlib.Path) -> list[str]:
    """Return findings when today's token usage exceeds threshold_pct% of budget."""
    threshold_pct: int = int(config.get("threshold_pct", 80))
    daily_budget = _read_daily_budget(repo_root)
    findings: list[str] = []

    if daily_budget is None:
        return findings  # silently skip when budget file missing

    tokens_used = _sum_audit_tokens(repo_root)
    threshold_tokens = int(daily_budget * threshold_pct / 100)

    if tokens_used > threshold_tokens:
        pct_used = round(tokens_used * 100 / daily_budget, 1)
        findings.append(
            f"  - Tokens used today: {tokens_used:,} / {daily_budget:,}"
            f" ({pct_used}%, threshold {threshold_pct}%)"
        )
    return findings


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

CHECK_FUNCTIONS = {
    "stale-goals": check_stale_goals,
    "missing-reflections": check_missing_reflections,
    "open-questions": check_open_questions,
    "audit-overrun": check_audit_overrun,
}


def run_checks(watchlist: dict[str, dict], repo_root: pathlib.Path) -> dict[str, list[str]]:
    """Execute all enabled checks and return {check_id: [finding, ...]}."""
    results: dict[str, list[str]] = {}
    for check_id, config in watchlist.items():
        if not config.get("enabled", True):
            continue
        fn = CHECK_FUNCTIONS.get(check_id)
        if fn is None:
            continue  # unknown check type — silently skip
        try:
            findings = fn(config, repo_root)
        except Exception:  # noqa: BLE001 — never crash
            findings = []
        results[check_id] = findings
    return results


def build_report(results: dict[str, list[str]], watchlist: dict[str, dict]) -> str:
    """Build a Markdown report from check results."""
    lines: list[str] = []
    for check_id, findings in results.items():
        if not findings:
            continue
        description = (watchlist.get(check_id) or {}).get("description", check_id)
        lines.append(f"## {check_id}")
        lines.append(f"_{description}_")
        lines.append("")
        lines.extend(findings)
        lines.append("")
    return "\n".join(lines).rstrip()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scan_repo.py",
        description="Proactive Watch scan engine — reads watchlist.yml and checks repo health.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
exit codes:
  0  all checks passed (no findings)
  1  one or more findings detected

examples:
  python scripts/scan_repo.py
  python scripts/scan_repo.py --watchlist memory/watchlist.yml
  python scripts/scan_repo.py --repo-root /path/to/repo
        """,
    )
    parser.add_argument(
        "--watchlist",
        metavar="PATH",
        default=str(_DEFAULT_WATCHLIST),
        help=f"path to watchlist.yml (default: {_DEFAULT_WATCHLIST})",
    )
    parser.add_argument(
        "--repo-root",
        metavar="PATH",
        default=str(_DEFAULT_REPO_ROOT),
        help=f"repository root directory (default: {_DEFAULT_REPO_ROOT})",
    )

    args = parser.parse_args(argv)
    watchlist_path = pathlib.Path(args.watchlist).resolve()
    repo_root = pathlib.Path(args.repo_root).resolve()

    watchlist = load_watchlist(watchlist_path)
    results = run_checks(watchlist, repo_root)

    any_findings = any(bool(v) for v in results.values())

    if any_findings:
        report = build_report(results, watchlist)
        print(report)
        return 1
    else:
        print("All checks passed.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
