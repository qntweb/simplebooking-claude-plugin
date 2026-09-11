# The 9 cross-lenses — formal specification

Each lens: **inputs from two or three sources → comparison → classification →
narration**. The classification always uses the thresholds in
`config/defaults.yaml`, never an eyeballed judgment. If `scripts/verify.py`
doesn't confirm the calculation, the lens produces no output — it declares
"not reconciled" and lists the raw numbers exactly as they came from the
sources.

## The third term, and what it changed

Until first-party demand existed, every lens ran between two points: **area
demand** and **sales**. A gap between them had two incompatible readings —
*they never reach me* and *they reach me and don't buy* — and nothing in the
data could tell them apart. Every classification was therefore a statement
about size, never about mechanism.

`run_property_demand_aggregation` supplies the middle term: the searches
performed on this property's own booking engine. See
`references/property-demand.md` for its grammar, its four mechanical
guardrails and the history floor — **read that file before writing any lens
that uses it.**

```
area demand  →  my shop window  →  sales
      leg 1: visibility     leg 2: conversion
```

X1 gains a decomposition into those two legs, X5 and X6 gain a middle term
that makes their comparison honest, and two lenses exist that could not
before: **X8** (visibility) and **X9** (denied demand).

**First-party demand is optional, not required.** If the source isn't
reachable in the session, every lens keeps its original two-point form and the
answer states that the decomposition wasn't available. No lens depends on it.

## Three guardrails

1. **Minimum base (`min_gap_base_n`, default 20).** A small STLY base can
   produce a gap that's arithmetically correct but has no practical meaning.
   Always pass `sales_base_n` to `scripts/verify.py`: below the threshold,
   report the absolute counts alongside the percentage, never the percentage
   alone.
2. **Double basis, RoomNights and reservationsCount.** The two bases can
   classify the same week two different ways ("to verify" vs "marked
   deviation"). Always compute both and pass `other_basis_classification` to
   `scripts/verify.py`: if they disagree, report both, don't silently pick one.
3. **Levels never cross sources; only variations do.** Area demand counts every
   property in a radius, first-party demand counts one, sales count a fraction
   of that one. The three are different populations by construction: a level
   from one is never subtracted from, divided by, or charted on the same axis
   as a level from another. **Every cross-source comparison in this file is
   between rates of change.** Within a single source, levels are the hotel's
   own data and are reported normally.

## X1 — Comparative pace

- **Input:** area demand for a window **this year** and for the same window
  **a year ago** (±364 days, same radius), from `sb-revenue-lens`; actual OTB
  for the window today and STLY (booked within the snapshot from a year ago
  minus canceled within that same snapshot) for the same window, from
  `sb-reservation-insights`. **Never** different weeks of the same snapshot
  looking forward in time — see the warning in `references/orchestration.md`:
  the demand count declines mechanically the further the stay week is from
  today, because of the demand report's fixed 91-day observation window.
  Comparing week N to week N+1 of the same snapshot mistakes this artifact
  for a market signal.
- **Comparison:** `gap_pp = delta_sales_pct_YoY - delta_demand_pct_YoY`.
- **Classification** (`gap_thresholds`): `|gap_pp| <= aligned_pp` → "in line
  with the market"; `aligned_pp < |gap_pp| <= notable_pp` → "to verify";
  beyond → "marked deviation" (state only that it exists, never the cause).
- **Note:** if demand and sales decline together YoY, it's likely
  seasonality/a weak year for the whole destination — say so before
  suggesting a property-specific problem. The interesting signal is when
  they **diverge**.

### X1b — Decomposition of the gap (when first-party demand is available)

The X1 gap answers *how much*. Adding the middle term answers *where*. Take
the YoY delta of first-party searches over the same window
(`delta_own_pct_YoY`, `SearchDate` basis) and split the total:

| Leg | Formula | What a negative value means |
|---|---|---|
| **Visibility** | `leg1_pp = delta_own_pct_YoY − delta_demand_pct_YoY` | the destination's demand is not reaching my booking engine as it used to — an acquisition problem |
| **Conversion** | `leg2_pp = delta_sales_pct_YoY − delta_own_pct_YoY` | they reach me and buy less — a product, price, availability or restriction problem |

The two legs sum to X1's total gap by construction; `scripts/verify.py`'s
`funnel` block re-derives them and refuses the decomposition if they don't.
Each leg is classified with the **same** `gap_thresholds` as X1.

**The two legs route to different places, and that is the point of the lens.**
A visibility leg is not this skill's to diagnose — hand it to
`sb-direct-attribution` (which source stopped delivering) or to the marketing
side. A conversion leg is X2, X8 and X9's territory. Say which leg carries the
gap; never present a total gap as a single explanation when the decomposition
is available.

**Guardrail — the attribution line.** Reporting the property's own variation is
always legitimate, with or without a comparison: *"searches on your engine fell
19% year over year"* is a complete fact. What requires the area series is
**attributing a cause**: the moment the sentence becomes *"because…"*, the
control has to be there. Without it the number stays true and the explanation
does not.

## X2 — Conversion brakes

- **Input:** the set of nights flagged by `sb-revenue-lens`'s L3 (MinLOS too
  strict relative to demand, gap night) and the set of actual nights with low
  sales/high cancellation from `sb-reservation-insights`, same period.
- **Comparison:** intersection of the two sets.
- **Output:** only nights present in **both** sets are a confirmed brake;
  nights present in only one remain a hypothesis, and must be stated as such,
  not presented as confirmed.
- **Correction to the lens:** count as a candidate "brake" only a night with
  an **explicit restriction code** in `Restrictions` (in particular
  `MinLOS N`), never a "Can Stay: No" night with empty `Restrictions` — an
  empty `Restrictions` column on a "No" night means sold-out, not a policy
  restriction, and sold-out is the opposite of the signal X2 looks for (full
  occupancy, not demand turned away by a rule).

## X3 — Price and realized parity

- **Input:** parity deviation per date/channel (`sb-revenue-lens`'s L4) and
  actual ADR per channel over a wider historical period
  (`sb-reservation-insights`).
- **Correct comparison — two facts side by side, not a subtraction.** A
  point-in-time price on ONE date and ONE room type (parity) and an average
  ADR over an entire quarter and multiple channels (realized) are numbers of
  different scope; subtracting them has no interpretable unit. **Report two
  distinct facts side by side instead**: (a) the live parity status on the
  sampled dates, (b) the realized ADR gap per channel over the historical
  period — leaving the job of connecting them to the narration, not the
  arithmetic.
- **Guardrail:** if `rate_match_enabled` is false on the booking-engine side,
  part (a) doesn't run — say so, don't estimate a deviation without the
  parity data.

## X4 — Product vs demand

- **Input:** peak-demand periods (top quartile, from L1/L2) cross-referenced
  with the presence of an active package/offer in that period (catalog, read
  from `sb-revenue-lens`) and with the actual sales of that package in the
  same period (`sb-reservation-insights`).
- **Output:** qualitative, two distinct signals not to confuse — "the
  catalog doesn't cover the peak" (no active package on those dates) is
  different from "the package is in the catalog but doesn't sell" (coverage
  exists, demand doesn't choose it).
- **Not yet tested:** if "peak demand" is read as the top quartile across
  consecutive weeks of the same forward-looking snapshot, it risks the same
  artifact as X1 (weeks closer to today mechanically have more accumulated
  demand — see `references/orchestration.md`). Prefer identifying seasonal
  peaks over a wide window with the same search_period for every week
  compared (e.g. a whole year, a single snapshot), not over a few consecutive
  weeks ahead of today.
- **Correction to the lens:** treat packages and offers as two populations of
  very different size, don't assume an empty catalog on one implies a
  problem — check which of the two concepts the property actually uses
  before reading "the catalog doesn't cover the peak" as a defect. The actual
  comparison against demand and actual sales remains untested.

## X5 — Markets and segments

- **Input:** % share of a `countryCode`/`guestType`/`device` in area demand
  (L6) and % share of the same segment in actual reservations, same period.
- **Comparison:** `demand_share_pct − sales_share_pct`, per segment.
- **Guardrail:** always state the coverage of the Back Office field (the
  actual source market isn't always populated — below `min_field_coverage`
  the lens abstains) before reading the comparison. The threshold alone isn't
  enough: even above the floor, always state the exact coverage number in the
  answer, not just when it's below threshold.

**Three-term version (when first-party demand is available).** Read the same
segment's share in *my* searches between the two existing terms:

```
share in area demand  →  share in my searches  →  share in my bookings
```

A market that is strong in the area and weak in my searches never arrives — a
reach problem. A market strong in my searches and weak in my bookings arrives
and doesn't convert — a product, price or content problem. The two-term version
cannot tell them apart, and would call both "uncovered market".

Field mapping via `references/property-demand.md` §7: `CustomerCountryCode`
here, `user.countryCode` on the area side, `CustomerCountryCode` on the sales
side. **Device needs the one-way fold**: the IBE report has `Tablet`, this tool
does not — collapse IBE `Tablet` into Mobile before comparing, never the
reverse. `guestType` has no first-party equivalent: that segment stays
two-term.

**`CustomerCountryCode` is filterable on the reservation side** (it was not in
older connector revisions, and older notes said otherwise): a single market's
ADR, lead time or revenue can be isolated rather than only read from a bucket.
The vocabulary is not normalised, so census the bucket values and filter with
`in` over every variant found, or the filter silently drops rows.

## X6 — Pacing

- **Root cause of the original problem — two different populations, not an
  arithmetic bug.** The demand's average `daysAhead` is the average over
  *all search events*: the vast majority is light traffic (browsing,
  comparing, price-checking) that's structurally close to the date. The
  actual `DaysInAdvance` is the average only of those who **actually
  booked** — a much smaller, more "planner" subset. The two averages measure
  populations that are different by nature: comparing them in absolute terms
  says nothing about THIS property's pacing, it only says how wide the
  market's funnel is.
- **Corrected with the same principle already used for X1: compare the YoY
  delta of each side, not the absolute value.** If the bias is stable over
  time, the YoY delta of each metric against itself cancels it out.
- **Input:** YoY delta % of the demand's average `daysAhead` (`sb-revenue-lens`'s
  L5, same window shifted by a year) and YoY delta % of the actual average
  `DaysInAdvance` (`sb-reservation-insights`, underlying `RegistrationDate`,
  same window), **only on already-concluded periods** — never on a future
  window, for the same reason `sb-reservation-insights` says "only redo this
  on already-concluded months" for booking lead time (censoring: short-term
  bookers of a future period haven't arrived yet).
- **Comparison:** `gap_pp = delta_sales_pct_YoY − delta_demand_pct_YoY`, same
  thresholds and same `scripts/verify.py` (`gap` block) as X1, **plus** the
  two optional fields `basis_ratio_a`/`basis_ratio_b` (the actual/demand
  ratio in each of the two years): if the ratio moves beyond
  `max_ratio_drift_pct` (default 15%), `verify.py` warns that the
  bias-stability assumption doesn't hold here, and the gap must be treated as
  a hypothesis to verify, not a confirmed reading.
- **Practical reading:** the YoY-delta method is the only valid correction to
  the original problem (the two populations remain incomparable in absolute
  terms, always), but it isn't infallible — always check
  `basis_ratio_a`/`basis_ratio_b` before presenting an X6 gap as a solid
  reading.

**First-party version — materially better, and the preferred one when
available.** X6's whole difficulty is that the two populations are strangers:
everyone searching the destination against the few who booked *here*. Swapping
the area side for first-party demand narrows that distance to **my searchers vs
my bookers** — same property, same booking engine, and the same field name
`DaysInAdvance` measured the same way on both sides (§7). The populations are
still not identical (a searcher is not a booker) so the **YoY-delta method
still applies** and the absolute values still must not be subtracted. But the
bias is far smaller and far more likely to be stable, which is exactly the
assumption the method rests on.

Keep computing `basis_ratio_a`/`basis_ratio_b` and passing them to
`scripts/verify.py`: the drift check is what tells you whether the assumption
held this time. When both versions are available, report the first-party one
and mention the area one only if the two disagree — a disagreement is itself
informative, since it means my searcher mix moved differently from the
market's.

## X7 — Portfolio

- **Input:** X1 (or the requested lens) repeated for each property in the group.
- **Comparison:** ranking of properties by `gap_pp` (or by the requested
  lens's metric).
- **Guardrail:** same rule as `sb-monday-brief` — if the output is for a
  single customer, no data from other properties named; the multi-property
  ranking is only for whoever manages the whole portfolio.

## X8 — Visibility: area demand vs my shop window

The first leg of X1b, promoted to a lens of its own because it answers a
question hoteliers ask directly: *"is the destination's demand reaching me at
all?"*

- **Input:** area demand for the window, this year and the same window a year
  ago (`sb-revenue-lens`, same radius on both sides); first-party searches over
  the same **stay** window, same two years, `SearchDate` basis — with both
  observation windows shifted together by 364 days.
- **Comparison:** `leg1_pp = delta_own_pct_YoY − delta_demand_pct_YoY`, the
  same arithmetic and the same `gap_thresholds` as X1.
- **Reading:** area up and mine flat or down means the destination grew without
  me. Both down together means the destination is softer and I am tracking it —
  state that before suggesting anything property-specific.
- **Output:** the fact, the classification, and **the handoff**. This skill does
  not diagnose acquisition: which source stopped delivering is
  `sb-direct-attribution`'s question, and the site's own health is
  `sb-website-audit`'s. Name the leg, hand it over, don't speculate here.
- **Guardrails:** history floor 2025-01-01 on both years of the first-party
  side; the attribution line from X1b — the variation is reportable on its own,
  the cause is not without the area control; levels never compared across the
  two sources, only their rates of change.

## X9 — Denied demand: what was asked for and could not be served

The lens with no two-term equivalent at all. `NumberOfSolutions = 0` is a guest
who set real parameters and was shown nothing — and the zero is clean, because
malformed searches, abandoned ones and impossible guest compositions never
enter the log (`references/property-demand.md` §1).

- **Input, first-party side:** denied searches over the window, and the same
  window unfiltered for the denominator; broken down by `CheckInDate` month or
  day, by `Nights`, and by `NumberOfPersons`; `RoomNights` summed over the
  denied set (query 8.1).
- **Input, sales side:** actual sales and occupancy over the same **stay**
  dates, from `sb-reservation-insights`; and, where the question is about
  restrictions, the nights `sb-revenue-lens`'s L3 flags with an explicit
  `MinLOS` code.
- **Comparison — the denied share, never the count.** `denied_pct = denied /
  total_searches` over the window, against the property's **own** baseline over
  the preceding comparable period. A raw count moves with traffic and says
  nothing.
- **Classification:** thresholds in `config/defaults.yaml:property_demand`
  (`denied_share_notable`, `denied_share_marked`), plus a minimum volume
  (`min_searches_window`) below which the lens abstains rather than reading a
  rate off a handful of searches.

**Three mechanisms, and the breakdown tells you which — this is the lens's real
output.** Never report the aggregate alone:

| Concentration in the breakdown | Mechanism | Where it goes |
|---|---|---|
| on specific check-in dates, with those dates sold out in `sb-reservation-insights` | genuine sold-out — demand exceeded capacity | not a defect; it's a pricing question (`sb-revenue-lens`) |
| on short stays, with `MinLOS` active on those dates | my own restriction refused the guest | X2, and `sb-revenue-lens` L3 |
| on one `NumberOfPersons` value while the calendar shows availability for others | **room occupancy configuration**, not capacity | the property's room setup — no other lens detects this |

That third row is the one nothing else in the toolchain finds: it looks like
sold-out in every other view.

- **Guardrails:** label the room-nights **requested and not served**, never
  "lost" — there is no dedup key, so repeated searches by one guest inflate the
  figure, and the phrasing must not imply recoverable revenue. Use
  `CheckInDate` for the breakdown, never `StayDate` (non-additive buckets, and
  the dimension ignores its own filter — §3). The denied *rate* is internal to
  the property's own funnel and needs **no** area control; only a statement
  about denied *volume* moving would.
