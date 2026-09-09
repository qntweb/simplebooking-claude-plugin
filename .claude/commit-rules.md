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
| `skills` | Content under `simplebooking/skills/` (generated for each release, not hand-edited here) |
| `docs` | `README.md` |

---

## Granularity

Each commit is one release: a version bump plus the skill content it ships. Don't mix an
unrelated `plugin.json`/`README.md` edit into a release commit.

---

## Never commit

- Anything other than the generated skill content and the plugin/marketplace
  metadata — this repo has no source code of its own to diverge from that.
- Real hotel data (names, Property IDs). Skills are anonymized before being
  published here; if one ever isn't, fix it before the next release, not here.

## Don't sign as AI

Don't add co-author lines, signatures, or references to Claude/Anthropic/AI tools in commit
messages. Don't use "claude" in branch names.

---

## Example

```text
feat(skills): release v0.2.0 — add sb-inventory-guard, fix demand-capture threshold
```
