# The 7 cross-lenses — formal specification

Each lens: **two inputs (one per source) → comparison → classification →
narration**. The classification always uses the thresholds in
`config/defaults.yaml`, never an eyeballed judgment. If `scripts/verify.py`
doesn't confirm the calculation, the lens produces no output — it declares
"not reconciled" and lists the raw numbers exactly as they came from the two
sources.

## Two guardrails

1. **Minimum base (`min_gap_base_n`, default 20).** A small STLY base can
   produce a gap that's arithmetically correct but has no practical meaning.
   Always pass `sales_base_n` to `scripts/verify.py`: below the threshold,
   report the absolute counts alongside the percentage, never the percentage
   alone.
2. **Double basis, RoomNights and reservationsCount.** The two bases can
   classify the same week two different ways ("to verify" vs "marked
   deviation"). Always compute both and pass `other_basis_classification` to
   `scripts/verify.py`: if they disagree, report both, don't silently pick one.

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

## X7 — Portfolio

- **Input:** X1 (or the requested lens) repeated for each property in the group.
- **Comparison:** ranking of properties by `gap_pp` (or by the requested
  lens's metric).
- **Guardrail:** same rule as `sb-monday-brief` — if the output is for a
  single customer, no data from other properties named; the multi-property
  ranking is only for whoever manages the whole portfolio.
