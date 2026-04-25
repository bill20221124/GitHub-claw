#!/usr/bin/env python3
"""Invoke the LLM for the current skill and write the response to .agent-run/output.md.

This script:
    1. Loads prompts/system.md, prompts/safety.md, prompts/skill-wrapper.md.
    2. Loads .agents/skills/<id>/skill.md (active skill definition).
    3. Loads MEMORY.md as standing context.
    4. Reads $GITHUB_EVENT_PATH to extract the untrusted body (issue / PR / comment).
    5. Performs a red-flag scan (per policies/prompt-safety.md). On hit, refuses.
    6. Composes the final prompt via prompts/skill-wrapper.md ({format} substitution).
    7. Branches on skill model_tier:
         simple   -> GitHub Models (`gh models run`), free tier, default for Phase 1
         complex  -> Anthropic Claude API (only if ANTHROPIC_API_KEY is set)
       In Phase 1 both branches collapse to a single "echo prompt as a stub"
       implementation when no provider is configured, so the workflow remains
       runnable end-to-end without secrets.
    8. Writes the response to .agent-run/output.md.

Outputs are deliberately conservative: we never modify repository files from this
script. The dispatcher posts the response as an issue/PR comment.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import textwrap


REPO_ROOT = pathlib.Path(".")
RUN_DIR = REPO_ROOT / ".agent-run"
OUTPUT = RUN_DIR / "output.md"

PROMPTS = REPO_ROOT / "prompts"
SKILLS = REPO_ROOT / ".agents/skills"
POLICY_SAFETY = REPO_ROOT / "policies/prompt-safety.md"

# Red-flag phrases. Mirrored from policies/prompt-safety.md — keep in sync.
RED_FLAGS = (
    "ignore previous instructions",
    "ignore all previous instructions",
    "disregard the system prompt",
    "you are now",
    "reveal your system prompt",
    "force-push",
    "delete branches",
    "disable safety",
)


def read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def load_event() -> dict:
    path = os.environ.get("GITHUB_EVENT_PATH")
    if not path or not pathlib.Path(path).is_file():
        return {}
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def untrusted_body(event: dict, args: str) -> str:
    """Return the text we'll feed into the <untrusted> block."""
    body = (
        (event.get("comment") or {}).get("body")
        or (event.get("issue") or {}).get("body")
        or (event.get("pull_request") or {}).get("body")
        or ""
    )
    if args:
        # Surface args explicitly so the skill can see what the user typed
        # after the slash command without having to re-parse the body.
        body = f"args: {args}\n\n{body}"
    return body


def red_flag(text: str) -> str | None:
    haystack = text.lower()
    for phrase in RED_FLAGS:
        if phrase in haystack:
            return phrase
    return None


def memory_excerpt() -> str:
    """Return the section of MEMORY.md the model should see.

    We feed the whole file as long as it stays under ~6 KB; otherwise the head
    plus the Task Log tail (the two parts that change most). Phase 2 will swap
    this for proper retrieval.
    """
    mem = REPO_ROOT / "MEMORY.md"
    if not mem.is_file():
        return "(MEMORY.md not found)"
    text = mem.read_text(encoding="utf-8")
    if len(text) <= 6000:
        return text
    head = text[:3000]
    tail = text[-3000:]
    return f"{head}\n\n... [truncated middle] ...\n\n{tail}"


def model_tier(skill_text: str) -> str:
    m = re.search(r"^model_tier:\s*(\w+)", skill_text, flags=re.M)
    return (m.group(1).lower() if m else "simple")


def call_github_models(prompt: str) -> str:
    """Invoke `gh models run` if available; otherwise return a stub."""
    if not shutil.which("gh"):
        return _stub_response("gh CLI not available", prompt)
    try:
        proc = subprocess.run(
            ["gh", "models", "run", "openai/gpt-4o-mini", "--prompt", prompt],
            capture_output=True, text=True, timeout=120, check=False,
        )
    except subprocess.SubprocessError as e:
        return _stub_response(f"gh models error: {e}", prompt)
    if proc.returncode != 0:
        return _stub_response(
            f"gh models exit {proc.returncode}: {proc.stderr.strip()[:400]}", prompt
        )
    return proc.stdout.strip() or _stub_response("empty model response", prompt)


def call_anthropic(prompt: str) -> str:
    """Call the Anthropic API. Falls back to GitHub Models if key is missing."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return call_github_models(prompt)
    try:
        import urllib.request
    except ImportError:  # pragma: no cover
        return _stub_response("urllib unavailable", prompt)

    body = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 1500,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001 — surface any network failure as stub
        return _stub_response(f"anthropic error: {e}", prompt)

    parts = payload.get("content") or []
    text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
    return text.strip() or _stub_response("empty anthropic response", prompt)


def _stub_response(reason: str, prompt: str) -> str:
    """Deterministic fallback so the workflow always produces *some* output."""
    preview = textwrap.shorten(prompt.replace("\n", " "), width=400, placeholder=" …")
    return (
        f"_stub response (reason: {reason})_\n\n"
        f"The dispatcher composed a prompt but no LLM provider is configured.\n"
        f"Prompt preview: {preview}\n"
    )


def main() -> int:
    skill_id = os.environ.get("SKILL", "").strip()
    args = os.environ.get("ARGS", "").strip()
    if not skill_id:
        print("SKILL env var is required", file=sys.stderr)
        return 2

    skill_path = SKILLS / skill_id / "skill.md"
    if not skill_path.is_file():
        print(f"Unknown skill: {skill_id}", file=sys.stderr)
        return 2

    RUN_DIR.mkdir(exist_ok=True)

    system = read(PROMPTS / "system.md")
    safety = read(PROMPTS / "safety.md")
    wrapper = read(PROMPTS / "skill-wrapper.md")
    skill_text = read(skill_path)

    event = load_event()
    untrusted = untrusted_body(event, args)

    flagged = red_flag(untrusted)
    if flagged:
        OUTPUT.write_text(
            f"/!\\ refused: red-flag phrase detected ({flagged!r}). "
            f"See policies/prompt-safety.md.\n",
            encoding="utf-8",
        )
        return 0

    prompt = wrapper.format(
        system=system,
        safety=safety,
        skill=skill_text,
        memory_excerpt=memory_excerpt(),
        untrusted=untrusted,
    )

    tier = model_tier(skill_text)
    response = call_anthropic(prompt) if tier == "complex" else call_github_models(prompt)

    OUTPUT.write_text(response.rstrip() + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
