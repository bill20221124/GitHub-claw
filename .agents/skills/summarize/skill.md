# Skill: Summarize

## Purpose
Summarize any file, pull request, issue, or text block into a concise set of bullet points.

## When to Use
- User asks: "summarize this", "give me a TL;DR", "what does this file do?"
- You need to brief the owner on a long document before acting on it.
- Preparing a one-line entry for `MEMORY.md` Task Log.

## Inputs
- **target**: the file path, URL, PR number, or raw text to summarize.
- **max_bullets** *(optional, default 5)*: maximum number of bullet points to produce.

## Steps
1. Read or fetch the full content of `target`.
2. Identify the main topic, key decisions, and any action items.
3. Produce ≤ `max_bullets` bullet points, each ≤ 20 words.
4. If the target is a PR or issue, also note: status, author, and date.
5. Present the bullets to the user; do **not** add prose unless asked.

## Outputs
A markdown bullet list, e.g.:

```
- Adds `.agents/skills/` convention for project-level skill storage.
- Updates `AGENTS.md` with skill discovery and usage instructions.
- Introduces `validate-skills` workflow to enforce skill directory structure.
```
