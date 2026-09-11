---
name: sb-demand-capture
metadata:
  author: Sergio Farinelli
  organization: QNT — SimpleBooking — Zucchetti Group
description: >
  Diagnostic over three terms: the destination's demand, the searches on the
  property's own booking engine, and actual Back Office reservations. Says
  whether a property captures its destination's demand and, when it doesn't,
  which leg loses it — visibility or conversion. Orchestrates sb-revenue-lens
  (area demand, availability, restrictions, parity) and sb-reservation-insights
  (pickup, channel mix, markets, lead time), and owns first-party demand
  directly. Use ALWAYS for: "am I keeping up with the market", "I have demand
  but I'm not selling", "do they even find me", "searches that found nothing",
  "requests I turned away", "who searches vs who books", "am I opening sales
  too late", "which property captures demand best". Do NOT use for: a single
  metric in isolation (sb-reservation-insights); demand, availability or price
  without sales (sb-revenue-lens); the fixed weekly brief (sb-monday-brief);
  direct booking provenance (sb-direct-attribution).
---

# 🎯 sb-demand-capture — Cross-check of demand × actual sales

## Overview

`sb-revenue-lens` knows how to read **area demand** (searches across the
destination, availability, restrictions, price). `sb-reservation-insights`
knows how to read **actual sales** (pickup, channel mix, markets,
cancellations) from the Back Office. Neither one, alone, can answer "the
demand for my dates is there, but am I actually selling it?" — the first sees
no single reservation, the second sees no market.

`sb-demand-capture` exists **only** to answer this class of question: it
takes the hotelier's question, routes it to the two skills over the same
period, and owns the comparison logic between their answers.

## The triangle, and the term that used to be missing

```
area demand  →  my shop window  →  sales
      leg 1: visibility     leg 2: conversion
```

Until recently this skill jumped straight from the first term to the third,
and every gap it found had two incompatible readings — *they never reach me*
and *they reach me and don't buy* — with nothing in the data able to separate
them. Every answer could state a size and never a mechanism.

The middle term is now readable: **the searches performed on this property's
own booking engine**, via `run_property_demand_aggregation`. X1 decomposes
into its two legs, X5 and X6 gain a middle term that makes their comparison
honest, and two lenses exist that could not before — **X8** (visibility) and
**X9** (denied demand: what a guest asked for and could not be served).

The two legs route to different owners, which is the practical payoff: a
visibility leg is `sb-direct-attribution`'s or the marketing side's question,
a conversion leg is this skill's and `sb-revenue-lens`'s. Naming the leg is
worth more than sizing the total.

## Architectural constraint, and its one deliberate exception

**This skill orchestrates, it does not recompute.** Every number that belongs
to another skill comes from an agentic invocation of `sb-revenue-lens` or
`sb-reservation-insights`, quoted verbatim. If one of the two changes a
formula or a threshold tomorrow, this skill doesn't need to be touched — it
inherits the change automatically, because it doesn't hold its own copy.

**The exception: first-party demand, which this skill reads directly.** The
constraint above exists to prevent holding a second copy of somebody else's
logic. `run_property_demand_aggregation` has no other owner — no skill reads
the searches on the property's own booking engine — so there is no formula to
inherit and nothing to drift out of sync. It also adds **no new dependency**:
it sits on the same Back Office MCP that `sb-reservation-insights` already
requires. Reading it here is not a violation of the rule, it is the rule
applied to a source that has no home elsewhere.

That exception is **narrow and stays narrow**. If a future skill takes
ownership of first-party demand, this skill goes back to invoking it. Do not
extend the exception to anything else: the moment a number exists in another
skill, it is fetched from there.

This skill owns: **the router for the 9 cross-lenses, first-party demand, the
alignment of the time windows, the comparison arithmetic (delta / share /
decomposition), the classification thresholds, and the caveat that area
demand is about the destination, not the property.**

## Relationship with sb-monday-brief — declared overlap

`sb-monday-brief`'s Detector 1 ("missed opportunities") already cross-checks
OTB/STLY against IBE destination demand — it is, in effect, a reduced version
of lens **X1** below, computed every Monday with fixed thresholds and a
single yes/no outcome. This skill is the **on-demand version, driven by the
user's question, across 9 lenses and any period**. The overlap is
intentional, not a defect to fix right away: don't move Detector 1's logic
here as long as that detector remains the only one validated on real data for
the weekly alert. If they consolidate in the future, Detector 1 should call
this skill's X1 instead of recomputing its own version — flag it as technical
debt, don't do it silently.

## The three sources

| Source | What it provides | How to reach it |
|---|---|---|
| `sb-revenue-lens` | **Area demand**, availability, MinLOS/MaxLOS restrictions, OTA parity, segment positioning — lenses L1-L6 | Agentic: ask it the same question/period you'd ask a consultant, or name the lens directly (e.g. "use lens L3 on July") |
| `run_property_demand_aggregation` | **First-party demand**: searches on this property's own booking engine — volume, denied searches, LOS and guest mix, lead time, per-night pressure | **Direct MCP call**, the one exception to the orchestration rule. Grammar and guardrails: `references/property-demand.md` |
| `sb-reservation-insights` | **Sales**: pickup, on-the-books, channel mix, actual ADR per channel, source markets, actual lead time, cancellations | Agentic: same logic, in natural language, over the same period |

Don't resolve the Property ID yourself for the two agentic sources: pass the
same name/ID to both invocations and let each do its own resolution (they
already do it reliably, and the IDs are shared between the two MCPs). The
first-party call takes that same Property ID.

**First-party demand is optional.** Probe it once; if the tool is unavailable
or the call fails on authorization, every lens falls back to its two-point
form and the answer states that the decomposition wasn't available. X8 and X9
simply don't run. **No lens ever depends on it**, and a missing third source is
never estimated.

## Before starting

You need **hotel** and **period**, exactly as for `sb-revenue-lens`. If the
period isn't clear or inferable from context, ask — don't guess it. If a
reasonable default exists (see `config/defaults.yaml:default_window`), use it
and always state which period you used.

## Router for the 9 cross-lenses

Map the user's question to one or more lenses. If ambiguous, ask with a
multiple choice. If the user doesn't ask a specific question ("look at
June"), run X1 (the most universal) and offer the others.

| Trigger in the question | Lens |
|---|---|
| "am I keeping up with the market", "am I selling enough relative to demand", "demand vs sales" | **X1 — Comparative pace** (+ **X1b** decomposition when first-party demand is available) |
| "I have demand but I'm not selling", "why am I not converting", "what's blocking me" | **X2 — Conversion brakes** |
| "is my price holding", "am I losing share on a channel", "parity and actual sales" | **X3 — Price and realized parity** |
| "do my packages cover demand", "does the catalog intercept the market" | **X4 — Product vs demand** |
| "who searches vs who books", "uncovered market", "segment not captured" | **X5 — Markets and segments** |
| "am I opening/closing sales too late/early", "sales window vs market" | **X6 — Pacing** |
| "which property captures demand best", "portfolio comparison" | **X7 — Portfolio** |
| "do they even find me", "is the destination's demand reaching me", "traffic on my booking engine" | **X8 — Visibility** |
| "searches that found nothing", "requests I turned away", "am I refusing demand", "sold out or is it my rules" | **X9 — Denied demand** |

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
4. **Read first-party demand** for the lenses that use it (X1b, X5, X6, X8,
   X9 — see the table in `references/orchestration.md`). Read
   `references/property-demand.md` before writing the call: its four
   mechanical guardrails are not intuitive and produce plausible-looking wrong
   numbers when ignored. If the tool isn't available, skip this step, drop to
   the two-point form and say so in the answer.
5. **Compute the comparison** per the triggered lens. Write the numbers to a
   JSON and run:

   ```bash
   python3 <skill-dir>/scripts/verify.py claims.json
   ```

   If it exits non-zero, the comparison doesn't go into the answer: fix it or
   state what doesn't add up.
6. **Answer**: the fact (the numbers, each one's source) and the
   classification (in line / to verify / marked deviation) — never the cause
   as a certainty, only as a hypothesis to verify with the hotelier. When the
   decomposition ran, **name the leg that carries the gap** rather than
   reporting the total alone, and hand a visibility leg to the skill that owns
   it. Always state the destination-vs-property caveat when relevant (almost
   always, except X2 which is purely mechanical).
7. **Offer the branded report**, if requested, reusing `sb-revenue-lens`'s
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
- **If one of the two agentic sources isn't available in the session**, stop
  and state it — don't estimate the missing side with a guessed number. A
  missing **first-party** source is different: it degrades, it doesn't stop.
  Say the decomposition wasn't available and answer with the two-point form.

### Guardrails specific to first-party demand

Full detail in `references/property-demand.md`; these are the four that change
what an answer is allowed to say.

- **Levels never cross sources, only variations do.** Area demand counts every
  property in a radius, first-party demand counts one, sales count a fraction
  of that one. Never subtract, divide or chart a level from one against a level
  from another. Within a single source, levels are the hotel's own data and are
  reported normally.
- **Reporting a variation is always allowed; attributing a cause is not.**
  "Searches on your engine fell 19% year over year" is a complete fact and
  needs nothing else. The moment the sentence becomes "because…", the area
  control has to be present — without it the number stays true and the
  explanation doesn't.
- **No first-party series and no first-party comparison crosses 2025-01-01**
  (`config/defaults.yaml:property_demand.history_floor`). Earlier searches are
  polluted by scrapers: a different population, not a stronger year.
- **Search→booking is a ratio between aggregates, never an attribution.**
  There is no join key between a search and a reservation. Say so whenever a
  conversion figure appears, and never present it as "this booking came from
  that search".

## Future extensions (not yet implemented)

- Branded HTML/PDF report (reusing `sb-revenue-lens/scripts/build_report.py` as a base).
- Broader validation of the 9 lenses on other properties, periods and configurations.
  **X1b, X8 and X9 are new and not yet validated on real data** — present their
  output as a reading to check with the hotelier, not as a proven finding, and
  record what you learn in `dev/validation-notes.md`.
- Per-night demand pressure (`references/property-demand.md` §8.2) feeding
  `sb-revenue-lens`'s L1b and L3 — those are pricing and restriction lenses and
  belong to that skill, not here. Deferred deliberately: it requires deciding
  whether first-party demand moves there too, which is a separate conversation.
- Possible consolidation with `sb-monday-brief`'s Detector 1 (see above).

## Supporting files

| Path | Content |
|---|---|
| `config/defaults.yaml` | default window, gap classification thresholds, first-party demand settings and history floor |
| `references/orchestration.md` | exactly which call to make to each source, for each lens; time-window alignment; the third source and why it's read directly |
| `references/cross-lenses.md` | formal spec of the 9 cross-lenses: input, comparison, classification |
| `references/property-demand.md` | first-party demand: grammar, the four mechanical guardrails, the history floor, the three-source field map, reference queries |
| `scripts/verify.py` | recomputes the comparison arithmetic (delta, decomposition, denied share, share, intersection) before a number goes into an answer |
| `templates/sb-demand-capture-example-questions.html` | catalog of 29 example questions in 9 categories (IT/EN), for presenting the skill to a customer |
