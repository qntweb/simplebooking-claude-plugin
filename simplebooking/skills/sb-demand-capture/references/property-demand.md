# First-party demand — `run_property_demand_aggregation`

The third source. `sb-revenue-lens` reads **area demand** (who searches the
destination), `sb-reservation-insights` reads **sales** (who booked). This tool reads
what sits between them: **the searches performed on this property's own booking
engine**.

```
area demand (IBE)  →  my shop window (this tool)  →  sales (Back Office)
```

Until this existed, every gap between the first and the third term was ambiguous: *they
don't find me* and *they find me and don't buy* produced the same number. They are now
separable, and that separation is what most of this skill's lenses gained.

**Same MCP as `sb-reservation-insights`** (Simple Booking Back Office). No new
dependency: this skill already reaches that server through its sales source.

---

## 1. What counts as a search

A guest interacted with the booking engine by setting search parameters. Three routes,
all equivalent in the log:

1. the search widget on the hotel's website;
2. the calendar in the SimpleBooking UI;
3. **landing on the IBE with dates and guests already filled in from the query string.**

One search per intent: re-renders, pagination and filter changes do **not** multiply it.
A new search is recorded only when **the dates or the guests change**.

Route 3 is why per-source figures need care — see §5.

**The outcome is clean.** `NumberOfSolutions = 0` means no bookable combination existed
for those parameters. Malformed searches, abandoned ones and impossible guest
compositions are rejected upstream and never enter the log. A zero is therefore a real
refusal, and can be reported as one.

`NumberOfSolutions > 0` means at least one room-type × rate-plan × meal-plan combination
was available and bookable for the requested parameters.

---

## 2. Grammar

Identical to `run_reservation_aggregation` — same request shape, same operators, same
"one entry per facet across the three filter families", same `sort` values. Everything is
top-level: there is no nested scope, so no equivalent of the `RoomsRatePlanNested` trap.

```json
{ "request": {
    "propertyIds": [ "<PROPERTY_ID>" ],
    "filters":    { "keyword": [], "numeric": [], "date": [] },
    "dimensions": [ { "terms|calendar": {}, "name": "", "size": 0, "sort": "", "metrics": [] } ],
    "metrics":    [ { "searchesCount|measure+statistic|distinctCountOf": "" } ] } }
```

| Family | Facets |
|---|---|
| Filters — keyword | `CustomerCountryCode`, `DeviceType`, `PropertyId`, `Source` |
| Filters — numeric | `DaysInAdvance`, `Nights`, `NumberOfPersons`, `NumberOfRooms`, `NumberOfSolutions`, `RoomNights` |
| Filters — date | `SearchDate`, `CheckInDate`, `CheckOutDate`, `StayDate` |
| Dimensions — terms | `CustomerCountryCode`, `DeviceType`, `HasSolutions`, `Nights`, `NumberOfAdults`, `NumberOfKids`, `NumberOfPersons`, `NumberOfRooms`, `NumberOfSolutions`, `Property`, `Source` |
| Dimensions — calendar | `SearchDate` (accepts `Hour` and `timeZone`), `CheckInDate`, `CheckOutDate`, `StayDate` (whole-day, **no** `timeZone`) |
| Measures | `DaysInAdvance`, `Nights`, `RoomNights`, `NumberOfAdults`, `NumberOfKids`, `NumberOfPersons`, `NumberOfRooms`, `NumberOfSolutions`, `NumberOfOffers`, `NumberOfMealPlans` |
| `distinctCountOf` | `CustomerCountryCode`, `DeviceType`, `Property`, `SessionId`, `Source`, `VisitorGuid` |

`Property` buckets resolve to `Name (ID)`.

**`NumberOfAdults` and `NumberOfKids` are not filterable** — they are dimensions and
measures only. Family demand is read from a bucket, never isolated with a filter.

> **Enum fallback.** This connector's published schema has lagged behind its validator.
> Don't probe it preemptively — but **if a call is rejected on a `facet`, the validation
> message lists the real enum**: read it and retry. That is the correct recovery, and it
> keeps this skill working across connector changes without an edit.

---

## 3. Four mechanical guardrails

**`StayDate` buckets are not additive.** The facet spreads a search across every night of
its stay, so a search spanning two months is counted in both buckets. Their sum exceeds
the matched-search total. Never render them as shares; never let a percentage be computed
over them. When you need additive buckets — one search in exactly one bucket — use
`CheckInDate`.

**The `StayDate` dimension ignores the `StayDate` filter.** The filter selects the
*search*; the dimension then expands *all* of that search's nights, including nights
outside the filtered range. This is expected behaviour and will not be fixed: intersecting
them would require scripted date-histogram aggregations, which this Elasticsearch version
does not support. **Read only the buckets inside the filtered window.** Anything outside
it is the tail of long stays, not demand for the period.

**`size` is ignored on `calendar` dimensions**, on this tool and on
`run_reservation_aggregation` alike — date histograms in Elasticsearch 6.4.2 do not
support it — and zero-count buckets are emitted too. There is no way to cap the response
downstream, so **size the window upstream**. Never use `Hour` over more than a few days.

**One `distinctCountOf` per request.** Sessions and visitors cost two calls.

---

## 4. History floor — 2025-01-01

Before 2025 the search log was polluted by scrapers; bot and scraping protection was
rolled out gradually through 2024, reaching full effect around the end of that year. The
resulting series falls by roughly a factor of three across 2024 — a ramp, not a step, so
there is no clean earlier point to anchor on.

> **No series and no comparison crosses 2025-01-01.** Earlier data is not a stronger
> year, it is a different population.

Configured as `property_demand.history_floor` in `config/defaults.yaml`.

---

## 5. `Source` — shared vocabulary, uneven denominator

The same values appear in the `Source` field of reservations, which is what makes a
search→booking ratio possible at all. **Typical coverage is around 15%**: most searches
carry no `Source`. State the coverage every time a per-source figure is shown.

**The denominator is not homogeneous.** Because landing on the IBE with dates pre-filled
counts as a search (§1, route 3), metasearch searches are *automatic landings*, not
deliberate intents — one landing, one search, until the guest changes dates or guests. A
website-widget search is a deliberate intent.

> **Guardrail.** Never rank metasearch sources and site sources in one list. They have
> different denominators. Present them side by side, labelled, or compare a source only
> against **itself over time** — where the denominator stays homogeneous with itself.

**Census, never an expected list.** `Source` is free text by design: spelling variants of
the same channel coexist in the same field, and device markers appear alongside real
sources. Always read the values with a high `size` before filtering on any of them.

Detailed provenance analysis belongs to `sb-direct-attribution`, not here — this skill
uses `Source` only where a lens needs it, and defers the funnel to that skill.

---

## 6. What this tool cannot do

- **No price.** You know how many solutions the guest saw, never at what price. "Did they
  leave because I was expensive?" is not answerable here.
- **No product identity.** `NumberOfOffers` and `NumberOfMealPlans` are counts: how many
  offers were shown, not which.
- **No join key with reservations.** `SessionId` and `VisitorGuid` exist here and have no
  counterpart on a reservation. Search→booking is a **ratio between aggregates, never an
  attribution.** Say so whenever one is reported.

---

## 7. Equivalence map across the three sources

The front-office field names will be aligned with these at some point but are not today.
**This table is the single place to update when that happens** — every lens references it
rather than restating the mapping.

| Concept | This tool (Back Office) | `destination_demands` (IBE, via `sb-revenue-lens`) | `run_reservation_aggregation` (Back Office) |
|---|---|---|---|
| event time | `SearchDate` | `searchTimestampUTC` | `RegistrationDate` |
| requested check-in | `CheckInDate` | `checkInDate` | `CheckInDate` |
| nights of the stay | `StayDate` | `datesOfStay` | — |
| lead time | `DaysInAdvance` | `daysAhead` | `DaysInAdvance` |
| length of stay | `Nights` | `numberOfNights` | `Nights` |
| room-nights | `RoomNights` | `numberOfRoomNights` | `RoomNights` |
| persons / adults / kids | `NumberOfPersons` / `NumberOfAdults` / `NumberOfKids` | `numberOfPersons` / `numberOfAdults` / `numberOfKids` | same |
| outcome | `HasSolutions`, `NumberOfSolutions` | `hasResults` | `ReservationStatusSimplified` |
| guest country | `CustomerCountryCode` | `user.countryCode` | `CustomerCountryCode` |
| device | `DeviceType` | `user.deviceType` | `Channel` (mixed with commercial channel) |

**Two differences that are not naming.** `DeviceType` here has only `Desktop` and
`Mobile`; the IBE report also has `Tablet`. **One-way rule: fold IBE `Tablet` into Mobile
before any comparison, never the reverse.** And the perimeters differ by design — the IBE
report covers a radius around the property, this tool covers the property itself. They are
the two ends of the triangle, not substitutes.

> **Name trap.** `property_destination_demands_run_report` is the IBE tool that
> `sb-revenue-lens` uses. `destination_demands_run_report`, almost identically named, is
> the Zucchetti Data Lake tool and is **not** available to customers. Never reach for the
> second one from this skill's orchestration.

---

## 8. Reference queries

### 8.1 Denied demand, by check-in month

`CheckInDate`, not `StayDate`: additive buckets are required here.

```json
{ "request": {
  "propertyIds": [ "<PROPERTY_ID>" ],
  "filters": { "date":    [ { "facet": "SearchDate", "between": { "from": "<FROM>", "to": "<TO>" }, "timeZone": "<TZ>" } ],
               "numeric": [ { "facet": "NumberOfSolutions", "equalTo": 0 } ] },
  "metrics": [ { "name": "denied", "searchesCount": true } ],
  "dimensions": [
    { "name": "checkin_month", "calendar": { "facet": "CheckInDate", "interval": "Month" }, "sort": "ByKeyAscending",
      "metrics": [ { "name": "denied", "searchesCount": true },
                   { "name": "room_nights", "measure": "RoomNights", "statistic": "Sum" } ] },
    { "name": "denied_los", "terms": { "facet": "Nights" },          "size": 12 },
    { "name": "denied_pax", "terms": { "facet": "NumberOfPersons" }, "size": 10 } ] } }
```

Pair it with the same window unfiltered to get the denominator: the denied **share** is
the readable figure, the count alone moves with traffic.

Label the room-nights **requested and not served**, never "lost": there is no dedup key
(§6), so several searches by one guest inflate it.

### 8.2 Demand pressure per night

```json
{ "request": {
  "propertyIds": [ "<PROPERTY_ID>" ],
  "filters": { "date": [ { "facet": "SearchDate", "between": { "from": "<FROM>", "to": "<TO>" } },
                         { "facet": "StayDate",   "between": { "from": "<STAY_FROM>", "to": "<STAY_TO>" } } ] },
  "dimensions": [
    { "name": "night", "calendar": { "facet": "StayDate", "interval": "Day" }, "sort": "ByKeyAscending",
      "metrics": [ { "name": "searches", "searchesCount": true },
                   { "name": "avg_solutions", "measure": "NumberOfSolutions", "statistic": "Average" } ] } ] } }
```

**Read only the nights inside `<STAY_FROM>`..`<STAY_TO>`** (§3). A night with meaningful
search volume and an average solutions count near zero is a night the guest asked for and
could not have — measured from the guest's side rather than inferred from the availability
calendar.

### 8.3 Own funnel mix

Root metrics plus one terms dimension: `CustomerCountryCode` for markets, `DeviceType` for
device, `Nights` for the LOS mix, `DaysInAdvance` as an average for lead time. All cheap,
all additive, all comparable against the equivalent reservation-side figure through §7.
