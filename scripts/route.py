#!/usr/bin/env python3
"""Parse a GitHub event payload into (skill, args, proceed) for the dispatcher.

Reads:
    $GITHUB_EVENT_PATH (event JSON), `.agents/skills/` (skill whitelist).

Writes:
    Three lines to $GITHUB_OUTPUT:
        skill=<id-or-empty>
        args=<rest-of-line>
        proceed=true|false

Recognised commands (must appear at the very start of a comment / body line):
    /summarize [args]
    /plan <goal>
    /review
    /memory-write [hint]
    /skill <id> [args]    # generic escape hatch

Anything that isn't one of the above (or whose <id> isn't a real skill directory)
yields proceed=false, which the dispatcher reads as "ignore this event silently".
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import sys


SKILLS_DIR = pathlib.Path(".agents/skills")


def load_event() -> dict:
    path = os.environ.get("GITHUB_EVENT_PATH")
    if not path or not pathlib.Path(path).is_file():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def valid_skills() -> set[str]:
    if not SKILLS_DIR.is_dir():
        return set()
    return {
        p.name
        for p in SKILLS_DIR.iterdir()
        if p.is_dir() and not p.name.startswith("_") and (p / "skill.md").is_file()
    }


def event_body(event: dict) -> str:
    """Pull the most-relevant text field for slash-command parsing."""
    return (
        (event.get("comment") or {}).get("body")
        or (event.get("issue") or {}).get("body")
        or (event.get("pull_request") or {}).get("body")
        or ""
    )


# Match a command at the start of a line (allowing leading whitespace),
# then the rest of that line as args. We deliberately do NOT span newlines —
# slash commands are single-line, anything after is conversational.
COMMAND_RE = re.compile(r"^\s*/([A-Za-z][\w-]*)\b\s*(.*)$", re.MULTILINE)


def parse(text: str) -> tuple[str | None, str]:
    """Return (skill_id, args). skill_id is None when no command is found."""
    if not text:
        return None, ""
    m = COMMAND_RE.search(text)
    if not m:
        return None, ""
    cmd = m.group(1).lower()
    args = m.group(2).strip()
    if cmd == "skill":
        # `/skill <id> [args]` — pop the first token as the skill id.
        parts = args.split(None, 1)
        cmd = parts[0].lower() if parts else ""
        args = parts[1] if len(parts) > 1 else ""
    return cmd or None, args


def emit(skill: str, args: str, proceed: bool) -> None:
    out_path = os.environ.get("GITHUB_OUTPUT")
    line = f"skill={skill}\nargs={args}\nproceed={'true' if proceed else 'false'}\n"
    if out_path:
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(line)
    else:
        # Local dev convenience — print to stdout when not running in Actions.
        sys.stdout.write(line)


def main() -> int:
    event = load_event()
    skill, args = parse(event_body(event))
    skills = valid_skills()
    proceed = bool(skill) and skill in skills
    emit(skill or "", args, proceed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
