---
name: sb-reservation-insights
metadata:
  author: Sergio Farinelli
  organization: QNT — SimpleBooking — Zucchetti Group
description: >
  Query a hotel's reservations via run_reservation_aggregation of the Simple Booking
  BackOffice MCP, for management, revenue management, front office and marketing. USE FOR:
  pick-up, on the books, "how is the month going", year-over-year pace, channel mix, direct vs
  OTA, commission cost, portal performance, cancellations, booking window, last minute, length
  of stay, MinLOS, arrivals and departures, in-house guests, source markets, ancillary
  services, payment methods; also any question on reservations, rooms sold,
  ADR or revenue without naming the tool. Trigger italiani: camere vendute, come sta andando
  settembre, siamo avanti o indietro, quanto mi costano le OTA, anticipo di prenotazione,
  permanenza media, arrivi e partenze, presenze in casa, mercati di provenienza. NON per:
  provenienza del diretto, UTM, campagne (sb-direct-attribution); date chiuse
  (sb-inventory-guard); tariffe e domanda d'area (sb-revenue-lens); traffico AI
  (sb-ai-traffic); sito (sb-website-audit); domanda vs vendite (sb-demand-capture).
---

# Reservation insights — Simple Booking BackOffice

This skill governs the use of `run_reservation_aggregation`, the single tool of the Simple Booking BackOffice MCP, for everything about reservations. The tool filters reservations, groups them into a tree of dimensions, computes curated metrics, and returns Markdown tables. It also uses one tool of the SimpleBooking IBE MCP, `booking_engine_search_properties`, but only to resolve a property name to its ID before querying — see "Before you start".

**Answer in the language the user writes in.** The reference files are in English; the answers are not.

## Before you start

You need the numeric **Property ID**. If the user names the property without giving it, look it
up first with `booking_engine_search_properties` (SimpleBooking IBE MCP), passing the name — or
the ID itself — as `searchTerm`. It returns `Name (ID)` matches directly, no reservation data
touched. IDs are shared with the BackOffice MCP (the ID a property resolves to on the IBE MCP is
the same one to use on the BackOffice MCP). If several matches come back, or the wording is
ambiguous, **ask** rather than guess — near-identical names coexist across cities (e.g. the same
hotel brand with one property in each of two different cities), and for
a broadly-privileged caller the search spans the **whole platform**, not just this client's group,
so an unrelated same-name hotel elsewhere is a real possibility.

**Fall back to the BackOffice-only method only if the IBE MCP is unavailable in this session, or
the search returns nothing** (some properties are queryable in the BackOffice without an active
IBE listing): run a `run_reservation_aggregation` query **without `propertyIds`**, with a single
`terms: { "facet": "Property" }` dimension, a high `size`, only `reservationsCount`, and a narrow
date filter. Buckets come back as `Name (ID)`. This is heavier — it scans the whole accessible
reservation portfolio — so treat it as last resort, not the default. If the name still does not
appear, ask for the ID — **never guess it**.

## Five non-negotiable rules

Each one, if broken, produces numbers that are **plausible and wrong**. These are the errors you cannot catch by rereading the result.

1. **`Adr` is nested-scoped.** It may only sit inside a dimension on `RoomType`, `RatePlan` or `Offer`. Anywhere else the tool rejects the request. **Compute aggregate ADR downstream: `TotalStay / RoomNights`.**

2. **ADR is built on `TotalStay`, never on `TotalReservationRevenue`.** The identity `TotalStay + TotalReservationServicesRevenue = TotalReservationRevenue` holds: the latter includes ancillary services and inflates ADR.

3. **Every dimension level carries its own metrics.** Metrics declared inside a dimension apply to the buckets *at that level*. A sub-dimension without `metrics` returns only a count.

4. **Measure a field's coverage before reading its distribution.** Many fields are populated only on some channels or some properties. Compare the sum of the buckets against the parent count; if it does not reconcile, the gap is unpopulated data and must be **stated alongside the result**.

5. **When a field is empty, absent or ambiguous, ask what it means — do not infer it.** A missing value admits opposite explanations that the data cannot separate.

## Workflow

1. **Identify the property and the period**, distinguishing *stay* (`CheckInDate`) from *booking* (`RegistrationDate`). This single choice changes the meaning of the answer more than anything else. **If the period is not stated and not inferable from context, ask.** Only fall back to a sensible default when asking would break the flow of an otherwise-clear conversation — and when you do, **state the period you used in the answer**, never silently.
2. **Check coverage** for any field beyond the basics.
3. **Build one call where possible** — the dimension tree usually removes the need for several.
4. **Check the arithmetic before answering.** The tool returns buckets; ADR, coverage, bands and the STLY subtraction are computed by hand, and an error there does not surface — it produces a table that reads correctly. Write the figures into a JSON file and run:

   ```bash
   python3 <skill-dir>/scripts/verify.py claims.json
   ```

   `<skill-dir>` is the folder this file was loaded from: substitute the real absolute path.
   `${CLAUDE_SKILL_DIR}` holds it in the session types that expand it, but **do not paste that
   token into a shell without checking that it resolved** — an undefined variable becomes an
   empty string, the command turns into `python3 /scripts/verify.py`, and the check silently
   fails to run instead of failing loudly.

   Declare only the blocks the answer leans on (`references/verify-contract.md` has the shape). **If it exits non-zero the numbers do not go out** — fix them or say what does not reconcile. A `[WARN]` is not blocking, but belongs in the answer.

   Skip it for a bare count or a single ranking with no derived figure. Do not skip it for anything with a division, a subtraction across two queries, or a set of bands.

5. **Answer with the number and its limit.** Never a percentage without its denominator, never a ranking without its coverage.

## Where to look

| You need | File |
|---|---|
| Request shape, scoping, revenue identity, time zones, common errors | `references/mechanics.md` |
| What each field contains, how well it is populated, what to ignore | `references/fields.md` |
| Ready-made templates for recurring questions | `references/use-cases.md` |
| Input shape for the arithmetic check | `references/verify-contract.md` |

Paths in this table are relative to this skill's own directory, **not** to the working
directory of the session — the two are almost never the same. Resolve them against the
folder this file was loaded from.

Load the relevant reference **before** building the request, not after an error.

## What this tool cannot tell you

State this upfront rather than approximating:

- **Occupancy and RevPAR** — property capacity is unknown. The tool gives room nights sold; the denominator must come from the user.
- **Night-by-night occupancy curve** — room nights are attributed to the **arrival** date, not spread across the nights of the stay.
- **Returning guests** — there is no guest identifier.
- **Amount collected, per booking** — `TotalReceived` / `TransactorPaidAmount` give the aggregate collected, but coverage sits almost entirely on `PaymentMethod = Transactor`; see `references/fields.md`. There is still no way to tell, for one reservation, whether it was paid in full or as a deposit.
- **True cost of every portal** — only a few channels transmit commission.
- **Competitor rates** — out of scope.

## Tone

The reader is hotel staff, not an analyst. Give the number that matters and the decision it enables, not the shape of the query. Mention a data limitation in one line; do not turn the answer into a list of caveats.
