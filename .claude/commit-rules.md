# Commit Rules

## Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```text
<type>(<scope>): <short description>

[optional body: explain why, not what]

[optional footer: issue references, breaking changes]
```

**Allowed types:** `feat`, `fix`, `refactor`, `docs`, `chore`

**Short description:** imperative, English, max 72 characters, no trailing period

**Body:** required if the change isn't self-explanatory; explain the *why*, not a file list

---

## Scope

| Scope | Area |
|-------|------|
| `plugin` | `plugin.json`, `marketplace.json`, `.mcp.json` |
| `skills` | Content under `simplebooking-tools/skills/` (normally released via `build-client-plugin.py` from the source repo, not hand-edited here) |
| `docs` | `README.md` |

---

## Granularity

Each commit is one release: a version bump plus the skill content it ships. Don't mix an
unrelated `plugin.json`/`README.md` edit into a release commit.

---

## Never commit

- Anything other than what `scripts/build-client-plugin.py` exported and the plugin/marketplace
  metadata — this repo has no source code of its own to diverge from that.
- Real hotel data (names, Property IDs). The source repo's skills are anonymized before
  export; if one ever isn't, fix it at the source, not here.

## Don't sign as AI

Don't add co-author lines, signatures, or references to Claude/Anthropic/AI tools in commit
messages. Don't use "claude" in branch names.

---

## Example

```text
feat(skills): release v0.2.0 — add sb-inventory-guard, fix demand-capture threshold

Exported from the internal skills repo via build-client-plugin.py.
```
