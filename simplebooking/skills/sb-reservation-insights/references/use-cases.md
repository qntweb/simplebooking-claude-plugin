# Common use cases — ready-made templates

Placeholders: `{{PID}}` property id · `{{FROM}}` / `{{TO}}` inclusive bounds `YYYY-MM-DD` · `{{DATE}}` single day · `{{TZ}}` IANA id.

**In every case, compute ADR downstream as `room_revenue / room_nights`**, where `room_revenue` is the sum of `TotalStay`. Never place `Adr` outside nested scope.

| # | Typical question | Who asks |
|---|---|---|
| 1 | What came in yesterday / this week? | Revenue Manager |
| 2 | How is the month going? Are we ahead or behind? | RM / Management |
| 3 | How much is direct worth, and what do OTAs cost us? | Management |
| 4 | How many arrivals tomorrow? How many guests in house? | Front Office |
| 5 | How far ahead do we sell? How much last minute? | Revenue Manager |
| 6 | Who cancels on me, and how late? | RM / Management |
| 7 | Which room type performs best? | Revenue Manager |
| 8 | Is direct really better, or does it just sell better rooms? | Management |
| 9 | What does each portal actually cost? | Management |
| 10 | What length of stay am I selling? Does a MinLOS make sense? | Revenue Manager |
| 11 | Which source markets do guests come from? | Management / Marketing |
| 12 | What did the campaigns deliver? | Marketing |
| 13 | How much do we sell beyond the room? | Management / Marketing |
| 14 | How well secured are my bookings? | Administration |
| 15 | How are the properties in the group doing? | Group Director |

---

## 1 — Pick-up

Business that came in during a **booking** window. By far the most repeated question.

```json
{ "request": {
  "propertyIds": [{{PID}}],
  "filters": {
    "date": [ { "facet": "RegistrationDate", "between": { "from": "{{FROM}}", "to": "{{TO}}" }, "timeZone": "{{TZ}}" } ],
    "keyword": [ { "facet": "ReservationStatusSimplified", "equalTo": "Active" } ] },
  "dimensions": [
    { "name": "day", "calendar": { "facet": "RegistrationDate", "interval": "Day", "timeZone": "{{TZ}}" },
      "sort": "ByKeyAscending", "size": 40,
      "metrics": [ { "name": "bookings", "reservationsCount": true },
                   { "name": "room_nights", "measure": "RoomNights", "statistic": "Sum" },
                   { "name": "room_revenue", "measure": "TotalStay", "statistic": "Sum" } ],
      "dimensions": [
        { "name": "channel", "terms": { "facet": "ChannelType" },
          "metrics": [ { "name": "bookings", "reservationsCount": true },
                       { "name": "room_nights", "measure": "RoomNights", "statistic": "Sum" },
                       { "name": "room_revenue", "measure": "TotalStay", "statistic": "Sum" } ] } ] } ],
  "metrics": [ { "name": "bookings_total", "reservationsCount": true },
               { "name": "room_nights_total", "measure": "RoomNights", "statistic": "Sum" },
               { "name": "room_revenue_total", "measure": "TotalStay", "statistic": "Sum" },
               { "name": "avg_lead_time", "measure": "DaysInAdvance", "statistic": "Average" } ] } }
```

Pick-up concentrated in a single day is usually a group or a campaign, not a trend. **If `{{TO}}` is today the last bucket is partial** — say so, or stop at yesterday.

---

## 2 — On the books and pace (STLY)

Call A — current position, night by night:

```json
{ "request": {
  "propertyIds": [{{PID}}],
  "filters": {
    "date": [ { "facet": "CheckInDate", "between": { "from": "{{FROM}}", "to": "{{TO}}" } } ],
    "keyword": [ { "facet": "ReservationStatusSimplified", "equalTo": "Active" } ] },
  "dimensions": [
    { "name": "arrival_date", "calendar": { "facet": "CheckInDate", "interval": "Day" },
      "sort": "ByKeyAscending", "size": 40,
      "metrics": [ { "name": "bookings", "reservationsCount": true },
                   { "name": "rooms", "measure": "NumberOfRooms", "statistic": "Sum" },
                   { "name": "room_nights", "measure": "RoomNights", "statistic": "Sum" },
                   { "name": "room_revenue", "measure": "TotalStay", "statistic": "Sum" } ] } ],
  "metrics": [ { "name": "bookings_total", "reservationsCount": true },
               { "name": "room_nights_total", "measure": "RoomNights", "statistic": "Sum" },
               { "name": "room_revenue_total", "measure": "TotalStay", "statistic": "Sum" } ] } }
```

The bucket is the **arrival date**: room nights of a multi-night stay are all attributed to that date. An excellent indicator of demand pressure by arrival date — **not** an occupancy curve.

Calls B and C — STLY reconstruction: see the pattern in `mechanics.md`. A third call on last year's **final** result, compared against STLY OTB, gives the net pick-up that arrived after that point: the best available estimate of what is still to come.

---

## 3 — Channel mix and cost of intermediation

```json
{ "request": {
  "propertyIds": [{{PID}}],
  "filters": {
    "date": [ { "facet": "CheckInDate", "between": { "from": "{{FROM}}", "to": "{{TO}}" } } ],
    "keyword": [ { "facet": "ReservationStatusSimplified", "equalTo": "Active" } ] },
  "dimensions": [
    { "name": "channel_type", "terms": { "facet": "ChannelType" }, "sort": "ByCountDescending",
      "metrics": [ { "name": "bookings", "reservationsCount": true },
                   { "name": "room_nights", "measure": "RoomNights", "statistic": "Sum" },
                   { "name": "room_revenue", "measure": "TotalStay", "statistic": "Sum" },
                   { "name": "services", "measure": "TotalReservationServicesRevenue", "statistic": "Sum" },
                   { "name": "commission", "measure": "CommissionAmount", "statistic": "Sum" },
                   { "name": "los", "measure": "Nights", "statistic": "Average" },
                   { "name": "lead_time", "measure": "DaysInAdvance", "statistic": "Average" } ],
      "dimensions": [
        { "name": "source", "terms": { "facet": "Source" }, "size": 30, "sort": "ByCountDescending",
          "metrics": [ { "name": "bookings", "reservationsCount": true },
                       { "name": "room_nights", "measure": "RoomNights", "statistic": "Sum" },
                       { "name": "room_revenue", "measure": "TotalStay", "statistic": "Sum" },
                       { "name": "commission", "measure": "CommissionAmount", "statistic": "Sum" } ] } ] } ] } }
```

`ChannelType` and `Channel` are top-level: additive buckets, reliable percentages. The readings: ADR per channel, **net ADR of intermediated business** (`(room_revenue − commission) / room_nights`, the only honest comparison against direct), and ancillary penetration on direct.

### OTA mix with readable names — `DistributionChannel`

A `DistributionChannel` terms facet (root-scope, additive, same behaviour class as `Source`)
returns resolved channel names instead of codes — confirmed live 2026-08-27: **100% coverage on
indirect, 0% on direct**, and on indirect its bucket counts are identical, one for one, to
`Source` (`BOOKINGXML` 696 = `Booking.com (XML)` 696). The only difference is cosmetic.

```json
{ "name": "distribution_channel", "terms": { "facet": "DistributionChannel" }, "size": 30,
  "sort": "ByCountDescending",
  "metrics": [ { "name": "bookings", "reservationsCount": true },
               { "name": "room_revenue", "measure": "TotalStay", "statistic": "Sum" } ] }
```

Prefer it for an OTA mix that will be read by someone: no normalization, no code-to-brand
lookup. Keep `Source` for anything touching direct, and for cross-referencing `CommissionAmount`.

**One commercial channel, three codes.** The channel referred to informally as "Imperatore" or
"Imperatore Travel" has moved connection platform to the channel manager more than once, leaving
three distinct `Source`/`DistributionChannel` codes behind (confirmed live 2026-08-27,
platform-wide): `IVECTOR` → *IVector (XML)* (1,956 bookings), `IMPERATOUR` → *Imperatour (XML)*
(538), `IMPERATOREJUN` → *Imperatore Juniper (XML)* (10). A question about "Imperatore" volume
must aggregate all three (the keyword `in` operator) on whichever field you use — `DistributionChannel`
does not merge them into one brand either. Ask whether a newer code has appeared if the property
is still active on that channel.

---

## 4 — Daily load

**Arrivals.** Query the week rather than a single day: one call instead of seven.

```json
{ "request": {
  "propertyIds": [{{PID}}],
  "filters": {
    "date": [ { "facet": "CheckInDate", "between": { "from": "{{FROM}}", "to": "{{TO}}" } } ],
    "keyword": [ { "facet": "ReservationStatusSimplified", "equalTo": "Active" } ] },
  "dimensions": [
    { "name": "day", "calendar": { "facet": "CheckInDate", "interval": "Day" },
      "sort": "ByKeyAscending", "size": 20,
      "metrics": [ { "name": "arrivals", "reservationsCount": true },
                   { "name": "rooms", "measure": "NumberOfRooms", "statistic": "Sum" },
                   { "name": "guests", "measure": "NumberOfPersons", "statistic": "Sum" },
                   { "name": "adults", "measure": "NumberOfAdults", "statistic": "Sum" },
                   { "name": "children", "measure": "NumberOfKids", "statistic": "Sum" },
                   { "name": "los", "measure": "Nights", "statistic": "Average" } ] } ] } }
```

**Departures:** identical, using `CheckOutDate` both as the filter facet and as the calendar facet.

**In house that night:** combined filters (see `mechanics.md`) — `CheckInDate lessOrEqualThan {{DATE}}` plus `CheckOutDate greaterThan {{DATE}}`.

`NumberOfRooms` does not equal the number of reservations: porters care about reservations, housekeeping about rooms.

---

## 5 — Booking window and last minute

> **The period must be complete.** For a future month you only see bookings already taken: the ones that would arrive close to the date do not exist yet, so average lead time is **inflated**, and the further out the month, the worse. For future periods the only legitimate reading is "how much lead time the bookings I already hold have".

```json
{ "request": {
  "propertyIds": [{{PID}}],
  "filters": {
    "date": [ { "facet": "CheckInDate", "between": { "from": "{{FROM}}", "to": "{{TO}}" } } ],
    "keyword": [ { "facet": "ReservationStatusSimplified", "equalTo": "Active" } ] },
  "dimensions": [
    { "name": "month", "calendar": { "facet": "CheckInDate", "interval": "Month" },
      "sort": "ByKeyAscending", "size": 14,
      "metrics": [ { "name": "bookings", "reservationsCount": true },
                   { "name": "lead_time_avg", "measure": "DaysInAdvance", "statistic": "Average" },
                   { "name": "lead_time_min", "measure": "DaysInAdvance", "statistic": "Min" },
                   { "name": "lead_time_max", "measure": "DaysInAdvance", "statistic": "Max" } ],
      "dimensions": [
        { "name": "channel", "terms": { "facet": "ChannelType" },
          "metrics": [ { "name": "bookings", "reservationsCount": true },
                       { "name": "lead_time_avg", "measure": "DaysInAdvance", "statistic": "Average" },
                       { "name": "room_nights", "measure": "RoomNights", "statistic": "Sum" },
                       { "name": "room_revenue", "measure": "TotalStay", "statistic": "Sum" } ] } ] } ] } }
```

**Last-minute share:** the same call plus `{ "facet": "DaysInAdvance", "lessOrEqualThan": 3 }` in `filters.numeric`, then compare the counts.

A `Max` around a year reflects when the booking window opens, not guest behaviour: read the average together with min and max.

---

## 6 — Cancellations

**No status filter**: both `Active` and `Cancelled` must pass, or the denominator disappears.

```json
{ "request": {
  "propertyIds": [{{PID}}],
  "filters": { "date": [ { "facet": "CheckInDate", "between": { "from": "{{FROM}}", "to": "{{TO}}" } } ] },
  "dimensions": [
    { "name": "source", "terms": { "facet": "Source" }, "size": 30, "sort": "ByCountDescending",
      "metrics": [ { "name": "bookings_total", "reservationsCount": true } ],
      "dimensions": [
        { "name": "status", "terms": { "facet": "ReservationStatusSimplified" },
          "metrics": [ { "name": "bookings", "reservationsCount": true },
                       { "name": "room_nights", "measure": "RoomNights", "statistic": "Sum" },
                       { "name": "room_revenue", "measure": "TotalStay", "statistic": "Sum" },
                       { "name": "days_before_checkin", "measure": "CancellationDaysBeforeCheckIn", "statistic": "Average" },
                       { "name": "days_after_booking", "measure": "CancellationDaysAfterRegistration", "statistic": "Average" } ] } ] } ],
  "metrics": [ { "name": "bookings_total", "reservationsCount": true } ] } }
```

Three readings: rate per channel (`Cancelled / (Active + Cancelled)`); **notice period**, because a cancellation 100 days out is resellable and one 2 days out is not; and ADR of cancelled versus confirmed, which tells you whether the expensive or the cheap product is being released.

Cancellation metrics return `-` on `Active` buckets, so averages stay clean. Compute the rate **per channel**, never inherited from the intermediated average: the spread between portals is very wide.

---

## 7 — Product performance

The only context where `Adr` is allowed.

```json
{ "request": {
  "propertyIds": [{{PID}}],
  "filters": {
    "date": [ { "facet": "CheckInDate", "between": { "from": "{{FROM}}", "to": "{{TO}}" } } ],
    "keyword": [ { "facet": "ReservationStatusSimplified", "equalTo": "Active" } ] },
  "dimensions": [
    { "name": "room_type", "terms": { "facet": "RoomType" }, "size": 30, "sort": "ByCountDescending",
      "metrics": [ { "name": "bookings", "reservationsCount": true },
                   { "name": "room_nights", "measure": "RoomNights", "statistic": "Sum" },
                   { "name": "room_revenue", "measure": "TotalStay", "statistic": "Sum" },
                   { "name": "adr", "measure": "Adr", "statistic": "Average" },
                   { "name": "adr_min", "measure": "Adr", "statistic": "Min" },
                   { "name": "adr_max", "measure": "Adr", "statistic": "Max" } ] } ] } }
```

Swap `RoomType` for `RatePlan`, `Offer` or `Package` for the other cuts. **Ranking and ADR only, never percentages** (nested facet). `RatePlan` buckets may come back as identifiers rather than readable names: map them from the Back Office before presenting.

For an **additive** plain / offer / package view use `RateType` — but **only with `ChannelType = Direct`**, because rate type is not populated on intermediated bookings and the `NotSet` bucket would simply mean "all intermediated business".

---

## 8 — Direct vs intermediated, like for like

Settles the objection *"direct has a higher ADR only because it sells the better rooms"* by comparing the **same room type** across both channels.

```json
{ "request": {
  "propertyIds": [{{PID}}],
  "filters": {
    "date": [ { "facet": "CheckInDate", "between": { "from": "{{FROM}}", "to": "{{TO}}" } } ],
    "keyword": [ { "facet": "ReservationStatusSimplified", "equalTo": "Active" } ] },
  "dimensions": [
    { "name": "channel", "terms": { "facet": "ChannelType" },
      "metrics": [ { "name": "bookings", "reservationsCount": true } ],
      "dimensions": [
        { "name": "room_type", "terms": { "facet": "RoomType" }, "size": 20, "sort": "ByCountDescending",
          "metrics": [ { "name": "bookings", "reservationsCount": true },
                       { "name": "room_nights", "measure": "RoomNights", "statistic": "Sum" },
                       { "name": "room_revenue", "measure": "TotalStay", "statistic": "Sum" },
                       { "name": "adr", "measure": "Adr", "statistic": "Average" } ] } ] } ] } }
```

`RoomType` is populated on **both** channel types, so the like-for-like comparison is possible. Be careful, though: the intermediated average can hide portals that differ widely, some with an ADR above direct. Break it down by `Source` before concluding.

---

## 9 — True cost per portal

**Mandatory first step: `CommissionAmount` coverage.** Read it from `Max`, not from `Min`:

- `Max` of zero → the portal transmits **nothing**. Its cost is invisible here.
- `Max` positive → the portal transmits. A `Min` of zero then means **partial** coverage, the worst case, because the total looks valid but is incomplete.
- **`Min` below zero is normal**, not an anomaly: chargebacks and corrections are recorded as negative commission. The `Sum` is therefore already net of them, silently.

```json
{ "request": {
  "propertyIds": [{{PID}}],
  "filters": {
    "date": [ { "facet": "CheckInDate", "between": { "from": "{{FROM}}", "to": "{{TO}}" } } ],
    "keyword": [ { "facet": "ChannelType", "equalTo": "Indirect" } ] },
  "dimensions": [
    { "name": "source", "terms": { "facet": "Source" }, "size": 30, "sort": "ByCountDescending",
      "metrics": [ { "name": "bookings", "reservationsCount": true },
                   { "name": "commission", "measure": "CommissionAmount", "statistic": "Sum" },
                   { "name": "commission_min", "measure": "CommissionAmount", "statistic": "Min" },
                   { "name": "commission_max", "measure": "CommissionAmount", "statistic": "Max" } ],
      "dimensions": [
        { "name": "status", "terms": { "facet": "ReservationStatusSimplified" },
          "metrics": [ { "name": "bookings", "reservationsCount": true },
                       { "name": "room_nights", "measure": "RoomNights", "statistic": "Sum" },
                       { "name": "room_revenue", "measure": "TotalStay", "statistic": "Sum" },
                       { "name": "commission", "measure": "CommissionAmount", "statistic": "Sum" } ] } ] } ] } }
```

No status filter: cancellations are needed too. The full picture per portal is **gross ADR · commission · net ADR · cancellation rate**.

The net-ADR ranking is reliable **only for rows where commission is transmitted**. For the others you need the contractual model, which lives outside the tool: without it, a gross-rate channel that does not transmit will look like the most profitable one.

---

## 10 — Length of stay and MinLOS

There is no numeric histogram: one call per band, changing only the `Nights` entry in `filters.numeric`.

```json
{ "facet": "Nights", "equalTo": 1 }
{ "facet": "Nights", "equalTo": 2 }
{ "facet": "Nights", "between": { "from": 3, "to": 4 } }
{ "facet": "Nights", "greaterOrEqualThan": 5 }
```

The rest of the request stays identical, with `ChannelType` as a sub-dimension and metrics `reservationsCount`, `RoomNights`, `TotalStay`.

**A fifth call is the one that actually decides a MinLOS**: `Nights equalTo 1` with a `CheckIn/Day` calendar dimension, to see **which dates** rest on single nights. If they are scattered, a restriction removes little — but for the same reason it gains little, which is a useful answer in the negative.

`Nights` is the length of the reservation, not room nights: a 2-night booking for 3 rooms sits in the "2 nights" band and weighs 6 room nights.

---

## 11 — Source markets

```json
{ "request": {
  "propertyIds": [{{PID}}],
  "filters": {
    "date": [ { "facet": "CheckInDate", "between": { "from": "{{FROM}}", "to": "{{TO}}" } } ],
    "keyword": [
      { "facet": "ReservationStatusSimplified", "equalTo": "Active" },
      { "facet": "ChannelType", "equalTo": "Direct" } ] },
  "dimensions": [
    { "name": "market", "terms": { "facet": "CustomerCountryCode" }, "size": 100, "sort": "ByCountDescending",
      "metrics": [ { "name": "bookings", "reservationsCount": true },
                   { "name": "room_nights", "measure": "RoomNights", "statistic": "Sum" },
                   { "name": "room_revenue", "measure": "TotalStay", "statistic": "Sum" },
                   { "name": "los", "measure": "Nights", "statistic": "Average" },
                   { "name": "lead_time", "measure": "DaysInAdvance", "statistic": "Average" } ] } ] } }
```

The `Direct` filter is deliberate: on intermediated bookings the country arrives from only a few portals. `size` is high because a low value truncates the tail and makes coverage look worse than it is. Unify variants of the same country before presenting a ranking.

The column that matters is not volume but **ADR × LOS**: a small market with double the length of stay is worth more than a large hit-and-run one.

---

## 12 — Campaign attribution

```json
{ "request": {
  "propertyIds": [{{PID}}],
  "filters": {
    "date": [ { "facet": "RegistrationDate", "between": { "from": "{{FROM}}", "to": "{{TO}}" }, "timeZone": "{{TZ}}" } ],
    "keyword": [
      { "facet": "ReservationStatusSimplified", "equalTo": "Active" },
      { "facet": "ChannelType", "equalTo": "Direct" } ] },
  "dimensions": [
    { "name": "medium", "terms": { "facet": "TrackingUtmMedium" }, "size": 30, "sort": "ByCountDescending",
      "metrics": [ { "name": "bookings", "reservationsCount": true },
                   { "name": "room_revenue", "measure": "TotalStay", "statistic": "Sum" } ],
      "dimensions": [
        { "name": "source", "terms": { "facet": "TrackingUtmSource" }, "size": 30, "sort": "ByCountDescending",
          "metrics": [ { "name": "bookings", "reservationsCount": true },
                       { "name": "room_revenue", "measure": "TotalStay", "statistic": "Sum" } ] } ] } ],
  "metrics": [ { "name": "direct_total", "reservationsCount": true } ] } }
```

> **Boundary.** If the question is really *"where do my direct bookings come from"* — the
> provenance of direct business, the weight of metasearch, an AI assistant, a CRM quote tool,
> the share that stays unattributable — that belongs to **`sb-direct-attribution`**, which
> classifies sources into bands, keeps a curated vocabulary in `known-sources.yaml`, and
> refuses to publish when the figures do not reconcile. Use the query above for a quick
> campaign readout inside a wider reservation analysis, and hand over when attribution *is*
> the question.

Start from **medium**, which is cleaner than source. The empty-key bucket gives the untracked count: **state coverage before the ranking**, always.

Pair this with a `Source` dimension: it catches origins UTMs never see, metasearch in particular, and it does not depend on link tagging. Exclude `PrenMan` from any attribution analysis — but see the caveat in `fields.md` before doing so, if the "CRM quote tool" band matters: a Converto quote closed by hand still carries `PrenMan`.

**A CRM quote tool no longer has to be identified by guessing its `Source` tag.** `ConvertoQuoteId hasValue: true` isolates every reservation converted from a Converto quote directly — see "Converto quote provenance" in `fields.md`. It does not correlate with any `Source` value (roughly a third of it is `PrenMan`, a chunk more is `MOBILE`, and the field is often empty), so this is not something a Source-vocabulary census would ever surface.

**`rezmate.ai` is worth knowing by name.** It is the AI concierge embedded natively in Simple
Booking on the hotel's own website — it answers questions from an extended knowledge base and
can walk a guest into a same-session booking. Filter `Source equalTo "rezmate.ai"` (confirmed
live 2026-08-27; verify the exact spelling per property, since `Source` is free text) to count
what it drove. Adoption varies widely — from a single booking to over twenty on the properties
checked at time of writing.

---

## 13 — Ancillary services

```json
{ "request": {
  "propertyIds": [{{PID}}],
  "filters": {
    "date": [ { "facet": "CheckInDate", "between": { "from": "{{FROM}}", "to": "{{TO}}" } } ],
    "keyword": [ { "facet": "ReservationStatusSimplified", "equalTo": "Active" } ] },
  "dimensions": [
    { "name": "channel", "terms": { "facet": "ChannelType" },
      "metrics": [ { "name": "bookings", "reservationsCount": true },
                   { "name": "room_revenue", "measure": "TotalStay", "statistic": "Sum" },
                   { "name": "services", "measure": "TotalReservationServicesRevenue", "statistic": "Sum" },
                   { "name": "services_avg", "measure": "TotalReservationServicesRevenue", "statistic": "Average" },
                   { "name": "services_max", "measure": "TotalReservationServicesRevenue", "statistic": "Max" } ] },
    { "name": "month", "calendar": { "facet": "CheckInDate", "interval": "Month" }, "sort": "ByKeyAscending", "size": 14,
      "metrics": [ { "name": "room_revenue", "measure": "TotalStay", "statistic": "Sum" },
                   { "name": "services", "measure": "TotalReservationServicesRevenue", "statistic": "Sum" } ] } ] } }
```

The indicator is `services / room_revenue` **on direct only**. `services_max` tells you whether a valuable ancillary product exists at all or only micro-sales. The spread between properties is enormous and does not depend on the platform: where it sits near zero, that is a commercial choice, not a technical limit.

### Itemized: which service, how much, how many

`Service` is a nested-scope terms facet — same family as `RoomType`, `RatePlan`, `Offer`:
non-additive, bucket names resolve (`Transfer Florence`, `Early check in`, `Buffet Breakfast`,
...), `docCount` counts service entries, not reservations.

```json
{ "request": {
  "propertyIds": [{{PID}}],
  "filters": {
    "date": [ { "facet": "CheckInDate", "between": { "from": "{{FROM}}", "to": "{{TO}}" } } ],
    "keyword": [
      { "facet": "ReservationStatusSimplified", "equalTo": "Active" },
      { "facet": "ChannelType", "equalTo": "Direct" } ] },
  "dimensions": [
    { "name": "service", "terms": { "facet": "Service" }, "size": 30, "sort": "ByCountDescending",
      "metrics": [ { "name": "bookings", "reservationsCount": true },
                   { "name": "revenue", "measure": "ServiceRevenue", "statistic": "Sum" },
                   { "name": "qty", "measure": "ServiceQuantitySold", "statistic": "Sum" } ] } ] } }
```

This turns "how much ancillary" into "which product": a service with high `qty` and low
`revenue` is a low-value amenity sold often (early check-in), the opposite pattern is a rare,
high-ticket purchase (a package or a transfer). `ServiceRevenue` and `ServiceQuantitySold` are
nested-scoped like `Adr` — they only make sense inside a dimension on `Service`. Still not
filterable: you cannot isolate "reservations that bought service X" as a filter clause, only
read it from the bucket.

---

## 14 — Payment method and collection risk

Always start with a **census** of the vocabulary: if the property uses a single value, there is nothing to read.

```json
{ "request": {
  "propertyIds": [{{PID}}],
  "filters": {
    "date": [ { "facet": "CheckInDate", "between": { "from": "{{FROM}}", "to": "{{TO}}" } } ],
    "keyword": [ { "facet": "ReservationStatusSimplified", "equalTo": "Active" } ] },
  "dimensions": [
    { "name": "method", "terms": { "facet": "PaymentMethod" }, "size": 10, "sort": "ByCountDescending",
      "metrics": [ { "name": "bookings", "reservationsCount": true },
                   { "name": "room_revenue", "measure": "TotalStay", "statistic": "Sum" },
                   { "name": "total_revenue", "measure": "TotalReservationRevenue", "statistic": "Sum" } ],
      "dimensions": [
        { "name": "channel", "terms": { "facet": "ChannelType" },
          "metrics": [ { "name": "bookings", "reservationsCount": true } ] } ] } ] } }
```

Three readings, all against the **total of populated methods** and never the total booking count: the `NM` share (**unsecured** business — nothing to charge on a no-show), the `TR` share (already settled through the gateway), and the `BT` share (manual reconciliation workload).

### What was actually collected

`TotalReceived` (root-scope, any payment method) and `TransactorPaidAmount` (root-scope, gateway
settlements only) expose the collected amount. A `PaymentTransactor` terms facet — root-scope
and **additive**, unlike `Service`/`RoomType`/`RatePlan`/`Offer` — resolves which gateway
processed the payment (`Carta Si - Nexi Online`, `ScalaPay`, ...).

```json
{ "request": {
  "propertyIds": [{{PID}}],
  "filters": {
    "date": [ { "facet": "CheckInDate", "between": { "from": "{{FROM}}", "to": "{{TO}}" } } ],
    "keyword": [
      { "facet": "ReservationStatusSimplified", "equalTo": "Active" },
      { "facet": "PaymentMethod", "equalTo": "Transactor" } ] },
  "dimensions": [
    { "name": "gateway", "terms": { "facet": "PaymentTransactor" }, "size": 10, "sort": "ByCountDescending",
      "metrics": [ { "name": "bookings", "reservationsCount": true },
                   { "name": "paid", "measure": "TransactorPaidAmount", "statistic": "Sum" } ] } ],
  "metrics": [ { "name": "total_received", "measure": "TotalReceived", "statistic": "Sum" },
               { "name": "total_transactor_paid", "measure": "TransactorPaidAmount", "statistic": "Sum" } ] } }
```

Note the filter uses the enum name `Transactor`, not the bucket code `TR` — see `mechanics.md`.

**Coverage is concentrated on `TR`, not universal** — validated on two properties: `TotalReceived`
was essentially zero on `CreditCard` (a guarantee, never a platform charge) and negligible on
`BankTransfer` and `NoMethod`, but substantial wherever `PaymentMethod` is `Transactor`. Treat
`TotalReceived` as "what the gateway settled", not as a generic collected-amount figure valid
across every payment method — measure coverage per property first, same as `CommissionAmount`.

**`TotalReceived` and `TransactorPaidAmount` do not always match, even filtered to `Transactor`
alone** — a gap of roughly 1% was observed with no known cause. Report `TotalReceived` as the
headline figure; if both are shown, flag the discrepancy rather than explaining it away.

This still falls short of a full cash forecast: nothing here tells you, **per booking**, whether
the collected amount is the full stay or a deposit with the balance due on arrival — only the
aggregate collected.

---

## 15 — Cross-property benchmark

```json
{ "request": {
  "propertyIds": [{{PID}}, {{PID}}, {{PID}}],
  "filters": {
    "date": [ { "facet": "CheckInDate", "between": { "from": "{{FROM}}", "to": "{{TO}}" } } ],
    "keyword": [ { "facet": "ReservationStatusSimplified", "equalTo": "Active" } ] },
  "dimensions": [
    { "name": "property", "terms": { "facet": "Property" }, "size": 50, "sort": "ByCountDescending",
      "metrics": [ { "name": "bookings", "reservationsCount": true },
                   { "name": "room_nights", "measure": "RoomNights", "statistic": "Sum" },
                   { "name": "room_revenue", "measure": "TotalStay", "statistic": "Sum" },
                   { "name": "commission", "measure": "CommissionAmount", "statistic": "Sum" },
                   { "name": "lead_time", "measure": "DaysInAdvance", "statistic": "Average" } ],
      "dimensions": [
        { "name": "channel", "terms": { "facet": "ChannelType" },
          "metrics": [ { "name": "bookings", "reservationsCount": true },
                       { "name": "room_nights", "measure": "RoomNights", "statistic": "Sum" },
                       { "name": "room_revenue", "measure": "TotalStay", "statistic": "Sum" } ] } ] },
    { "name": "currency", "terms": { "facet": "Currency" },
      "metrics": [ { "name": "bookings", "reservationsCount": true } ] } ] } }
```

Absolute revenue always rewards the largest property: the useful comparisons are **ADR, direct share and average lead time**. The `Currency` dimension is a control — if more than one bucket comes back, aggregate totals are meaningless.

The data is **live**: for any comparison that will be shared or repeated, record the extraction date and time.
