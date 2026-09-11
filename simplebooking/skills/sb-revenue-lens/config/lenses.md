# sb-revenue-lens — Formal detector specification

Each lens is **input → rule → output**. The model *narrates* the rule's
result; it does not invent the rule. All thresholds are in
`config/defaults.yaml` and are **relative** to the period/hotel.

---

## Cross-cutting rule R0 — Availability reconciliation (MANDATORY)

`availability_calendar` and `query_bookable_options` **don't always agree**,
and "no options" has three different causes to distinguish before concluding
anything:

1. **Genuinely sold out** — `Can Stay = No` in the calendar.
2. **Cut off by a restriction** — calendar says `Can Stay = Yes` but a
   multi-night `query` comes back empty because an internal night is
   MinLOS/sold-out (→ see L3 gap-night).
3. **Allocation mismatch** — no room for that guest composition.

Procedure: if a multi-night `query` comes back empty but the calendar shows
availability, **retry with 1 night** on each individual date in the range.
The night that fails alone is the blocker.

> Never trust the calendar alone: it can say "Can Stay: Yes" on nights that
> in practice break up a stay.

---

## Cross-cutting rule R2 — First-party demand pressure (Tier 2, OPTIONAL)

Available only with Back Office access (`run_property_demand_aggregation`).
**Every lens below is fully defined without it.** Where R2 appears, it sharpens
a rule that already works; it never gates one. If the tier is absent, skip
every R2 clause and run Tier 1 unchanged.

Grammar and mechanical guardrails: `references/property-demand.md`.

**Definitions.** For each night *n* in the period, from the per-night query:

- `searches_n` — searches whose stay covers *n*
- `avg_solutions_n` — average number of bookable solutions those searches found

```
unserved_night(n)  ⇔  avg_solutions_n ≤ unserved_solutions_max
                      AND searches_n ≥ min_searches_night
```

The volume floor is not optional: below it the average is computed on a handful
of searches and swings wildly.

`pressure_n` = tercile of `searches_n` **within the property's own series for
the period**. Never mixed with the area series — see the robustness note below.

**Three mechanical guardrails, all of them load-bearing:**

1. Read **only the buckets inside the filtered stay window**. The `StayDate`
   dimension ignores its own filter and returns the whole stay of every matched
   search; the tails outside the window are long stays, not demand for the
   period.
2. `StayDate` buckets are **not additive** — one search lands in every night it
   covers, so they sum to more than the search total. Never render them as
   shares or percentages.
3. `size` is ignored on calendar dimensions and zero-count buckets are emitted.
   Size the window upstream; never `Hour` beyond a few days.

---

## L1 — Money-leak ("where am I leaving money on the table?")

**Input:** demand per week; availability calendar; prices on the dates of interest + 1 soft baseline.

**Rule — flag a night if at least one:**
- **L1a Last-room-at-flat-rate:** `tight` (max rooms available across all
  categories ≤ `tight_max_available`) **AND** nightly price ≤ period_median ×
  (1 + `premium_expected_min`). → scarcity not priced in.
  *R2 confidence tier:* **confirmed** when `pressure_n` is top tercile on the
  property's own series; **to watch** when the area week is top tercile but
  `pressure_n` is bottom tercile — that combination is an acquisition problem
  wearing a pricing costume, and must be labelled as such rather than priced.
- **L1b High-value orphan night:** a free night adjacent to a sold-out night
  (see R0/L3) in a high-demand week (top tercile). → an expensive night that
  becomes unsellable as part of a multi-night stay.
  *R2 replaces the demand qualifier.* The week-level area tercile is a proxy:
  it says the destination was busy, never that anyone wanted **this** night.
  With R2 the rule reads the night itself — fires when the night is free,
  adjacent to a sold-out night, **AND** (`pressure_n` ≥ the period's median
  **OR** `unserved_night(n)`). An unserved night *is* the orphan mechanism
  observed from the guest's side instead of deduced from the calendar.
- **L1c High demand / I'm wide open & cheap:** top-tercile demand week **AND**
  high category coverage **AND** bottom-quartile price. → you could push the price.
  *R2 anti-flag, mandatory.* **Do not fire** if the week is bottom tercile on
  the property's own series while area demand is top tercile. Report instead,
  in one line, that the destination's demand isn't reaching the booking engine
  on those dates. Raising a price into an audience that isn't arriving is the
  wrong lever, and Tier 1 cannot tell this case apart from a genuine pricing
  opportunity — this is the class of false positive R2 exists to kill.

**Output:** list of nights ranked by estimated value, with the **type** (a/b/c)
and a verification question (never an order).

**Edge/control:** if the hotel is wide open but prices are already
weekend/weekday-differentiated, **don't** flag L1c — pricing is already
working. Avoid the false alarm.

---

## L2 — Unsold risk ("which dates risk going unsold?")

**Input:** demand per week + `daysAhead`; availability; sample price.

**Rule — flag a block of dates if ALL:**
- bottom-tercile area demand (or monotonically declining toward the end of the period);
- category coverage ≥ `wide_open_room_types_min`;
- bottom-quartile price;
- **inside/beyond** the booking window (`days_left < average_week_lead_time`).
  *R2:* prefer the average `DaysInAdvance` of **your own** searchers over the
  area `daysAhead` — same property, same engine, a far closer population. The
  area value stays the Tier-1 fallback; say which one you used.

**R2 anti-fire, mandatory.** If a block qualifies as `unserved_night` while the
calendar shows wide category coverage, **L2 must not fire**. Those are not soft
dates: guests asked and got nothing, which is R0's case 2 or 3 and routes to L3,
not to a discount. Firing L2 here would recommend lowering the price on nights
that are already turning demand away.

**Output:** soft dates + "how far behind you are on the cycle" + possible
levers (short offer, low MinLOS, package) as **options**, not prescriptions.

---

## L3 — Restrictions vs demand LOS ("are my own rules shutting me out?")

**Input:** demand `numberOfNights` (distribution); availability calendar (MinLOS + gap night via R0).

**Rule — two variants:**
- **L3a Gap-night:** a night exists with `Can Stay = Yes` that can't be sold
  as part of a 2-3 night stay because an adjacent night is sold out. Quantify
  the lost night (nightly price × number of orphan nights).
- **L3b MinLOS vs short-stay:** share of short-stay searches
  (≤ `short_stay_nights_max`) ≥ `short_stay_share_flag` **AND** MinLOS on those
  dates > `short_stay_nights_max`. → matchable demand is being turned away.

  *R2 changes the source of that share, and it is the biggest single upgrade in
  this file.* At Tier 1 the short-stay share comes from the **area** mix: it
  describes how the destination tends to book, not what you refused. At Tier 2
  it comes from the length-of-stay distribution of the searches **you actually
  turned away** (`NumberOfSolutions = 0`, `Nights` terms). "Two hundred refusals
  at three nights on these dates" is a different order of evidence from "this
  destination tends to book short".

  Quantify with `RoomNights` summed over the denied set, and label it
  **requested and not served** — **never "lost"**. There is no dedup key, so
  several searches by one guest inflate the figure, and "lost" reads to a
  hotelier as recoverable revenue that a rule change would hand back.

- **L3c Occupancy mismatch (R2 only — NEW).** R0 lists three causes for "no
  options" and the third, **allocation mismatch**, has never had a detector.
  Fires when denied searches concentrate on a single `NumberOfPersons` value
  above `denied_pax_concentration` **AND** the availability calendar shows
  rooms for other compositions on those dates. → the room occupancy setup, not
  capacity.

  This is the one case that looks identical to sold-out from every Tier-1 view,
  which is why nothing else in the toolchain finds it. Present it as a
  configuration question to verify with the hotelier — "you are turning away
  mostly parties of N while rooms for other compositions stay free on those
  dates" — never as a certainty, and never as a pricing signal.

**Output:** how much *matchable* demand is being turned away and where; for
L3a suggest opening a 1-night/orphan-night stay; for L3b **present it as a
TRADE-OFF, not an error**; for L3c a configuration check, not a rate action.

---

## L4 — OTA parity ("does my direct rate beat the OTAs?")

**Pre-condition:** `rate_match_enabled = true` (otherwise skip and say so).
**Input:** `query_bookable_options` → Query ID → `get_ota_prices` on key dates.
**Rule:** flag dates where an OTA is priced below direct.
**Output:** list of disparity dates with absolute/% gap.

---

## L5 — Runway / lead time ("how much time do I have to act?")

**Input:** demand `daysAhead` per period; calendar (days remaining).
**Rule:** `average_lead_time` vs `days_left` → urgency (act now / there's time / window closed).
**Output:** urgency level per block of dates.

---

## L6 — Demand positioning ("soft" lens, optional)

**Input:** demand `user.countryCode`, `guestType`, `numberOfKids`, `device`; room types/services/languages.
**Rule:** large demand from a market/segment vs misaligned content/rooms/languages.
**Output:** positioning gap. Explicitly qualitative.

---

## Robustness notes

- **Two demand series, never mixed.** *Area demand* is the destination: two
  hotels 200m apart get identical numbers, and it must never be passed off as
  the hotel's own demand. *First-party demand* (Tier 2) is genuinely the
  property's — but it counts one booking engine against a radius full of them,
  so the two are different populations by construction. Never put them on the
  same axis, never subtract one from the other, never compute a tercile across
  both. Where a rule compares them it compares **rates of change**; levels are
  read only within one series.
- **Tier 2 history floor: nothing crosses 2025-01-01.** Earlier searches are
  polluted by scrapers — a different population, not a stronger year. Rarely
  binding on a forward-looking run, binding the moment a baseline enters.
- **R0's third case now has a detector** (L3c), but only at Tier 2. At Tier 1
  an allocation mismatch still reads as sold-out: say so rather than guessing.
- **"Available N"** is per category+rate, not house inventory.
- **Rate structure varies:** some hotels expose *Offers*, others expose *Rate
  Plans*. The detector reads the "cheapest" regardless of the structure.
- **Taxes/extras** (e.g. city tax per night) may not be included in the
  displayed price: don't add them by hand, just flag that they exist.
- **Current month:** start from today (past dates aren't queryable) and say so.
- **False-alarm check:** a healthy, well-priced hotel should produce few or
  zero flags. If a lens "fires" on everything, the threshold is wrong.
