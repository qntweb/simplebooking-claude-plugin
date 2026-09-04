---
name: sb-hotel-content-audit
metadata:
  author: Sergio Farinelli
  organization: QNT — SimpleBooking — Zucchetti Group
description: >
  Structured audit of hotel content on the SimpleBooking platform. Checks
  missing translations, text quality, and information completeness across
  all enabled languages. Use when the user asks to check, audit, or verify
  content, translations, or localization of a hotel on SimpleBooking, or
  mentions "content audit". Trigger italiani: verifica traduzioni, controllo
  contenuti hotel, auditare i contenuti.
---

# 🏨 Hotel Content Audit — Skill for Claude Cowork

## Overview

This skill guides a structured audit of a hotel's content in the SimpleBooking
system (CRS). It checks missing translations, length thresholds, broken HTML,
and completeness across all enabled languages.

## Supporting files in this skill

Before starting, read these files in the order listed:

1. **config/hotels.md** — Hotel → SimpleBooking ID and GA4 ID reference table
2. **config/default.yaml** — Configurable parameters (thresholds, lookback, etc.)
3. **config/rules.md** — Mechanical classification rules (Rules 1→6)
4. **templates/report-full.md** — Report template for Sonnet/Opus
5. **templates/report-haiku.md** — Simplified report template for Haiku
6. **config/analytics.md** — Step 9 instructions (GA4 + Data Lake)

## Which template to use

- If you're running as **Haiku** or the `FORCE_MICRO_BATCH: true` parameter is
  set: use `templates/report-haiku.md` and follow the micro-batch rules.
- Otherwise: use `templates/report-full.md`.

If in doubt, ask the user: "Would you prefer a quick, concise audit
(checklist) or a full audit with qualitative suggestions?"

## Required MCP tools

- **SimpleBooking MCP** — REQUIRED. The workflow cannot start without it.
- **Google Analytics MCP** — Optional, auto-detected in Step 8.5
- **Zucchetti Travel Data Lake MCP** — Optional, auto-detected in Step 8.5

Do NOT ask the user whether they have the tools. Check silently (Step 8.5).

## Workflow — Step by Step

ALWAYS proceed in order. At each step, wait for the user's response.
Use the `ask_user_input_v0` tool when possible.

### STEP 1 — Conversation language
Ask for the language. Options: Italiano, English, Français, Deutsch, Español.
From here on, EVERYTHING in the chosen language.

### STEP 2 — Hotel selection
Ask for the hotel (name or ID). Use `config/hotels.md` to resolve it.
If not in the list → ask for the SimpleBooking Property ID.

### STEP 3 — Basic info + Master language + Audit languages
1. Call `property_get_basic_info` (conversation language)
2. Show: name, stars, city, enabled languages
3. Ask for **MASTER_LANGUAGE** (default: IT) — the source language the
   translations are derived from. All others are compared against this one.
4. Ask for **AUDIT_LANGUAGES**: all or a selection. Master is always included.
5. Also save **ALL_ENABLED_LANGUAGES** (needed for Step 9B)

### STEP 4 — Section selection
multi_select: Hotel Info, Room Types, Rate Plans, Offers, Packages,
Services, Meal Plans, Cancellation Policies, ALL.

### STEP 5 — Check type
single_select:
- 🔍 Missing translations only
- 📏 Formal check only (thresholds + HTML)
- ✨ Qualitative quality check (USP, tone — Sonnet/Opus only)
- 🔍📏 Translations + Formal (DEFAULT)
- 🔍📏✨ Everything (Sonnet/Opus only)

### STEP 6 — Detail level
single_select:
- ⚡ Quick — summary table + counts
- 📝 Detailed — table for every section, every field

### STEP 7 — Confirmation and start
Show a recap of the parameters. Ask for confirmation.
Then proceed with the API calls.

**API strategy:** For each section × language, call the appropriate tool.
Master language FIRST. Read `config/rules.md` for the classification rules.

Respect `MAX_API_CALLS_PER_BLOCK` (see config/default.yaml).
Show progress: "✅ [Section] completed ([N]/[TOTAL])"

### STEP 8 — Report generation
Use the appropriate template (full or haiku) from `templates/`.
Fill in every placeholder with the audit results.

### STEP 8.5 — MCP Probe (silent)
INVISIBLE to the user. Read `config/analytics.md` for details.
Try `get_account_summaries()` and `destination_get_report_options()`.
If they fail → skip Step 9. NEVER mention missing tools.

### STEP 9 — Smart next step
Only if at least 1 optional tool is available.
Read `config/analytics.md` for the full logic (9A Triage / 9B Opportunity).

### STEP 10 — Export
Sequential: one format at a time, then ask if another one is needed.
PDF → read /mnt/skills/public/pdf/SKILL.md
Excel → read /mnt/skills/public/xlsx/SKILL.md

## General rules

1. Step by step, never skip.
2. `ask_user_input_v0` for multiple-choice questions.
3. Step 1 language = the language for everything.
4. Issues on MASTER → highest priority (cascading impact).
5. Identity fields (addresses, phone numbers, emails, GPS, codes) → ⚪ not ⚠️.
6. NEVER mention unavailable tools.
7. Silent MCP probe.
8. Step 9 = a suggestion, never forced.
9. Sequential exports.
10. Hospitality tone in suggestions (Sonnet/Opus only).
