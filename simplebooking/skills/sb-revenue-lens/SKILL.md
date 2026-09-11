---
name: sb-revenue-lens
metadata:
  author: Sergio Farinelli
  organization: QNT — SimpleBooking — Zucchetti Group
description: >
  Demand-driven revenue diagnostic for hotels, SimpleBooking MCP only. The
  user asks a question about a hotel+period and the skill cross-references
  area demand, availability, restrictions and prices: answer in chat, branded
  report on request. Use ALWAYS for: "where am I losing money", "unsold
  risk", "weak dates", "my restrictions", "MinLOS", "minimum stay", "direct
  vs OTA", "rate parity", "which dates do I still have rooms",
  "how much lead time do I have", "revenue opportunity", "money leak",
  "requests I turned away", "searches that found nothing",
  "period check", "analyze period X". Do NOT use for: events (sb-event-radar),
  AI traffic (sb-ai-traffic), content audit (sb-hotel-content-audit), site
  crawl (qnt-site-inspector), comparison with actual reservations
  (sb-demand-capture).
---

# 🔎 sb-revenue-lens — Demand-driven revenue diagnostic (SimpleBooking only)

## Overview

`sb-revenue-lens` answers **one question from the hotelier** about a period,
cross-referencing **area demand** (traveler searches across the destination,
via `property_destination_demands_run_report`) with the property's
**availability, restrictions and prices** — and, when the tier is available,
with **first-party demand**: the searches performed on this property's own
booking engine.

The second demand series is what turns several lenses from a proxy into a
measurement. Area demand says the destination was busy; it never says anyone
wanted *your* night. First-party demand does.

Unlike a report that dumps every metric, this skill is **intent-driven**: the
user thinks in terms of problems ("am I losing money?"), not metrics. An
internal router maps the question to one or more **lenses**, each of which is
a **deterministic detector** (a verifiable rule) plus a short narration.

**Founding constraint:** uses ONLY SimpleBooking MCPs. No Zucchetti Travel
Data Lake, no proprietary events source. → see §"What it CANNOT do".

**Two tiers, and the distinction matters for who can run this.**

| Tier | Server | Who has it |
|---|---|---|
| **Tier 1 — the whole skill** | SimpleBooking **IBE** MCP | anyone with booking-engine access: hoteliers, consultants, **external resellers** |
| **Tier 2 — first-party demand** | SimpleBooking **Back Office** MCP | whoever has a Back Office login **for that property** |

**Every lens is fully defined at Tier 1 and stays that way.** Tier 2 sharpens
some of them and adds one sub-lens; it is never required. Probe it once at the
start of a run; on a missing tool or an authorization failure, proceed silently
at Tier 1 and **state the degradation once** in the limits block — don't
mention the missing tool repeatedly, and never estimate what it would have
said.

A reseller without Back Office access therefore gets exactly the skill as it
was before this tier existed. Nothing they had was taken away.

Defaults to **chat** (fast first answer). Branded report **on request**.

## MCP Tools (all and only SimpleBooking)

### IBE MCP — required, Tier 1

- `booking_engine_search_properties` / `booking_engine_get_accessible_properties` — hotel resolution.
- `property_get_basic_info` — name, stars, city, languages, currency, **rate_match_enabled**, room types.
- `destination_get_report_options` — valid values for the demand report fields.
- `property_destination_demands_run_report` — **core engine**: area demand.
- `property_get_availability_calendar` — actual availability + restrictions (MinLOS/MaxLOS/CI/CO).
- `property_query_bookable_options` — prices, remaining rooms, LOS breakdown, Query ID for OTA.
- `property_get_ota_prices` — OTA parity (only for hotels with rate match).
- `property_get_room_types_list` / `property_get_services_list` — only for the "positioning" lens.
- `calendar_*` — date classification (weekends, national holidays, night counts). **Never** compute days of the week by hand.

### Back Office MCP — optional, Tier 2

- `run_property_demand_aggregation` — **first-party demand**: the searches
  performed on this property's own booking engine. Per-night pressure and
  average solutions found, denied searches (`NumberOfSolutions = 0`) with their
  length-of-stay and guest-composition breakdown, own lead time, own market and
  device mix.

  Grammar, the four mechanical guardrails and the reference queries:
  `references/property-demand.md`. **Read it before writing a call** — the
  guardrails are not intuitive and produce plausible-looking wrong numbers when
  ignored.

  **Note the name trap on the other side**: the Tier-1 demand tool is
  `property_destination_demands_run_report` (IBE). A tool named
  `destination_demands_run_report` also exists, belongs to the Zucchetti Data
  Lake, and is **out of bounds for this skill** — never reach for it.

## What it CANNOT do (always state this in the output)

The skill is an **area-demand vs my-availability/price diagnostic**, NOT an RMS. With the SB MCP alone it does **not** see:

- actual on-the-books figures or pickup pace (**neither** demand series is sales — one is the destination searching, the other is people searching *you*; a search is not a booking). For demand against actual sales, that's `sb-demand-capture`;
- real competitor rates (only OTA parity, and only if rate match is active);
- **an events source**: the skill detects patterns (sold-out, gap nights) but **does not attribute** the cause. See §Events.

At Tier 2 specifically, three more things it does **not** see:

- **the price the guest was shown.** First-party demand says how many solutions
  a searcher found, never at what price. "Did they leave because I was
  expensive?" is not answerable here;
- **which** offer or room was searched. `NumberOfOffers` and
  `NumberOfMealPlans` are counts, not identities;
- **any link between a search and a booking.** There is no join key, so a
  search-to-booking figure is a ratio between aggregates and never an
  attribution. This skill doesn't compute one at all — that is
  `sb-direct-attribution`'s and `sb-demand-capture`'s ground.

Anything that is inference must be labeled as such, distinct from facts.

## Input parameters

### Required
| Parameter | Type | Description |
|---|---|---|
| `hotel` | SB name or ID | Resolve known names via the mapping; if unknown ask for the Property ID. |
| `period` | flexible | E.g. "June", "Jun-Jul", "next 6 weeks", explicit range. |

### Optional
| Parameter | Default | Description |
|---|---|---|
| `question` | — | The question in natural language. If absent, see STEP 2 (router/ask). |
| `radius_km` | `12` urban / `25` extra-urban | Area demand radius. |
| `room_allocations` | `[{adults:2, children:[]}]` | Guest composition for price queries. |
| `output_mode` | `chat` | `chat` = first answer; `report` = branded PDF/HTML. |
| `language` | conversation language | Answer/report language. |
| `promo_code` | null | Promo code to test in price queries. |

## Two-pass architecture (cost/latency control)

`property_query_bookable_options` is **expensive**; `availability_calendar` and
the demand report are **cheap**. So:

1. **Light pass (always):** demand report (per week + 1-2 cuts) +
   availability calendar over the whole period, plus — at Tier 2 — two cheap
   Back Office aggregations (per-night pressure, denied searches). From this
   the detector identifies the **dates of interest** (sold-out, sold-out edges,
   weekends, last room, high-demand weeks, and at Tier 2 the *unserved* nights).

   First-party demand belongs in the light pass precisely because it is cheap
   and it **narrows** the expensive pass: a night where guests searched and
   found nothing is a date of interest identified without spending a single
   `query_bookable_options` call.
2. **Targeted pass (only where needed):** `query_bookable_options` ONLY on the
   dates of interest, not over the whole period. OTA parity
   (`get_ota_prices`) only in `report` mode and only if rate match is active.

## Intent router

Maps the user's question → lens(es). If ambiguous, ask with a multiple choice.
If the user doesn't ask a question ("analyze June"), run lenses L1+L2 (the
most universal) and offer the others.

| Trigger in the question | Lens |
|---|---|
| "where am I losing money", "money leak", "opportunity" | **L1 — Money-leak** |
| "unsold risk", "weak dates", "which dates do I still have rooms" | **L2 — Unsold risk** |
| "restrictions", "MinLOS", "minimum stay", "short stays" | **L3 — Restrictions vs LOS** |
| "direct vs OTA", "parity", "disparity" | **L4 — OTA parity** |
| "lead time", "how much time do I have", "runway", "urgency" | **L5 — Runway/lead time** |
| "where does demand come from", "families", "markets", "languages" | **L6 — Demand positioning** |
| "requests I turned away", "searches that found nothing", "am I refusing demand" | **L3c — Occupancy mismatch** (Tier 2; if absent, say the question isn't answerable without Back Office access) |

## The lenses (deterministic detectors)

Each lens: **input → rule → output**. The model *narrates* the rule's result;
it does not invent the rule.

### L1 — Money-leak ("where am I leaving money on the table?")
- **Input:** demand per week; availability calendar; prices on the dates of interest. *Tier 2:* per-night searches and average solutions found.
- **Rule — flag a date/night if:**
  - *Last-room-at-flat-rate:* few rooms remaining (e.g. ≤1-2 for the cheapest) **and** nightly price ≈ the period baseline (no premium despite scarcity).
  - *High-value orphan night:* a free night wedged between sold-out nights (see L3 for the mechanism detail) in a high-demand week. **At Tier 2 the demand qualifier moves from the week to the night itself** — see `config/lenses.md`.
  - *High demand / I'm wide open & cheap:* a week with area searches in the top quartile **but** wide availability and price in the bottom quartile. **At Tier 2 this acquires an anti-flag**: if area demand is high and first-party demand on the same week is low, the issue is that the market isn't reaching you, not your price. Report it as such and don't flag a pricing leak.
- **Output:** list of "leak" dates ranked by estimated value, with the **type** of loss and a verification question (not an order).

### L2 — Unsold risk ("which dates risk going unsold?")
- **Input:** demand per week + `daysAhead`; availability calendar; sample price.
- **Rule — flag if:** low/declining area demand **+** wide availability across many categories **+** already **inside/beyond** the period's average lead time (little runway left).
- **Output:** soft dates + "how far behind you are" on the booking cycle + possible levers (short offer, low MinLOS, package) as options, not prescriptions.

### L3 — Restrictions vs demand LOS ("are my own rules shutting me out?")
- **Input:** demand `numberOfNights` (distribution); availability calendar (MinLOS + gap nights).
- **Rule — flag if:**
  - demand is concentrated on 1-2 nights **but** MinLOS ≥3 is set on those dates; or
  - **gap nights** exist: a free night that can't be sold as part of a 2-3 night stay because an adjacent night is sold out (e.g. the 23rd is free but the 24th is full → a 23→25 search fails and the night of the 23rd is lost).
- **Output:** how much *matchable* demand is being turned away and on which nights; suggestion to open a 1-night/orphan-night stay.
- **Tier 2 — L3b measures what L3 infers.** The share of short-stay demand today comes from the *area* length-of-stay mix, which describes the destination's habits, not your refusals. With first-party demand you read the length-of-stay distribution of the requests **you actually turned away**. Quantify it in room-nights and label them **requested and not served** — never "lost": there is no dedup key, repeated searches by one guest inflate the figure, and "lost" reads as recoverable revenue.
- **Tier 2 — L3c, occupancy mismatch (new sub-lens).** The reconciliation rule R0 lists three causes for "no options": sold out, cut by a restriction, and **allocation mismatch** — and the third has never had a detector. Denied searches concentrated on one guest composition, while the calendar shows availability for others, *is* that detector. From the availability calendar this case is indistinguishable from sold-out, which is why nothing else in the toolchain finds it. Full rule in `config/lenses.md`.
- **Robustness note:** L3 is the most reliable lens because it's 100% mechanical and SB-only. **Always reconcile** `availability_calendar` (which can say "Can Stay: Yes") with a verification multi-night `query_bookable_options` call: in practice the calendar can say available while a 2-night query still fails. Don't trust the calendar alone.

### L4 — OTA parity ("does my direct rate beat the OTAs?")
- **Pre-condition:** `rate_match_enabled = true` (otherwise skip and say so).
- **Input:** `query_bookable_options` → Query ID → `get_ota_prices` on key dates.
- **Rule:** flag dates where an OTA is priced below direct.
- **Output:** list of disparity dates with absolute/% gap.

### L5 — Runway / lead time ("how much time do I have to act?")
- **Input:** demand `daysAhead` for the period; calendar (days remaining). *Tier 2:* prefer your **own** searchers' `DaysInAdvance` — same property, same engine, a far closer population than everyone searching the destination. Fall back to the area value when Tier 2 is absent, and say which one you used.
- **Rule:** compare the period's average lead time vs days remaining → urgency map (act now / there's time / window closed).
- **Output:** urgency level per block of dates.

### L6 — Demand positioning ("soft" lens, optional)
- **Input:** demand `user.countryCode`, `guestType`, `numberOfKids`, `device`; room types/services/languages. *Tier 2:* the same mix for **your own** searchers (`CustomerCountryCode`, `DeviceType`, `NumberOfKids`) — a segment strong in the area and absent from your own searches is a reach problem, not a content one, and the two-series version is the only way to tell. **Device needs a one-way fold**: the IBE report has `Tablet`, first-party demand does not — collapse IBE `Tablet` into Mobile before comparing, never the reverse.
- **Rule:** large demand from a market/segment (e.g. US, families) vs misaligned content/rooms/languages.
- **Output:** positioning gap on the booking engine. Explicitly qualitative, not a price calculation.

## Events — how to handle the gap without a demand data lake

The skill **has no events source**. Golden rule: **never claim** an event it
can't prove. In order of preference:

1. **Detect, don't attribute:** "June 24th is sold out and breaks 2-night stays" — 100% correct.
2. **Ask the hotelier:** "You're full on these dates: do you know of any events or fairs?" They know their calendar better than the model.
3. *(Optional, outside the SB MCP)* if the environment has web search, "best-effort" enrichment labeled as a **hypothesis**. Never a dependency, never presented as fact.

## Guardrails

- **Not prescriptive pricing advice.** Frame it as support: "3 things to check", options, not "do X". Remember the skill doesn't see costs, allotments, groups, contracts, or strategy.
- **Always show the evidence table** (dates, availability, price, demand). Transparency is the moat against black-box "AI revenue" tools.
- **"Available: N" ≠ house inventory.** It's N for that category at that rate. Don't cry scarcity.
- **Fact vs inference** always kept distinct in the text.
- **Past dates:** `query_bookable_options` doesn't accept the past; for the current month, start from today and say so.

### Tier 2 guardrails (first-party demand)

Full detail in `references/property-demand.md`; these four change what the
answer is allowed to say.

- **The two demand series are never mixed.** Area demand counts every property
  in a radius, first-party demand counts one. Never put them on the same axis,
  never subtract one from the other, never rank a night using a tercile
  computed across both. Where a lens compares them, it compares **rates of
  change**, never levels.
- **`StayDate` bleeds and doesn't add up.** Its buckets spread one search over
  every night of its stay, so they sum to more than the search total — never
  render them as shares — and the dimension ignores its own filter, so read
  **only the buckets inside the filtered window**. This is expected behaviour
  and will not be fixed.
- **`size` is ignored on calendar dimensions** and zero-count buckets are
  emitted. There is no way to cap the response downstream: size the window
  upstream, and never use `Hour` over more than a few days.
- **Nothing crosses 2025-01-01.** Earlier searches are polluted by scrapers —
  a different population, not a stronger year. It rarely bites a
  forward-looking run, but it binds the moment a baseline or a "vs last year"
  enters the answer.

## Output

### `chat` mode (default)
1. One summary line for the property.
2. The answer for the triggered lens (list of dates + signal type).
3. Compact evidence table.
4. 1-3 verification questions / options.
5. Offer: "want the branded report / the scheduled scan?"

### `report` mode (on request)
Generated with the included script, **not** by hand-writing HTML:

```
python scripts/build_report.py analysis.json -o report_<hotel>_<period>.html
```

The script (stdlib only, Chart.js from CDN) produces the approved layout:
SimpleBooking header, demand, summary, demand/LOS charts, per-lens signals
with evidence tables + callouts, calendar date map, limits block, events
space, options. Procedure: run the lenses → fill in a JSON per the schema in
`scripts/sample_hotel_d.json` → run the script → deliver the HTML (openable
in the browser, exportable to PDF).

Table cell color classes: `t-or` `t-gr` `t-red`. Calendar classes: `red`
(sold-out/MinLOS4), `or` (tight/MinLOS3), `y` (MinLOS2), `gr` (soft), `past`.

## Extensions
- **Multi-hotel batch** for consultants/resellers (portfolio scan).
- **Scheduling**: a morning scan that only alerts when a detector triggers
  (e.g. a weekend's last rooms below threshold, a new gap night).

## Supporting files
1. `config/defaults.yaml` — detector thresholds, known-hotel mapping, default radii.
2. `config/lenses.md` — formal spec of every detector (input, rule, edge case).
3. `references/property-demand.md` — Tier 2: first-party demand grammar, the four mechanical guardrails, the history floor, reference queries.
4. `templates/report-structure.md` — narrative structure of the report.
5. `scripts/build_report.py` — branded HTML generator (approved layout).
6. `scripts/sample_hotel_d.json` — full example input, runnable.
7. `examples/usage.md` — question → answer examples on 4 hotels (regression suite).
