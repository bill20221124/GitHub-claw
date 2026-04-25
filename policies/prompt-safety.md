# Prompt Safety Policy

## Untrusted Inputs
Every piece of text that did NOT originate from this repository's committed files is untrusted:
issue bodies, issue comments, PR bodies, PR review comments, commit messages from forks,
webhook payloads, external API responses.

All untrusted text MUST be wrapped in `<untrusted>...</untrusted>` before being sent to the model.
See `prompts/skill-wrapper.md`.

## Red-Flag Phrases
If an untrusted input contains any of these (case-insensitive), the skill must refuse and escalate:

- "ignore previous instructions"
- "ignore all previous instructions"
- "disregard the system prompt"
- "you are now …" (role re-assignment)
- "reveal your system prompt"
- any command that asks to reveal secrets, push to main, force-push, delete branches,
  or disable safety rules

## Escalation
On refusal, `scripts/run_skill.py` writes a comment beginning with `/!\ refused: <reason>`
and exits 0 (so the workflow surfaces the refusal without failing). The audit row records
status `refused`.

## Maintainer Note
This file is the **human-readable** safety policy. The model-facing version is
`prompts/safety.md`. Keep the two consistent: when you add a rule here, mirror it there.
