#!/usr/bin/env python3
"""
Goal Stack CLI — scripts/goal_stack.py

Provides four subcommands for managing goals/G-NNN.md files:
  list                          List all G-NNN.md (id / title / status / priority / owner / updated)
  show <id>                     Print full content of a goal (front-matter + body)
  advance <id> "<one-line>"     Append a line to Last advanced (date + GOAL_AUTHOR env)
  set-status <id> <new-status>  Change status field; enforces state machine from goals/README.md §4

Constraints (T-001):
  - No new pip dependencies (stdlib only, with optional PyYAML fallback)
  - Pure functional style: each subcommand is an independent function; main() only routes
  - No LLM calls

Usage:
  python scripts/goal_stack.py --help
  python scripts/goal_stack.py list
  python scripts/goal_stack.py show G-001
  GOAL_AUTHOR=Copilot python scripts/goal_stack.py advance G-001 "implemented feature X"
  python scripts/goal_stack.py set-status G-001 done
"""

import argparse
import os
import re
import sys
from datetime import date

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_GOALS_DIR = os.path.normpath(os.path.join(_SCRIPT_DIR, '..', 'goals'))

# State machine from goals/README.md §4
# Maps current_status → set of allowed next statuses
VALID_TRANSITIONS = {
    'backlog':     {'in-progress'},
    'in-progress': {'done', 'blocked'},
    'blocked':     {'in-progress', 'abandoned'},
    'done':        set(),       # terminal
    'abandoned':   set(),       # terminal
}

GOAL_FILE_PATTERN = re.compile(r'^G-\d+\.md$')

# ---------------------------------------------------------------------------
# Front-matter parsing helpers (no external deps required)
# ---------------------------------------------------------------------------

def _parse_fm_with_regex(fm_text):
    """Minimal YAML parser for the simple key: value pairs used in goals."""
    result = {}
    for line in fm_text.splitlines():
        if ':' not in line:
            continue
        key, _, value = line.partition(':')
        key = key.strip()
        value = value.strip()
        if value.startswith('[') and value.endswith(']'):
            inner = value[1:-1]
            result[key] = [x.strip() for x in inner.split(',') if x.strip()]
        else:
            result[key] = value
    return result


def parse_front_matter(text):
    """Parse YAML front-matter block from markdown text.

    Returns (fm_dict, body_text).  Falls back to regex parser when PyYAML is
    not available so the script has zero required dependencies.
    """
    match = re.match(r'^---\n(.*?)\n---\n(.*)', text, re.DOTALL)
    if not match:
        return {}, text
    fm_text, body = match.group(1), match.group(2)
    try:
        import yaml  # noqa: PLC0415
        fm = yaml.safe_load(fm_text) or {}
    except ImportError:
        fm = _parse_fm_with_regex(fm_text)
    return fm, body


def update_front_matter_field(text, field, new_value):
    """Return *text* with *field* in the YAML front-matter replaced by *new_value*.

    Only the first occurrence inside the opening ``---`` block is modified.
    """
    fm_match = re.match(r'^(---\n)(.*?)(\n---\n)(.*)', text, re.DOTALL)
    if not fm_match:
        return text
    prefix, fm_text, separator, body = fm_match.groups()
    pattern = re.compile(rf'^({re.escape(field)}:\s*).*$', re.MULTILINE)
    new_fm = pattern.sub(rf'\g<1>{new_value}', fm_text, count=1)
    return prefix + new_fm + separator + body

# ---------------------------------------------------------------------------
# File-level helpers
# ---------------------------------------------------------------------------

def find_goal_file(goals_dir, goal_id):
    """Return the absolute path to *goal_id*.md, or exit(1) if not found."""
    goal_id = goal_id.upper()
    path = os.path.join(goals_dir, f'{goal_id}.md')
    if not os.path.isfile(path):
        print(f"error: goal '{goal_id}' not found (expected {path})", file=sys.stderr)
        sys.exit(1)
    return path


def _all_goal_files(goals_dir):
    """Return sorted list of G-NNN.md filenames in *goals_dir*."""
    try:
        entries = os.listdir(goals_dir)
    except FileNotFoundError:
        return []
    return sorted(f for f in entries if GOAL_FILE_PATTERN.match(f))

# ---------------------------------------------------------------------------
# Subcommand implementations (pure functions; each accepts goals_dir)
# ---------------------------------------------------------------------------

def list_goals(goals_dir):
    """Print a table of all goals with key fields."""
    files = _all_goal_files(goals_dir)
    if not files:
        print("(no goals found)")
        return

    rows = []
    for filename in files:
        path = os.path.join(goals_dir, filename)
        with open(path, encoding='utf-8') as fh:
            fm, _ = parse_front_matter(fh.read())
        rows.append({
            'id':       fm.get('id', filename[:-3]),
            'status':   fm.get('status', '?'),
            'priority': fm.get('priority', '?'),
            'owner':    str(fm.get('owner', '?')),
            'updated':  str(fm.get('updated', '?')),
            'title':    fm.get('title', '(no title)'),
        })

    col_id       = max(len(r['id'])       for r in rows) + 2
    col_status   = max(len(r['status'])   for r in rows) + 2
    col_priority = max(len(r['priority']) for r in rows) + 2
    col_owner    = max(len(r['owner'])    for r in rows) + 2
    col_updated  = max(len(r['updated'])  for r in rows) + 2

    header = (
        f"{'ID':<{col_id}}"
        f"{'STATUS':<{col_status}}"
        f"{'PRIO':<{col_priority}}"
        f"{'OWNER':<{col_owner}}"
        f"{'UPDATED':<{col_updated}}"
        f"TITLE"
    )
    print(header)
    print('-' * len(header))
    for r in rows:
        print(
            f"{r['id']:<{col_id}}"
            f"{r['status']:<{col_status}}"
            f"{r['priority']:<{col_priority}}"
            f"{r['owner']:<{col_owner}}"
            f"{r['updated']:<{col_updated}}"
            f"{r['title']}"
        )


def show_goal(goals_dir, goal_id):
    """Print the full content of a goal file."""
    path = find_goal_file(goals_dir, goal_id)
    with open(path, encoding='utf-8') as fh:
        print(fh.read(), end='')


def advance_goal(goals_dir, goal_id, message, author=None):
    """Append one line to the *Last advanced* section of *goal_id*.

    The author is read from the *GOAL_AUTHOR* environment variable when not
    supplied explicitly.  The ``updated`` front-matter field is also refreshed.
    """
    if author is None:
        author = os.environ.get('GOAL_AUTHOR', 'unknown')
    # Normalize: strip any leading '@' so the output format is always "by @<name>"
    author = author.lstrip('@')

    path = find_goal_file(goals_dir, goal_id)
    with open(path, encoding='utf-8') as fh:
        text = fh.read()

    if '## Last advanced' not in text:
        print("error: '## Last advanced' section not found in goal file", file=sys.stderr)
        sys.exit(1)

    today = date.today().isoformat()
    new_line = f"- {today} by @{author}: {message}\n"

    # Insert the new line immediately after the section header
    new_text = re.sub(
        r'(## Last advanced\n)',
        rf'\1{new_line}',
        text,
        count=1,
    )
    new_text = update_front_matter_field(new_text, 'updated', today)

    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(new_text)

    print(f"advanced {goal_id}: {new_line.strip()}")


def set_status(goals_dir, goal_id, new_status):
    """Change the *status* field of *goal_id*, enforcing the state machine.

    Illegal transitions cause a non-zero exit so callers can detect failures.
    """
    if new_status not in VALID_TRANSITIONS:
        valid = ', '.join(sorted(VALID_TRANSITIONS))
        print(
            f"error: unknown status '{new_status}'. valid values: {valid}",
            file=sys.stderr,
        )
        sys.exit(1)

    path = find_goal_file(goals_dir, goal_id)
    with open(path, encoding='utf-8') as fh:
        text = fh.read()

    fm, _ = parse_front_matter(text)
    current_status = fm.get('status', '')

    if current_status == new_status:
        print(f"{goal_id} is already '{new_status}'")
        return

    allowed = VALID_TRANSITIONS.get(current_status, set())
    if new_status not in allowed:
        if not allowed:
            reason = f"'{current_status}' is a terminal state; no further transitions allowed"
        else:
            reason = f"allowed from '{current_status}': {sorted(allowed)}"
        print(
            f"error: illegal transition '{current_status}' → '{new_status}'. {reason}",
            file=sys.stderr,
        )
        sys.exit(1)

    today = date.today().isoformat()
    new_text = update_front_matter_field(text, 'status', new_status)
    new_text = update_front_matter_field(new_text, 'updated', today)

    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(new_text)

    print(f"{goal_id}: status '{current_status}' → '{new_status}'")

# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        prog='goal_stack.py',
        description='Goal Stack CLI — manage goals/G-NNN.md files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python scripts/goal_stack.py list
  python scripts/goal_stack.py show G-001
  GOAL_AUTHOR=Copilot python scripts/goal_stack.py advance G-001 "implemented X"
  python scripts/goal_stack.py set-status G-001 done
        """,
    )
    parser.add_argument(
        '--goals-dir',
        default=DEFAULT_GOALS_DIR,
        metavar='DIR',
        help=f'directory containing G-NNN.md files (default: {DEFAULT_GOALS_DIR})',
    )

    subparsers = parser.add_subparsers(dest='command', metavar='COMMAND')
    subparsers.required = True

    # list
    subparsers.add_parser('list', help='list all goals')

    # show
    show_p = subparsers.add_parser('show', help='print full content of a goal')
    show_p.add_argument('id', help='goal ID, e.g. G-001')

    # advance
    adv_p = subparsers.add_parser('advance', help='append a line to Last advanced')
    adv_p.add_argument('id', help='goal ID')
    adv_p.add_argument('message', help='one-line progress note')

    # set-status
    ss_p = subparsers.add_parser('set-status', help='change goal status')
    ss_p.add_argument('id', help='goal ID')
    ss_p.add_argument(
        'status',
        choices=list(VALID_TRANSITIONS.keys()),
        help='new status value',
    )

    args = parser.parse_args(argv)
    goals_dir = os.path.abspath(args.goals_dir)

    if args.command == 'list':
        list_goals(goals_dir)
    elif args.command == 'show':
        show_goal(goals_dir, args.id)
    elif args.command == 'advance':
        advance_goal(goals_dir, args.id, args.message)
    elif args.command == 'set-status':
        set_status(goals_dir, args.id, args.status)


if __name__ == '__main__':
    main()
