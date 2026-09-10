# Mechanics of `run_reservation_aggregation`

## Request shape

```json
{
  "request": {
    "propertyIds": [9999],
    "filters":    { "keyword": [ { "facet": "..." } ], "numeric": [ { "facet": "..." } ], "date": [ { "facet": "..." } ] },
    "dimensions": [ { "terms|calendar": { }, "name": "", "size": 0, "sort": "", "dimensions": [], "metrics": [] } ],
    "metrics":    [ { "reservationsCount|measure+statistic|distinctCountOf": "" } ]
  }
}
```

Omitting `propertyIds` means **every property the caller can access**: convenient for a lookup, risky in an analysis, because the perimeter shifts with permissions.

## Filters

`filters` is **one object**, not a list: three optional lists, one per family — `keyword`,
`numeric`, `date`. Each entry names one `facet` and puts its operators (`equalTo`, `between`,
`greaterThan`, …) **directly on the entry** — there is no `dateFilter`/`numericFilter`/`keywordFilter`
wrapper key. A facet may appear at most once across all three lists.

- **Dates** — `equalTo` (whole day), `between` (inclusive on both ends), `greaterThan` / `greaterOrEqualThan` / `lessThan` / `lessOrEqualThan`, `hasValue`. `between` cannot be combined with other operators: use comparisons for an open-ended range. **`between` rejects a span over 24 months** (confirmed live on `RegistrationDate`) — split a longer range into two calls.
- **Numeric** — `equalTo`, `in`, `between`, comparisons, `hasValue`. **There are no numeric
  negations**: `notEqualTo` and `notIn` exist on keyword fields only. To exclude a numeric
  value, use two comparisons or an explicit `in`.
  `ConvertoQuoteId` is one of these — `hasValue: true` isolates reservations converted from a
  Converto quote. See "Converto quote provenance" in `fields.md`.
- **Keyword** — `equalTo`, `in`, `notEqualTo`, `notIn`, `hasValue`. On enum fields, values must
  be **exact member names**. One affirmative (`equalTo` or `in`) and one negation
  (`notEqualTo` or `notIn`) **may be combined** in the same clause: that is how you take a set
  while carving values out of it — every portal except two, for instance.

Allowed enums:

| Facet | Values |
|---|---|
| `ChannelType` | `Direct`, `Indirect` |
| `Channel` | `Website`, `Facebook`, `Mobile`, `Business`, `Group`, `Portal`, `Ota`, `Agency` |
| `RateType` | `NotSet`, `Plain`, `Package`, `Offer` |
| `ReservationStatusSimplified` | `Active`, `Cancelled` |
| `PaymentMethod` | `NoMethod`, `BankTransfer`, `PostalTransfer`, `PostalOrder`, `CreditCard`, `Transactor` |

**`PaymentMethod` has two different vocabularies — do not mix them.** The **filter** value is
the enum name above (`"equalTo": "Transactor"`). The **bucket key**, when you group by
`PaymentMethod`, comes back as the short code documented in `fields.md` (`TR`, `CC`, `BT`, `NM`,
`PT`, `MT`). Writing the short code into a filter clause is rejected.

**Filter status with `ReservationStatusSimplified`.** The `ReservationStatus` + `ReservationSubStatus` pair is finer-grained but considerably easier to get wrong.

### Combined filters

Two date clauses over the same set combine with AND, which enables some non-obvious queries:

```json
"filters": { "date": [
  { "facet": "CheckInDate",  "lessOrEqualThan": "2026-08-23", "greaterOrEqualThan": "2026-02-23" },
  { "facet": "CheckOutDate", "greaterThan":     "2026-08-23", "lessOrEqualThan":    "2027-02-23" }
] }
```

This isolates reservations **in house** that night. The boundary is delicate: `greaterThan` (strict) correctly excludes guests departing that morning, while `greaterOrEqualThan` double-counts rooms in turnover.

**Bound both sides** (confirmed live 2026-09-10): leaving `CheckInDate` and `CheckOutDate` fully
open-ended on both clauses, as a naive reading of "in house" suggests, fails with `the check-in
or check-out date filter spans more than 24 months`. A generous bracket around the target date
(here ±6 months) is enough and does not change which reservations match, since a stay longer than
a year on either side is not a realistic case to worry about missing.

### Filtering on nested elements — mind the name, and the value

`RatePlan`, `Offer` and `RoomQuantity` **are** filterable, and so is room type — but as a
filter the facet is **`RoomId`**, not `RoomType` and, as of a schema change confirmed live
2026-09-08, no longer `Room` either — the facet was renamed and now takes the numeric room
type **ID**, not its name. `RoomId equalTo "Deluxe Double"` is rejected outright; a value that
looks like a name but isn't a valid ID fails at the search layer instead (`Document search
error: all shards failed`), which is a worse failure mode because it looks like a transient
fault rather than a wrong request. Resolve the ID first from a `RoomType` dimension bucket —
its key is `Name (ID)` — then filter on the ID as a string:

```json
{ "facet": "RoomId", "equalTo": "28615" }
```

This is what lets you escape the non-additivity of those facets: instead of reading a bucket
that double-counts multi-room reservations, filter to one product and read a clean total. Worth
reaching for in the product-performance and like-for-like cases in `use-cases.md`.

### No monetary field is filterable

`TotalStay`, `TotalReservationRevenue`, `TotalReservationServicesRevenue`, `TotalTaxes`,
`CommissionAmount`, `TotalReceived`, `TransactorPaidAmount`, `ServiceRevenue` and `Adr` are
measures only — none appears among the filter facets. You cannot ask for "reservations above
1000 euro", nor filter to "reservations with at least one service". Filter on the countable
fields instead (`Nights`, `RoomNights`, `NumberOfPersons`, `RoomQuantity`, `DaysInAdvance`, the
cancellation-distance pair) and read money as a metric.

## Dimensions

Two kinds, nestable to any depth.

**`terms`** — group by a field's value:
`Property`, `Offer`, `RatePlan`, `RoomType`, `Package`, `Service`, `Portal`, `DistributionChannel`, `Channel`, `ChannelType`, `RateType`, `Currency`, `PaymentTransactor`, `ReservationStatusSimplified`, `ReservationStatus`, `ReservationSubStatus`, `ReservationType`, `Source`, `PaymentMethod`, `PropertyCountryCode`, `ReservationCode`, `TrackingUtmSource`, `TrackingUtmMedium`, `TrackingUtmCampaign`, `TrackingRefId`, `Tracking*ClickId`, `CustomerCountryCode`, `FromConvertoQuote`.

`CustomerCountryName` **no longer exists** (confirmed live, 2026-09-08 — see `fields.md`): only
the code is groupable now, no resolved country name. `FromConvertoQuote` is new (boolean, see
"Converto quote provenance" in `fields.md`) and, unlike most of this list, **rejected as a
filter facet** — filter on the numeric `ConvertoQuoteId` instead (`hasValue: true`).

`DistributionChannel` is not documented in the tool's own facet enum (confirmed live, 2026-08-27) — the schema description lags the connector, same pattern already seen with `TotalReservationServicesRevenue`. Do not trust the enum list as exhaustive; if a field is reported as newly added, try it.

**`calendar`** — group by date: facets `RegistrationDate`, `CheckInDate`, `CheckOutDate`, `CancellationDate`; intervals `Hour`, `Day`, `Week`, `Month`, `Quarter`, `Year`.

`sort`: `ByCountAscending`, `ByCountDescending`, `ByKeyAscending`, `ByKeyDescending`. Use `ByKeyAscending` for time series.

**Always set `size` explicitly** — the default truncates silently. Use at least 40 for a month of days, 100 or more for a vocabulary census.

### Bucket rows carry resolved names, not just IDs

Confirmed live (2026-08-26) on `Offer`, `RatePlan`, `Package` and `Service`: a bucket key comes
back as `Name (ID)` — for example `Transfer Florence (34222)` — not the bare numeric ID. This
was previously documented only for the `Property` lookup in `SKILL.md`; it applies more broadly.
A row that has no name resolves to `0 (unresolved)` rather than failing.

### `DistributionChannel` — resolved OTA names, indirect only

Root-scope and additive, same behaviour class as `Source` — not a nested facet, and **not the
same field as `Portal`** (see `fields.md`, `Portal` is almost always empty; do not confuse the
two despite the similar name). Bucket keys resolve to `Name (Code)`, e.g. `Booking.com (XML)
(BOOKINGXML)`, `Expedia (XML) (EXPEDIA)`.

**Coverage is not guaranteed on direct bookings.** On a property tested end to end,
`ChannelType = Indirect` bookings had 100% coverage, while `ChannelType = Direct`
bookings had 0% — the field is simply not populated on the direct side. On indirect
bookings its bucket counts matched `Source` one for one (same OTAs, same counts), the
only difference being a readable name instead of a code.

**Use it for an OTA mix you are about to show someone**: no normalization, no code-to-brand
lookup. **Keep using `Source`** for anything touching direct, or for cross-referencing
`CommissionAmount` per portal — `DistributionChannel` has nothing to say there.

## Metrics

Three mutually exclusive forms: `reservationsCount: true`, or `measure` + `statistic`, or `distinctCountOf`.

The available **measures** are twenty: `Nights`, `RoomNights`, `RoomQuantity`, `NumberOfAdults`, `NumberOfKids`, `NumberOfPersons`, `NumberOfRooms`, `DaysInAdvance`, `CancellationDaysAfterRegistration`, `CancellationDaysBeforeCheckIn`, `TotalReservationRevenue`, `TotalReservationServicesRevenue`, `TotalStay`, `TotalTaxes`, `CommissionAmount`, `Adr`, `TotalReceived`, `TransactorPaidAmount`, `ServiceRevenue`, `ServiceQuantitySold`.

**`TotalReservationServicesRevenue` replaced `TotalServices`** in the connector's accepted enum (confirmed in production, 2026-08-26: the old name now fails with `Unknown values: TotalServices`). Same meaning, same value — only the name changed.

**Four measures are new** (confirmed live, 2026-08-26):
- `TotalReceived`, `TransactorPaidAmount` — the amount actually collected. Root-scope. See
  `fields.md` for the coverage caveat: in practice populated almost only where `PaymentMethod`
  is `Transactor`, despite the generic name.
- `ServiceRevenue`, `ServiceQuantitySold` — nested-scope, same family as `Adr`. They only make
  sense inside a dimension on the new `Service` facet (see Scoping below); do not place them at
  the root or inside a calendar dimension.

Statistics: `Sum`, `Average`, `Min`, `Max`.

`distinctCountOf` is **approximate** — exact for small counts, estimated for large ones. Never use it for reconciliation.

### Metrics must be repeated at every level

Metrics declared inside a dimension are computed on that level's buckets. If you need revenue both per day and per channel, write it twice:

```json
{ "name": "day",
  "calendar": { "facet": "RegistrationDate", "interval": "Day", "timeZone": "Europe/Rome" },
  "sort": "ByKeyAscending",
  "metrics": [ { "name": "bookings", "reservationsCount": true },
               { "name": "room_revenue", "measure": "TotalStay", "statistic": "Sum" } ],
  "dimensions": [
    { "name": "channel", "terms": { "facet": "ChannelType" },
      "metrics": [ { "name": "bookings", "reservationsCount": true },
                   { "name": "room_revenue", "measure": "TotalStay", "statistic": "Sum" } ] } ] }
```

## Scoping: the rule that makes requests fail

Some elements live in the reservation's **nested** room / rate-plan block rather than at the top level. They are:

- the **`Adr`**, **`ServiceRevenue`** and **`ServiceQuantitySold`** measures
- the **`RoomType`**, **`RatePlan`**, **`Offer`**, **`Service`** facets
- `distinctCountOf` on `RoomType`, `RatePlan` and `Offer` (not available on `Service`)

`ServiceRevenue` / `ServiceQuantitySold` follow `Adr`'s rule exactly: they must sit inside a
dimension on `Service`, not at the root or inside a calendar dimension.

An `Adr` at the root, or inside a calendar dimension, produces:

```
metric 'adr' is nested-scoped and must sit inside a nested-scope dimension
```

**Where `Adr` is allowed** — inside a dimension on a nested facet:

```json
{ "name": "room_type", "terms": { "facet": "RoomType" }, "size": 20,
  "metrics": [ { "name": "bookings", "reservationsCount": true },
               { "name": "adr",     "measure": "Adr", "statistic": "Average" },
               { "name": "adr_min", "measure": "Adr", "statistic": "Min" },
               { "name": "adr_max", "measure": "Adr", "statistic": "Max" } ] }
```

The min/max spread per room type is often more informative than the average: it describes how wide the rate range is on that product.

### Two different ADRs — never mix them

| | How you get it | What it is |
|---|---|---|
| **Computed ADR** | `TotalStay / RoomNights`, downstream | **night-weighted** average. This is the one for a report |
| **Engine `Adr`** | measure inside nested scope | **unweighted** average across room/rate-plan entries. Use it to compare room types with each other |

On the same data they return different figures. That is not a bug — they are different measures. **Do not use both in one document.**

### Non-additivity

Buckets on `RoomType`, `RatePlan`, `Offer` and `Service` **do not sum to the total**: a reservation with three room types, or three services, appears in three buckets. The tool states this in its output and warns that `docCount` counts *entries*, not reservations. Always add `reservationsCount` inside the bucket to get distinct reservations.

Consequence: read those facets as **ranking**, never as percentage shares (ranking and ADR for `RoomType`/`RatePlan`/`Offer`; ranking, revenue and quantity for `Service`).

`PaymentTransactor`, by contrast, is **root-scope and additive** — despite being about payments, it behaves like `ChannelType` or `PaymentMethod`, not like the nested four above. Its bucket counts sum to the matched total.

## The revenue components

```
TotalStay + TotalReservationServicesRevenue = TotalReservationRevenue
```

- **`TotalStay`** — room revenue. **The basis for ADR.**
- **`TotalReservationServicesRevenue`** — ancillary sold at booking time. **Always exactly zero on intermediated channels**: an OTA does not sell booking-engine services. The correct denominator for penetration is therefore direct only.
- **`TotalReservationRevenue`** — the sum of the two. It is "what the reservation is worth", not room revenue.
- **`TotalTaxes`** — see `fields.md`: **ignore it**.

None of the three above is **what was collected**. That is `TotalReceived` /
`TransactorPaidAmount` — a separate pair of measures with its own, much narrower coverage. See
`fields.md`, section `PaymentMethod`, before using either in a report.

## Time zones

`timeZone` accepts **IANA ids only** (`Europe/Rome`); a numeric offset (`+02:00`) is rejected.

It affects **`RegistrationDate`** and **`CancellationDate`** only. `CheckInDate` and `CheckOutDate` are whole-day fields: passing a zone there is not an error, it simply has no effect.

**On multi-property queries the time zone is ignored.** If the properties in scope do not share a zone, the tool interprets dates in **UTC** and says so at the top of the output. For day-level analysis, query one property at a time.

## Recurring patterns

### Vocabulary census

Before interpreting a free-value field (`Source`, `PaymentMethod`, `TrackingUtmSource`), enumerate it:

```json
{ "name": "values", "terms": { "facet": "Source" }, "size": 100,
  "sort": "ByCountDescending",
  "metrics": [ { "name": "bookings", "reservationsCount": true },
               { "name": "properties", "distinctCountOf": "Property" } ] }
```

### Measuring coverage

Unpopulated rows **do not appear** in keyword-field buckets: coverage is `sum of buckets / parent count`. The exception is `TrackingUtmSource`, which returns an **empty-key bucket** holding the untracked count — there, coverage is readable directly.

You can also isolate the unpopulated rows with `hasValue: false`.

### Same Time Last Year (STLY)

The wrong comparison is today's on-the-books against last year's **final** result: one is closed, the other is not. It always reports "we are behind".

The right comparison reconstructs the book **as it stood a year ago today**, and it is exact:

```
STLY OTB = (booked by the snapshot) − (cancelled by the snapshot)
```

```json
// 1) gross booked by the snapshot — no status filter
"filters": { "date": [
  { "facet": "CheckInDate",      "between": { "from": "2025-09-01", "to": "2025-09-30" } },
  { "facet": "RegistrationDate", "lessOrEqualThan": "2025-08-23" } ] }

// 2) cancelled by the snapshot — to subtract
"filters": {
  "date": [
    { "facet": "CheckInDate",      "between": { "from": "2025-09-01", "to": "2025-09-30" } },
    { "facet": "RegistrationDate", "lessOrEqualThan": "2025-08-23" },
    { "facet": "CancellationDate", "lessOrEqualThan": "2025-08-23" } ],
  "keyword": [
    { "facet": "ReservationStatusSimplified", "equalTo": "Cancelled" } ]
}
```

Simply filtering `Active` on last year is the error to avoid: it would drop every cancellation that happened over the following twelve months, badly understating the benchmark.

**The snapshot is today's real date minus one year**, and it must move on every rerun. A misaligned snapshot leaves the comparison percentages almost unchanged while badly distorting the residual pick-up estimate — precisely the figure used to project the close of the month.

### Numeric bands

There is no numeric histogram: build bands with one call each, changing only the filter. They must be **exhaustive and disjoint** — the sum has to return the period total.

## Common errors and what they mean

| Symptom | Cause |
|---|---|
| `metric 'X' is nested-scoped...` | `Adr` or a nested distinct-count outside the right scope |
| A filter on `RoomType` is rejected | as a filter the facet is `RoomId`; `RoomType` is a dimension facet only |
| `Document search error: all shards failed` on a `RoomId` filter | value is a room name, not the numeric ID — resolve the ID from a `RoomType` bucket first |
| A filter on `FromConvertoQuote` is rejected | it is a dimension facet only; filter on the numeric `ConvertoQuoteId` instead |
| A filter on an amount is rejected | monetary fields are measures, never filter facets |
| Time zone rejected | numeric offset instead of an IANA id |
| Truncated buckets | `size` not set |
| Percentages do not sum to 100 | nested facet, non-additive |
| Cancellation rate cannot be computed | a status filter was applied: both `Active` and `Cancelled` must pass |
| Implausibly large totals | different currencies summed together — add a `Currency` control dimension |
| Last calendar bucket unusually low | the period runs to today and is partial |
| `the ... date filter spans more than 24 months` | narrow the `between` range, or split into several calls |
