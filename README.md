# SimpleBooking Claude Plugin

Claude skills for SimpleBooking hotel customers — reservation insights, revenue
analysis, content audit, and demand capture — built on the SimpleBooking IBE and
BackOffice MCP connectors.

## Install (Claude Desktop)

1. Open **Customize → Plugins → Add → Add marketplace**, and enter
   `qntweb/simplebooking-claude-plugin`.
2. Install the **simplebooking-tools** plugin. This adds the two SimpleBooking
   MCP connectors and four skills — sign in with your SimpleBooking account when
   prompted for the connectors.

## Update

When a new version is released, open **Customize → Plugins → Yours** and press
**Sync**. No need to re-download or re-upload anything.

## What's included

- **sb-reservation-insights** — pick-up, on the books, pace YoY, channel mix,
  commissions, cancellations, booking window, arrivals, markets, services,
  payments.
- **sb-revenue-lens** — demand-driven revenue diagnostic: money leaks, unsold
  risk, MinLOS restrictions, direct-vs-OTA parity.
- **sb-hotel-content-audit** — content and translation completeness audit
  across the SimpleBooking platform.
- **sb-demand-capture** — cross-checks area demand against actual reservations
  to tell whether a property is capturing the demand of its own destination.

## For maintainers — cutting a new release

Commit messages in this repo follow [.claude/commit-rules.md](.claude/commit-rules.md).

The skills are developed in the internal QNT `skills` monorepo, not here. To
publish an update:

1. In the `skills` repo, run:
   ```
   python scripts/build-client-plugin.py \
     --skills sb-reservation-insights sb-revenue-lens sb-hotel-content-audit sb-demand-capture \
     --plugin-dir /path/to/simplebooking-claude-plugin/simplebooking-tools
   ```
   Add `--worktree` if the latest changes aren't committed yet there.
2. Bump `version` in `simplebooking-tools/.claude-plugin/plugin.json` (semver).
3. Commit and push to this repo.
4. Tell pilot customers to press **Sync** in Claude Desktop.
