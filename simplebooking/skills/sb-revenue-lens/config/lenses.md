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

## L1 — Money-leak ("where am I leaving money on the table?")

**Input:** demand per week; availability calendar; prices on the dates of interest + 1 soft baseline.

**Rule — flag a night if at least one:**
- **L1a Last-room-at-flat-rate:** `tight` (max rooms available across all
  categories ≤ `tight_max_available`) **AND** nightly price ≤ period_median ×
  (1 + `premium_expected_min`). → scarcity not priced in.
- **L1b High-value orphan night:** a free night adjacent to a sold-out night
  (see R0/L3) in a high-demand week (top tercile). → an expensive night that
  becomes unsellable as part of a multi-night stay.
- **L1c High demand / I'm wide open & cheap:** top-tercile demand week **AND**
  high category coverage **AND** bottom-quartile price. → you could push the price.

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

**Output:** how much *matchable* demand is being turned away and where; for
L3a suggest opening a 1-night/orphan-night stay; for L3b **present it as a
TRADE-OFF, not an error**.

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

- **Area demand = destination, not property.** Two hotels 200m apart get
  identical demand numbers. Don't pass it off as the hotel's own demand.
- **"Available N"** is per category+rate, not house inventory.
- **Rate structure varies:** some hotels expose *Offers*, others expose *Rate
  Plans*. The detector reads the "cheapest" regardless of the structure.
- **Taxes/extras** (e.g. city tax per night) may not be included in the
  displayed price: don't add them by hand, just flag that they exist.
- **Current month:** start from today (past dates aren't queryable) and say so.
- **False-alarm check:** a healthy, well-priced hotel should produce few or
  zero flags. If a lens "fires" on everything, the threshold is wrong.
