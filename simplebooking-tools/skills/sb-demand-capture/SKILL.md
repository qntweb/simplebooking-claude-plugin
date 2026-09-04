---
name: sb-demand-capture
metadata:
  author: Sergio Farinelli
  organization: QNT — SimpleBooking — Zucchetti Group
description: >
  Diagnostic that cross-references the booking engine's area demand with actual
  Back Office reservations: tells you whether a property is capturing its
  destination's demand or letting it go. Orchestrates sb-revenue-lens (demand,
  availability, restrictions, OTA parity) and sb-reservation-insights (pickup,
  channel mix, markets, actual lead time) over the same period, without
  recomputing their logic: it only owns the comparison between the two answers
  and the caveat that demand is about the destination, not the property. Use
  ALWAYS for: "am I keeping up with the market", "I have demand but I'm not
  selling", "does my catalog intercept demand", "who searches vs who books",
  "am I opening sales too late", "which property in the group captures demand
  best". Do NOT use for: a single real metric in isolation
  (sb-reservation-insights); demand/availability/price without actual sales
  (sb-revenue-lens); the fixed weekly brief (sb-monday-brief); direct booking
  provenance (sb-direct-attribution).
---

# 🎯 sb-demand-capture — Cross-check of demand × actual sales

## Overview

`sb-revenue-lens` knows how to read **market demand** (booking engine
searches, availability, restrictions, price). `sb-reservation-insights` knows
how to read **actual sales** (pickup, channel mix, markets, cancellations)
from the Back Office. Neither one, alone, can answer "the demand for my
dates is there, but am I actually selling it?" — the first sees no single
reservation, the second sees no market.

`sb-demand-capture` exists **only** to answer this class of question: it
takes the hotelier's question, routes it to both skills over the same
period, and owns **only** the comparison logic between the two answers.

## Non-negotiable architectural constraint (like sb-monday-brief)

**This skill orchestrates, it does not recompute.** It never calls an MCP
tool directly: every number comes from an agentic invocation of
`sb-revenue-lens` or `sb-reservation-insights`, quoted verbatim. If one of
the two changes a formula or a threshold tomorrow, this skill doesn't need
to be touched — it inherits the change automatically, because it doesn't
hold its own copy.

This skill owns only: **the router for the 7 cross-lenses, the alignment of
the time windows, the comparison arithmetic (delta/share), the gap
classification thresholds, and the destination-vs-property caveat.**

## Relationship with sb-monday-brief — declared overlap

`sb-monday-brief`'s Detector 1 ("missed opportunities") already cross-checks
OTB/STLY against IBE destination demand — it is, in effect, a reduced version
of lens **X1** below, computed every Monday with fixed thresholds and a
single yes/no outcome. This skill is the **on-demand version, driven by the
user's question, across 7 lenses and any period**. The overlap is
intentional, not a defect to fix right away: don't move Detector 1's logic
here as long as that detector remains the only one validated on real data for
the weekly alert. If they consolidate in the future, Detector 1 should call
this skill's X1 instead of recomputing its own version — flag it as technical
debt, don't do it silently.

## The two sources (never duplicated here)

| Source | What it provides | How to invoke it |
|---|---|---|
| `sb-revenue-lens` | Area demand, availability, MinLOS/MaxLOS restrictions, OTA parity, segment positioning — lenses L1-L6 | Agentic: ask it the same question/period you'd ask a consultant, or name the lens directly (e.g. "use lens L3 on July") |
| `sb-reservation-insights` | Pickup, on-the-books, channel mix, actual ADR per channel, source markets, actual lead time, cancellations — from the Back Office | Agentic: same logic, in natural language, over the same period |

Don't resolve the Property ID yourself: pass the same name/ID to both
invocations and let each do its own resolution (they already do it
reliably, and the IDs are shared between the two MCPs — no need for a third
resolution here).

## Before starting

You need **hotel** and **period**, exactly as for `sb-revenue-lens`. If the
period isn't clear or inferable from context, ask — don't guess it. If a
reasonable default exists (see `config/defaults.yaml:default_window`), use it
and always state which period you used.

## Router for the 7 cross-lenses

Map the user's question to one or more lenses. If ambiguous, ask with a
multiple choice. If the user doesn't ask a specific question ("look at
June"), run X1 (the most universal) and offer the others.

| Trigger in the question | Lens |
|---|---|
| "am I keeping up with the market", "am I selling enough relative to demand", "demand vs sales" | **X1 — Comparative pace** |
| "I have demand but I'm not selling", "why am I not converting", "what's blocking me" | **X2 — Conversion brakes** |
| "is my price holding", "am I losing share on a channel", "parity and actual sales" | **X3 — Price and realized parity** |
| "do my packages cover demand", "does the catalog intercept the market" | **X4 — Product vs demand** |
| "who searches vs who books", "uncovered market", "segment not captured" | **X5 — Markets and segments** |
| "am I opening/closing sales too late/early", "sales window vs market" | **X6 — Pacing** |
| "which property captures demand best", "portfolio comparison" | **X7 — Portfolio** |

Detail of each lens (input, comparison, classification): `references/cross-lenses.md`.
Exactly which call to make to each source, for each lens: `references/orchestration.md`.

## Workflow

1. **Identify hotel, period and lens** (router above).
2. **Invoke `sb-revenue-lens`** with the relevant question/lens over the
   period. Save the answer (including the evidence-table numbers) verbatim.
3. **Invoke `sb-reservation-insights`** with the equivalent question over the
   same period and, where possible, at the same granularity (weekly — see
   "Window alignment" in `references/orchestration.md`). Save the answer
   verbatim.
4. **Compute the comparison** per the triggered lens. Write the numbers to a
   JSON and run:

   ```bash
   python3 <skill-dir>/scripts/verify.py claims.json
   ```

   If it exits non-zero, the comparison doesn't go into the answer: fix it or
   state what doesn't add up.
5. **Answer**: the fact (the two numbers, each one's source) and the
   classification (in line / to verify / marked deviation) — never the cause
   as a certainty, only as a hypothesis to verify with the hotelier. Always
   state the destination-vs-property caveat when relevant (almost always,
   except X2 which is purely mechanical).
6. **Offer the branded report**, if requested, reusing `sb-revenue-lens`'s
   script as the layout base (don't write a new one from scratch) — a future
   extension, see below.

## Guardrails

- **Not prescriptive advice.** Like `sb-revenue-lens`: show the comparison and
  1-3 verification questions, not a "do X".
- **Cannibalization — same rule as `sb-monday-brief`.** "Would this guest have
  booked direct anyway?" isn't measurable here: never assert it.
- **The report goes to a customer.** In the multi-property comparison (X7),
  no data from other properties if the output is for a single hotel; the
  ranking is only for whoever manages the whole portfolio (same rule as
  `sb-monday-brief`).
- **Fact vs inference always kept distinct**, as in `sb-revenue-lens`.
- **If one of the two sources isn't available in the session**, stop and
  state it — don't estimate the missing side with a guessed number.

## Future extensions (not yet implemented)

- Branded HTML/PDF report (reusing `sb-revenue-lens/scripts/build_report.py` as a base).
- Broader validation of the 7 lenses on other properties, periods and configurations.
- Possible consolidation with `sb-monday-brief`'s Detector 1 (see above).

## Supporting files

| Path | Content |
|---|---|
| `config/defaults.yaml` | default window, gap classification thresholds |
| `references/orchestration.md` | exactly which call to make to each source, for each lens; time-window alignment |
| `references/cross-lenses.md` | formal spec of the 7 cross-lenses: input, comparison, classification |
| `scripts/verify.py` | recomputes the comparison arithmetic (delta, share, intersection) before a number goes into an answer |
| `templates/sb-demand-capture-example-questions.html` | catalog of 23 example questions in 7 categories, for presenting the skill to a customer |
