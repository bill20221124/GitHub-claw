#!/usr/bin/env python3
"""Append an audit row; enforce daily token budget.

Phases:
    --phase check    -> pre-flight; exits 78 (neutral) if today's token cap is hit
    --phase finish   -> post-run; records final status / tokens

The token cap comes from `policies/budget.md`'s `daily_tokens:` line. The "tokens
spent today" figure is recomputed each call by parsing the Tokens column of
`memory/audit/<UTC date>.md`.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import pathlib
import re
import sys


AUDIT_DIR = pathlib.Path("memory/audit")
BUDGET_FILE = pathlib.Path("policies/budget.md")
DEFAULT_DAILY_TOKENS = 200_000

HEADER = (
    "| Time | Phase | Skill | Status | Tokens | Run |\n"
    "|---|---|---|---|---|---|\n"
)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--phase", choices=["check", "finish"], required=True)
    ap.add_argument("--skill", required=True)
    ap.add_argument("--status", default="")
    ap.add_argument("--tokens", type=int, default=0)
    return ap.parse_args()


def today_log() -> pathlib.Path:
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    log = AUDIT_DIR / f"{today}.md"
    log.parent.mkdir(parents=True, exist_ok=True)
    if not log.exists():
        log.write_text(f"# Audit {today}\n\n{HEADER}", encoding="utf-8")
    return log


def daily_token_cap() -> int:
    if not BUDGET_FILE.is_file():
        return DEFAULT_DAILY_TOKENS
    m = re.search(r"^\s*daily_tokens:\s*(\d+)", BUDGET_FILE.read_text(), flags=re.M)
    return int(m.group(1)) if m else DEFAULT_DAILY_TOKENS


# Match the Tokens column inside an audit row. Rows look like:
#     | <time> | <phase> | <skill> | <status> | <tokens> | <run> |
ROW_RE = re.compile(
    r"^\|\s*[^|]+\|\s*[^|]+\|\s*[^|]+\|\s*[^|]+\|\s*(\d+)\s*\|", re.MULTILINE
)


def tokens_used_today(log: pathlib.Path) -> int:
    if not log.is_file():
        return 0
    return sum(int(x) for x in ROW_RE.findall(log.read_text(encoding="utf-8")))


def append_row(log: pathlib.Path, args: argparse.Namespace) -> None:
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    row = (
        f"| {timestamp} | {args.phase} | {args.skill} | "
        f"{args.status} | {args.tokens} | {run_id} |\n"
    )
    with log.open("a", encoding="utf-8") as f:
        f.write(row)


def main() -> int:
    args = parse_args()
    log = today_log()
    append_row(log, args)

    if args.phase == "check":
        cap = daily_token_cap()
        used = tokens_used_today(log)
        if used >= cap:
            print(f"Budget exceeded: {used}/{cap}", file=sys.stderr)
            # Re-record this as a budget-exceeded refusal row so the audit log
            # explains why the run did not proceed.
            stop = argparse.Namespace(
                phase="finish", skill=args.skill,
                status="budget-exceeded", tokens=0,
            )
            append_row(log, stop)
            return 78  # GitHub Actions "neutral"
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
