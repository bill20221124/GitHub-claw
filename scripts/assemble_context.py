#!/usr/bin/env python3
"""Working Set assembler — scripts/assemble_context.py

Assembles a ContextPack for the current task from layered memory sources,
replacing the blunt ``memory_excerpt()`` approach in run_skill.py.

Public API:
    assemble(event: dict, repo_root: pathlib.Path | None = None) -> str

Layer priority (total ≤ 6000 chars; truncated by layer when over budget):
    1. Standing Context — MEMORY.md ## Standing Context section   (≤ 1500 chars)
    2. Active Goal      — in-progress goals/G-NNN.md              (≤ 1500 chars)
    3. Recent Audit     — memory/audit/ last 7 days, 20 lines max (≤ 1500 chars)
    4. Event Hint       — file paths extracted from PR/issue event (≤  500 chars)

Constraints (T-003):
    - stdlib only (no new pip dependencies)
    - pure functional style, matches goal_stack.py / append_reflection.py convention
    - no LLM calls
    - each layer silently skips (returns "(not available)") when its source files
      are missing or unreadable; never raises an exception to the caller
"""

from __future__ import annotations

import os
import pathlib
import re
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SCRIPT_DIR = pathlib.Path(__file__).parent
_DEFAULT_REPO_ROOT = (_SCRIPT_DIR / "..").resolve()

TOTAL_CHAR_LIMIT = 6000

LAYER_LIMITS = {
    "standing_context": 1500,
    "active_goal": 1500,
    "recent_audit": 1500,
    "event_hint": 500,
}

GOAL_FILE_PATTERN = re.compile(r"^G-\d+\.md$")

# ---------------------------------------------------------------------------
# Layer 1 — Standing Context
# ---------------------------------------------------------------------------


def _extract_standing_context(repo_root: pathlib.Path) -> str:
    """Extract the ## Standing Context section from MEMORY.md."""
    mem_path = repo_root / "MEMORY.md"
    try:
        text = mem_path.read_text(encoding="utf-8")
    except OSError:
        return "(not available)"

    # Find the section
    match = re.search(r"^##\s+Standing Context\s*\n(.*?)(?=^##\s|\Z)", text,
                      flags=re.MULTILINE | re.DOTALL)
    if not match:
        return "(not available)"

    return match.group(1).strip()


# ---------------------------------------------------------------------------
# Layer 2 — Active Goal
# ---------------------------------------------------------------------------


def _extract_active_goals(repo_root: pathlib.Path) -> str:
    """Summarise in-progress goals from goals/G-NNN.md files."""
    goals_dir = repo_root / "goals"
    if not goals_dir.is_dir():
        return "(not available)"

    try:
        files = sorted(f for f in os.listdir(goals_dir) if GOAL_FILE_PATTERN.match(f))
    except OSError:
        return "(not available)"

    if not files:
        return "(not available)"

    parts: list[str] = []
    for filename in files:
        path = goals_dir / filename
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue

        status = _fm_scalar(text, "status")
        if status != "in-progress":
            continue

        title = _fm_scalar(text, "title") or filename
        acceptance = _extract_section(text, "Acceptance Criteria")
        last_advanced = _extract_section(text, "Last advanced")

        chunk = f"### {filename[:-3]}: {title}\n"
        if acceptance:
            chunk += f"**Acceptance Criteria:**\n{acceptance}\n"
        if last_advanced:
            chunk += f"**Last advanced:**\n{last_advanced}\n"
        parts.append(chunk.strip())

    return "\n\n".join(parts) if parts else "(not available)"


def _fm_scalar(text: str, field: str) -> str | None:
    """Extract a scalar field from YAML front-matter."""
    m = re.search(rf"^{re.escape(field)}:\s*(.+)$", text, flags=re.MULTILINE)
    if not m:
        return None
    value = m.group(1).strip()
    if value.startswith(("'", '"')) and value.endswith(value[0]):
        value = value[1:-1]
    return value


def _extract_section(text: str, heading: str) -> str:
    """Extract the body of a markdown ## heading section."""
    match = re.search(
        rf"^##\s+{re.escape(heading)}\s*\n(.*?)(?=^##\s|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not match:
        return ""
    return match.group(1).strip()


# ---------------------------------------------------------------------------
# Layer 3 — Recent Audit
# ---------------------------------------------------------------------------


def _extract_recent_audit(repo_root: pathlib.Path) -> str:
    """Return last 20 audit lines from the most recent 7 days of audit logs."""
    audit_dir = repo_root / "memory" / "audit"
    if not audit_dir.is_dir():
        return "(not available)"

    today = date.today()
    candidate_dates = [today - timedelta(days=i) for i in range(7)]

    lines: list[str] = []
    for d in candidate_dates:
        audit_file = audit_dir / f"{d.isoformat()}.md"
        try:
            text = audit_file.read_text(encoding="utf-8")
        except OSError:
            continue
        # Collect non-empty, non-header lines
        for line in text.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                lines.append(line)

    if not lines:
        return "(not available)"

    # Keep the most recent 20 lines
    recent = lines[-20:]
    return "\n".join(recent)


# ---------------------------------------------------------------------------
# Layer 4 — Event Hint
# ---------------------------------------------------------------------------


def _extract_event_hint(event: dict) -> str:
    """Extract file paths from a GitHub PR or issue event dict."""
    if not event:
        return "(not available)"

    paths: list[str] = []

    # PR: pull_request.changed_files is a count; file paths come from the
    # files endpoint which isn't in the raw event JSON.  Instead, look for
    # head.ref, base.ref, and any file-list the dispatcher may have injected.
    pr = event.get("pull_request") or {}
    if pr:
        head_ref = pr.get("head", {}).get("ref", "")
        base_ref = pr.get("base", {}).get("ref", "")
        if head_ref:
            paths.append(f"PR head: {head_ref}")
        if base_ref:
            paths.append(f"PR base: {base_ref}")

    # Some dispatcher implementations inject a `changed_files` list
    changed = event.get("changed_files") or []
    if isinstance(changed, list):
        paths.extend(str(p) for p in changed[:20])

    # Issue / PR body — extract file-path-like tokens (heuristic)
    body = (
        (event.get("comment") or {}).get("body")
        or (event.get("issue") or {}).get("body")
        or pr.get("body")
        or ""
    )
    file_tokens = re.findall(r"\b[\w./\-]+\.(?:py|yml|yaml|md|json|sh)\b", body)
    paths.extend(file_tokens[:20])

    if not paths:
        return "(not available)"

    return "\n".join(dict.fromkeys(paths))  # deduplicate, preserve order


# ---------------------------------------------------------------------------
# Budget enforcement
# ---------------------------------------------------------------------------


def _budget(text: str, limit: int) -> str:
    """Truncate *text* to *limit* chars, appending a note when clipped."""
    if len(text) <= limit:
        return text
    return text[: limit - 20].rstrip() + "\n… [truncated]"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def assemble(event: dict, repo_root: pathlib.Path | None = None) -> str:
    """Assemble and return a ContextPack Markdown string for the current task.

    Args:
        event:     GitHub event dict (from $GITHUB_EVENT_PATH).  May be empty.
        repo_root: Repository root directory.  Defaults to the parent of the
                   scripts/ directory, i.e. the repository root at runtime.

    Returns:
        A Markdown string with four labelled sections.  Total length ≤ 6000
        chars.  Individual layers that cannot be read return "(not available)"
        rather than raising an exception.
    """
    if repo_root is None:
        repo_root = _DEFAULT_REPO_ROOT

    # Collect each layer (may return "(not available)")
    try:
        standing = _extract_standing_context(repo_root)
    except Exception:  # noqa: BLE001
        standing = "(not available)"

    try:
        goals = _extract_active_goals(repo_root)
    except Exception:  # noqa: BLE001
        goals = "(not available)"

    try:
        audit = _extract_recent_audit(repo_root)
    except Exception:  # noqa: BLE001
        audit = "(not available)"

    try:
        hint = _extract_event_hint(event)
    except Exception:  # noqa: BLE001
        hint = "(not available)"

    # Apply per-layer budgets
    standing = _budget(standing, LAYER_LIMITS["standing_context"])
    goals = _budget(goals, LAYER_LIMITS["active_goal"])
    audit = _budget(audit, LAYER_LIMITS["recent_audit"])
    hint = _budget(hint, LAYER_LIMITS["event_hint"])

    sections = [
        ("## Standing Context", standing),
        ("## Active Goal", goals),
        ("## Recent Audit", audit),
        ("## Event Hint", hint),
    ]

    # Build output, enforcing the total cap by dropping trailing sections
    output_parts: list[str] = []
    remaining = TOTAL_CHAR_LIMIT

    for header, body in sections:
        block = f"{header}\n\n{body}"
        if remaining <= 0:
            break
        if len(block) > remaining:
            # Truncate the block to fit
            block = block[:remaining].rstrip() + "\n… [truncated]"
        output_parts.append(block)
        remaining -= len(block)

    return "\n\n".join(output_parts)
