#!/usr/bin/env python3
"""Append a new reflection skeleton to reflections/R-NNN.md.

Creates the next available R-NNN.md from reflections/_template.md with the
front-matter fields populated.  The four body question sections are left as
blank placeholders — answers must be filled in by a human or @Copilot.

Idempotent: if a reflection for the given --ticket already exists, the script
prints a warning and exits 0 without overwriting anything.

CLI usage (human / tests):
    python scripts/append_reflection.py \\
        --ticket T-002 \\
        --goal G-001 \\
        [--skill summarize] \\
        [--outcome pass|partial|fail] \\
        [--duration-minutes 30]

Constraints (T-002):
    - stdlib only (no new pip dependencies)
    - pure functional style (matches goal_stack.py convention)
    - no LLM calls
    - only creates skeleton; never fills four-question answers
"""

from __future__ import annotations

import argparse
import os
import pathlib
import re
import sys
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SCRIPT_DIR = pathlib.Path(__file__).parent
DEFAULT_REFLECTIONS_DIR = (_SCRIPT_DIR / ".." / "reflections").resolve()

REFLECTION_FILE_PATTERN = re.compile(r"^R-(\d+)\.md$")
TEMPLATE_FILENAME = "_template.md"

# Maps --outcome CLI value → YAML front-matter value
OUTCOME_MAP = {
    "pass": "yes",
    "partial": "partial",
    "fail": "no",
}

# ---------------------------------------------------------------------------
# Pure-functional helpers
# ---------------------------------------------------------------------------


def next_reflection_number(reflections_dir: pathlib.Path) -> int:
    """Return the next available R-NNN sequence number (1-based)."""
    max_num = 0
    if reflections_dir.is_dir():
        for entry in reflections_dir.iterdir():
            m = REFLECTION_FILE_PATTERN.match(entry.name)
            if m:
                max_num = max(max_num, int(m.group(1)))
    return max_num + 1


def find_existing_for_ticket(
    reflections_dir: pathlib.Path, ticket: str
) -> pathlib.Path | None:
    """Return the path of an existing reflection for *ticket*, or None."""
    if not reflections_dir.is_dir():
        return None
    for entry in sorted(reflections_dir.iterdir()):
        if not REFLECTION_FILE_PATTERN.match(entry.name):
            continue
        try:
            text = entry.read_text(encoding="utf-8")
        except OSError:
            continue
        if _extract_fm_field(text, "ticket") == ticket:
            return entry
    return None


def _extract_fm_field(text: str, field: str) -> str | None:
    """Extract a scalar field from YAML front-matter."""
    m = re.search(
        rf"^{re.escape(field)}:\s*(.+)$", text, flags=re.MULTILINE
    )
    if not m:
        return None
    value = m.group(1).strip()
    # Strip surrounding quotes if present
    if value.startswith(("'", '"')) and value.endswith(value[0]):
        value = value[1:-1]
    return value


def _replace_fm_field(text: str, field: str, new_value: str) -> str:
    """Replace the value of a YAML front-matter scalar field."""
    return re.sub(
        rf"^({re.escape(field)}:\s*).*$",
        rf"\g<1>{new_value}",
        text,
        flags=re.MULTILINE,
    )


def build_reflection_text(
    template_text: str,
    reflection_id: str,
    ticket: str | None,
    goal: str | None,
    skill: str | None,
    outcome: str,
    duration_minutes: int,
    author: str,
    date_str: str,
) -> str:
    """Return the full content of a new reflection file.

    Replaces the front-matter placeholders in *template_text* with the
    provided values and updates the heading id.
    """
    text = template_text

    # Front-matter replacements
    text = _replace_fm_field(text, "id", reflection_id)
    text = _replace_fm_field(text, "date", date_str)
    text = _replace_fm_field(text, "author", author)
    text = _replace_fm_field(text, "ticket", ticket if ticket else "null")
    text = _replace_fm_field(text, "goal", goal if goal else "null")
    text = _replace_fm_field(text, "skill", skill if skill else "null")
    text = _replace_fm_field(
        text, "goal_met", outcome
    )
    text = _replace_fm_field(text, "duration_minutes", str(duration_minutes))

    # Update heading
    text = re.sub(
        r"^(# Reflection )R-NNN\s*$",
        rf"\g<1>{reflection_id}",
        text,
        flags=re.MULTILINE,
    )

    return text


def create_reflection(
    reflections_dir: pathlib.Path,
    ticket: str | None,
    goal: str | None,
    skill: str | None,
    outcome: str,
    duration_minutes: int,
    author: str,
) -> pathlib.Path:
    """Create the next R-NNN.md and return its path.

    Raises FileExistsError (via sys.exit) if a reflection for *ticket* already
    exists (idempotency guard).
    """
    template_path = reflections_dir / TEMPLATE_FILENAME
    if not template_path.is_file():
        raise FileNotFoundError(
            f"template not found at {template_path}"
        )

    template_text = template_path.read_text(encoding="utf-8")

    seq = next_reflection_number(reflections_dir)
    reflection_id = f"R-{seq:03d}"
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")

    content = build_reflection_text(
        template_text=template_text,
        reflection_id=reflection_id,
        ticket=ticket,
        goal=goal,
        skill=skill,
        outcome=outcome,
        duration_minutes=duration_minutes,
        author=author,
        date_str=date_str,
    )

    out_path = reflections_dir / f"{reflection_id}.md"
    out_path.write_text(content, encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="append_reflection.py",
        description=(
            "Create the next reflections/R-NNN.md skeleton from the template. "
            "Idempotent: if --ticket already has a reflection, exits 0 with warning."
        ),
    )
    parser.add_argument("--ticket", default=None, help="Associated AGENT-COLLAB.md ticket ID (e.g. T-002)")
    parser.add_argument("--goal", default=None, help="Associated goals/ goal ID (e.g. G-001)")
    parser.add_argument("--skill", default=None, help="Associated skill ID (e.g. summarize)")
    parser.add_argument(
        "--outcome",
        choices=list(OUTCOME_MAP.keys()),
        default="pass",
        help="Outcome of the task: pass | partial | fail  (default: pass)",
    )
    parser.add_argument(
        "--duration-minutes",
        type=int,
        default=0,
        dest="duration_minutes",
        help="Approximate task duration in minutes (default: 0)",
    )
    parser.add_argument(
        "--author",
        default="@Copilot",
        help="Author tag to write into the reflection front-matter (default: @Copilot)",
    )
    parser.add_argument(
        "--reflections-dir",
        default=None,
        dest="reflections_dir",
        help="Override the reflections directory (for testing)",
    )

    args = parser.parse_args(argv)

    reflections_dir = (
        pathlib.Path(args.reflections_dir)
        if args.reflections_dir
        else DEFAULT_REFLECTIONS_DIR
    )

    # Idempotency check
    if args.ticket:
        existing = find_existing_for_ticket(reflections_dir, args.ticket)
        if existing:
            print(
                f"WARNING: reflection for ticket {args.ticket} already exists at "
                f"{existing.name} — skipping.",
                file=sys.stderr,
            )
            return 0

    try:
        out_path = create_reflection(
            reflections_dir=reflections_dir,
            ticket=args.ticket,
            goal=args.goal,
            skill=args.skill,
            outcome=OUTCOME_MAP[args.outcome],
            duration_minutes=args.duration_minutes,
            author=args.author,
        )
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Created {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
