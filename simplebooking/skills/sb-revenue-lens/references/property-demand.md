# Tier 2 — first-party demand (`run_property_demand_aggregation`)

**Optional.** Every lens in this skill is fully defined without it. Read this file
before writing a call: the guardrails below are counter-intuitive and produce numbers
that look right and are wrong. Two were fixed by the team on 2026-09-17 (verified live) —
this file reflects the current state, not the 2026-09-11 baseline.

## What it is, and what it is not

Tier 1's demand (`property_destination_demands_run_report`, IBE) covers a radius around
the property: **the destination**. This tool covers **the property itself** — the
searches guests performed on its own booking engine.

That distinction is the point. Area demand says the destination was busy; it never says
anyone wanted *your* night. Several lenses in `config/lenses.md` used the area figure as
a stand-in for exactly that, and R2 replaces the stand-in with the measurement.

Neither series is sales. A search is not a booking, and there is no key linking one to
the other. For demand against actual reservations, that is `sb-demand-capture`.

> **Name trap.** `property_destination_demands_run_report` is the IBE tool this skill
> uses at Tier 1. `destination_demands_run_report`, almost identically named, belongs to
> the Zucchetti Data Lake and is **out of bounds** — it would break the founding
> constraint. Always write the IBE name in full.

## Access

Simple Booking **Back Office** MCP — a different server and a different authorization
from every Tier-1 tool. Probe once per run. On a missing tool or an auth failure, skip
every R2 clause, run Tier 1 unchanged, and state the degradation **once** in the limits
block. Never estimate what this tier would have said.

## What counts as a search

A guest set search parameters on the booking engine — from the site widget, from the
SimpleBooking calendar, or by landing on the IBE with dates and guests already filled in
from the query string. **One search per intent**: re-renders, pagination and filter
changes do not multiply it; a new search is recorded only when the dates or the guests
change.

**`NumberOfSolutions = 0` is a clean refusal.** Malformed searches, abandoned ones and
impossible guest compositions are rejected upstream and never enter the log. A zero means
there was genuinely no bookable combination for those parameters — which is what makes
L3b and L3c reportable to a hotelier.

`NumberOfSolutions > 0` means at least one room-type × rate-plan × meal-plan combination
was available and bookable.

## Grammar

Same request shape as the Back Office reservation tool; everything is top-level, with no
nested scope.

| Family | Facets this skill uses |
|---|---|
| Filters — date | `SearchDate`, `CheckInDate`, `StayDate` |
| Filters — numeric | `NumberOfSolutions`, `Nights`, `NumberOfPersons`, `RoomNights` |
| Dimensions — terms | `Nights`, `NumberOfPersons`, `NumberOfKids`, `CustomerCountryCode`, `DeviceType` |
| Dimensions — calendar | `StayDate` (per-night), `CheckInDate` (additive) |
| Measures | `NumberOfSolutions`, `RoomNights`, `DaysInAdvance`, `Nights` |

`NumberOfAdults` and `NumberOfKids` are **filterable** (fixed 2026-09-17; previously
dimensions and measures only) — see L3c below for what that unlocks.

> **Enum fallback.** This connector's published schema has lagged behind its validator.
> Don't probe it preemptively, but **if a call is rejected on a `facet`, the validation
> message lists the real enum**: read it and retry. That is the correct recovery and it
> keeps the skill working across connector changes.

## The four guardrails — two current, two fixed 2026-09-17

**1. `StayDate` buckets are not additive — still true.** The facet spreads one search
across every night of its stay, so a search covering two months lands in both buckets and
the column sums to more than the search total. Never render them as shares or
percentages. When you need one search in exactly one bucket — the denied-demand
breakdown, for instance — use `CheckInDate`.

**2. The `StayDate` dimension used to ignore the `StayDate` filter — fixed.** Until
2026-09-17 the filter picked the *search* while the dimension expanded *all* of that
search's nights, well outside the filtered range — declared by the team as expected and
permanent. It was fixed and verified live: the same query today returns buckets only
inside the filtered window. Guardrail 1 above still applies independently — buckets
inside the window can still overlap for stays spanning several of its nights.

**3. `size` used to be ignored on `calendar` dimensions — fixed.** Date histograms in
Elasticsearch 6.4.2 didn't support it, so zero-count buckets were emitted regardless of
`size`. Verified fixed on both this tool and `run_reservation_aggregation`: `size` is now
respected. Sizing the window upstream is no longer the only defense against a runaway
`Hour` grouping, though it remains good practice.

**4. Nothing crosses 2025-01-01 — unaffected.** Bot and scraping protection rolled out
gradually through 2024 and the series falls by roughly a factor of three across it — a
ramp, not a step, so there is no clean earlier anchor. Earlier searches are a different
population, not a stronger year. (`config/defaults.yaml:property_demand.history_floor`.)

## The two queries

### Per-night pressure — feeds R2, L1a, L1b, L2

```json
{ "request": {
  "propertyIds": [ "<PROPERTY_ID>" ],
  "filters": { "date": [ { "facet": "SearchDate", "greaterOrEqualThan": "<SEARCH_FROM>" },
                         { "facet": "StayDate", "between": { "from": "<PERIOD_FROM>", "to": "<PERIOD_TO>" } } ] },
  "dimensions": [
    { "name": "night", "calendar": { "facet": "StayDate", "interval": "Day" }, "sort": "ByKeyAscending",
      "metrics": [ { "name": "searches", "searchesCount": true },
                   { "name": "avg_solutions", "measure": "NumberOfSolutions", "statistic": "Average" } ] } ] } }
```

Buckets stay inside `<PERIOD_FROM>`..`<PERIOD_TO>` on their own now (guardrail 2, fixed).
Guardrail 1's non-additivity still applies — a stay spanning several nights in the window
is counted once per night, so read a profile, not a share. A night with `searches ≥
min_searches_night` and `avg_solutions ≤ unserved_solutions_max` is an **unserved
night** — the orphan-night mechanism observed from the guest's side rather than inferred
from the calendar.

### Denied demand — feeds L3b and L3c

```json
{ "request": {
  "propertyIds": [ "<PROPERTY_ID>" ],
  "filters": { "date":    [ { "facet": "SearchDate", "greaterOrEqualThan": "<SEARCH_FROM>" },
                            { "facet": "CheckInDate", "between": { "from": "<PERIOD_FROM>", "to": "<PERIOD_TO>" } } ],
               "numeric": [ { "facet": "NumberOfSolutions", "equalTo": 0 } ] },
  "metrics": [ { "name": "denied", "searchesCount": true },
               { "name": "room_nights", "measure": "RoomNights", "statistic": "Sum" } ],
  "dimensions": [
    { "name": "denied_los",  "terms": { "facet": "Nights" },          "size": 12 },
    { "name": "denied_pax",  "terms": { "facet": "NumberOfPersons" }, "size": 10 },
    { "name": "denied_date", "calendar": { "facet": "CheckInDate", "interval": "Day" }, "sort": "ByKeyAscending" } ] } }
```

`CheckInDate`, not `StayDate`: additive buckets are required (guardrail 1). Run the same
window without the `NumberOfSolutions` clause for the denominator — the denied **share**
is the readable figure; the raw count moves with traffic.

**Label the room-nights "requested and not served", never "lost".** There is no dedup
key, so several searches by one guest inflate the figure, and "lost" reads to a hotelier
as revenue a rule change would hand back.

### Occupancy mismatch, isolated directly — feeds L3c (fix 2026-09-17)

```json
{ "request": {
  "propertyIds": [ "<PROPERTY_ID>" ],
  "filters": { "date":    [ { "facet": "SearchDate", "greaterOrEqualThan": "<SEARCH_FROM>" },
                            { "facet": "CheckInDate", "between": { "from": "<PERIOD_FROM>", "to": "<PERIOD_TO>" } } ],
               "numeric": [ { "facet": "NumberOfSolutions", "equalTo": 0 },
                            { "facet": "NumberOfKids", "greaterOrEqualThan": 1 } ] },
  "metrics": [ { "name": "denied_family", "searchesCount": true } ] } }
```

Before the fix, L3c inferred a family/occupancy mismatch from the `NumberOfPersons` and
`NumberOfKids` buckets of the plain denied-demand query. Now `NumberOfKids` filters
directly: this isolates denied family demand from denied demand generally, without
reading it out of a bucket. Use it to confirm a mismatch already suggested by
`denied_pax`, not as the sole trigger — the bucket-level read remains valid and this adds
precision, it does not replace the query above.

## What this tier cannot do

- **No price.** How many solutions a guest saw, never at what price. "Did they leave
  because I was expensive?" stays unanswerable.
- **No product identity.** `NumberOfOffers` and `NumberOfMealPlans` are counts, not names.
- **No link to a booking.** No join key exists. This skill computes no search-to-booking
  ratio at all — that is `sb-direct-attribution`'s and `sb-demand-capture`'s ground.
- **One `distinctCountOf` per request**, and this skill needs none of them.
