# Orchestration — which source to call for each cross-lens

Every cross-lens (X1-X7) combines **one answer from `sb-revenue-lens`** and
**one answer from `sb-reservation-insights`** over the same period and,
where possible, at the same granularity. Never call an MCP tool directly
from this skill: `sb-demand-capture`'s value is in the comparison, not in
data access. If one of the two skills isn't available in the session, stop
and state it — don't estimate the missing side.

## Two behavioral facts to read before anything else

**1. `radius_km` is required and has no system default.** Always pass it
explicitly (see `config/defaults.yaml:radius_km`), never omit it. Passing 0
is silently rewritten to 2 km by the tool — undocumented behavior, don't
rely on it. Use the **same radius on both sides** of any YoY comparison.

**2. The valid demand comparison is always year-over-year, never
week-over-week within a single snapshot.** `search_period_from/to` defaults
to always covering the 91 days before **today**, not before the queried stay
week. As a result, the demand count for stay weeks progressively further in
the future declines almost mechanically, regardless of any real seasonality.
**This is not a market signal: it's an artifact of the fixed observation
window.** Lens X1 (and every other lens that reads a demand trend: X4, X6,
X7) must therefore always compare the **same stay window a year ago vs
today**, never two different weeks of the same snapshot — it's the same
method `sb-monday-brief` already uses for its own Detector 1
(`raw/demand_now.md` / `raw/demand_ly.md`), it shouldn't be reinvented.

| Lens | Ask `sb-revenue-lens` | Ask `sb-reservation-insights` | Comparison |
|---|---|---|---|
| **X1** — Comparative pace | Demand for {period} **this year** and demand for the same window **a year ago** (±364 days), same radius (L1/L2 of `sb-revenue-lens`, not "week ahead" — see warning above) | Actual OTB for {period} today, and STLY for the same window a year ago (booked within the snapshot minus canceled within the snapshot — `sb-reservation-insights`/`sb-monday-brief`'s method, don't reinvent it) | Delta % demand YoY vs delta % sales YoY, over the same window |
| **X2** — Conversion brakes | L3 — Restrictions vs LOS, **only nights with an explicit restriction code** (`MinLOS N` in `Restrictions`) — never a "Can Stay: No" with empty `Restrictions`, which is sold-out, not a brake (see "X2" warning in `references/cross-lenses.md`) | Cancellations and one-night stays over {period}, per date | Intersection of the nights flagged by L3 and the nights with low actual sales/high cancellations |
| **X3** — Price and realized parity | L4 — OTA parity on sample dates (requires `rate_match_enabled`) | Actual ADR per channel over a wider historical period (e.g. last concluded quarter) | **Two facts side by side** (see "X3" in `references/cross-lenses.md`): live parity status + realized ADR gap per channel |
| **X4** — Product vs demand | L1/L2 to identify demand peaks (over a single wide snapshot, never consecutive weeks ahead), plus the package **and** offer catalog (an internal call of `sb-revenue-lens`, not ours — many properties don't use "packages" at all, check which of the two concepts the property uses) | Which packages/offers actually sell over {period} | Catalog in peak periods vs actual sales in those periods |
| **X5** — Markets and segments | L6 — Demand positioning (`countryCode`, `guestType`, `device`) | Actual source markets and guest composition over {period} — always state the field's exact coverage, even above `min_field_coverage` (see "X5" in `references/cross-lenses.md`) | % share of a market/segment in demand vs % share in actual reservations |
| **X6** — Pacing | YoY delta % of average `daysAhead` (L5), **same window a year ago**, **only already-concluded periods** (never a future window — censoring) | YoY delta % of actual average `DaysInAdvanced`, same window, same "only concluded" constraint | Delta YoY sales − delta YoY demand — **never the absolute value of the two lead times**, the scale is structurally different. Also compute the actual/demand ratio in both years and pass it to `scripts/verify.py`: if it has moved significantly, the gap is a hypothesis to verify, not a confirmed reading — see "X6" in `references/cross-lenses.md` |
| **X7** — Portfolio | X1-X6 repeated for each property in the group | Multi-property comparison: direct share, ADR, length of stay, pace (already natively supported) | Ranking of properties by local demand capture |

## Window alignment — the easiest mistake

`sb-revenue-lens` doesn't see actual on-the-books figures: its "demand" is
always a **search**, future or past, on the booking engine — never a
reservation. When you ask `sb-reservation-insights` for the sales side,
always distinguish `CheckInDate` (stay) from `RegistrationDate` (booking) —
the same distinction that skill enforces for its own users. For a comparison
with area demand (always referring to searched stay dates), use
`CheckInDate`, not `RegistrationDate` — the exception is **X6**, where the
actual booking lead time is needed and so `RegistrationDate` is correct.

`sb-revenue-lens` aggregates demand **per week** by default in its light
pass: if you ask `sb-reservation-insights` for a weekly breakdown, use the
same granularity on both sides — but for X1/X4/X6/X7 the granularity that
actually matters is "same window, two years", not the sub-weeks inside the
window.

## When a market-side lens isn't applicable

- **L4** (parity) is skipped if `rate_match_enabled` is false: say so, don't
  estimate a deviation.
- **L6** is qualitative in `sb-revenue-lens`: don't turn it into a percentage
  the data doesn't support — X4 and X5 remain share/presence comparisons, not
  amount comparisons.
- **Back Office field coverage** (source market, in particular): before
  reading the X5 comparison, check the coverage as you would in
  `sb-reservation-insights` — below `config/defaults.yaml:min_field_coverage`,
  the lens abstains and states so instead of producing a fragile share.
