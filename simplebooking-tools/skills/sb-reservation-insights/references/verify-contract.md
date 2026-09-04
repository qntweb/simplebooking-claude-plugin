# Input contract for `scripts/verify.py`

The tool returns buckets. Everything past them — ADR, coverage, bands, the STLY
subtraction — is arithmetic done by hand, and a mistake there does not raise an error: it
produces a table that reads correctly. This script re-derives those figures from the same
buckets and refuses the ones that do not hold.

Write a JSON file anywhere you like — the script takes its path as the only argument —
run it, and read the answer only if it exits zero.

```bash
python3 <skill-dir>/scripts/verify.py claims.json   # absolute path to this skill's folder
```

`0` nothing blocking · `1` at least one figure is wrong · `2` the file itself is unusable.

Every block is optional — declare only what the answer leans on. Any block may also be a
**list** of objects, to check several perimeters in one run; give each a `label` so the
output names them.

---

## `revenue` — the components add up

```json
{ "revenue": { "label": "settembre, diretto",
               "total_stay": 48250.00,
               "total_services": 1310.50,
               "total_reservation_revenue": 49560.50,
               "channel_type": "Direct" } }
```

Checks `TotalStay + TotalReservationServicesRevenue = TotalReservationRevenue` (the JSON key
here stays `total_services` — this contract's own field name, independent of the MCP measure
name). `channel_type` is optional; set
it to `Indirect` and the script also enforces that services are exactly zero, which is the
fastest way to discover that a perimeter is not the one you meant.

## `adr` — divided by the right things

```json
{ "adr": { "total_stay": 48250.00, "room_nights": 341, "adr": 141.49 } }
```

Recomputes `total_stay / room_nights`. Catches the two classic slips: dividing
`TotalReservationRevenue` instead, and reporting an ADR when room nights are zero.

Use this for **computed** ADR only. The engine `Adr` measure is an unweighted average over
nested entries — a different quantity, not comparable, and not something this script can
re-derive.

## `coverage` — the denominator is real

```json
{ "coverage": { "label": "utm_source, direct only",
                "parent_count": 412,
                "buckets": [61, 24, 12, 9],
                "claimed_coverage": 0.2573 } }
```

`buckets` are the per-bucket counts, `parent_count` the count they sit inside. Unpopulated
rows do not appear in keyword buckets, so coverage is their sum over the parent.
`claimed_coverage` is optional: supply it and the script checks the figure you were about to
write. Coverage under 25% is a warning, not an error — you may report it, but say so.

If the buckets exceed the parent you are on a **non-additive** facet (`RoomType`, `RatePlan`,
`Offer`): coverage is the wrong reading there, and the script says so rather than computing a
number above 100%.

## `bands` — exhaustive and disjoint

```json
{ "bands": { "period_total": 412,
             "bands": [ { "label": "0-7",  "from": 0,  "to": 7,    "count": 118 },
                        { "label": "8-30", "from": 8,  "to": 30,   "count": 165 },
                        { "label": "31+",  "from": 31, "to": null, "count": 129 } ] } }
```

There is no histogram in the tool: bands are separate calls, and they only mean something if
every reservation lands in exactly one. `to: null` is the open upper band. Bounds are
**inclusive on both ends**, so a band starting where the previous one ended double-counts the
boundary — the most common way to build bands that look fine and sum wrong.

Counts that miss the period total are an error; a gap between two bands is a warning, since
occasionally it is deliberate.

## `stly` — the snapshot holds

```json
{ "stly": { "booked_by_snapshot": 388,
            "cancelled_by_snapshot": 47,
            "stly_otb": 341,
            "snapshot_date": "2025-08-23",
            "today": "2026-08-23" } }
```

Checks `stly_otb = booked − cancelled`, that cancellations cannot exceed bookings — if they
do, the two queries are not over the same perimeter — and that the snapshot is exactly one
year before today. The date pair is optional but worth passing: a drifted snapshot leaves the
comparison percentages almost unchanged while distorting the residual pick-up, which is the
figure used to project the close of the month.

## `currency` — one, or no totals

```json
{ "currency": { "currencies": ["EUR"], "amounts_summed": true } }
```

List what a `terms: { "facet": "Currency" }` control dimension returned. More than one code
with `amounts_summed` true is an error: the tool adds amounts across currencies with nothing
in the output to signal it. Set `amounts_summed` to false when you are only comparing shares.
