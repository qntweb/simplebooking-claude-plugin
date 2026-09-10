# Field semantics and coverage

Many fields in this tool are not populated everywhere. The key distinction is between what **holds on any property** and what **depends on the individual property's configuration**: the first can be assumed, the second must be measured every time.

---

## Platform behaviour — holds everywhere

### Very few channels transmit commission

`CommissionAmount` is populated **only by Expedia, Booking and Agoda**. Every other connectable channel — over a hundred of them — does not send it via API alongside the reservation.

**A zero says nothing about cost.** Behind a channel at zero there are two opposite situations that the data cannot separate:

| Model | What happens | How it looks |
|---|---|---|
| **Net rate** (bedbank, wholesaler, tour operator) | no commission exists: the margin sits inside the price | recorded ADR is **already net**, and lower |
| **Gross rate, not transmitted** | commission exists and is owed, but never arrives via API | recorded ADR is **gross**, the cost is **invisible** |

The second case is treacherous: that channel appears **artificially high** in any net-ADR ranking, precisely because its cost is missing. Separating the two models requires the **contract**, not the data.

**Commission values can be negative.** Chargebacks and corrections appear as negative amounts, so a `Min` below zero is normal rather than a data error. Two consequences: a `Sum` is already net of those corrections without anything signalling it, and the presence check must be read as "is `Max` non-zero", not "is `Min` zero".

**The problem does not arise everywhere, though.** Many small properties work with very few portals — typically Booking for Europe, Expedia for the US, Agoda for Asia: exactly the three that transmit. On those properties coverage is effectively complete. The coverage check is what tells you, property by property.

### Guest country comes from only some portals

`CustomerCountryCode`:

- On **direct** bookings it is populated almost always (around 99%).
- On **intermediated** bookings it arrives only from **Booking and HotelBeds**. Expedia, Agoda and Ctrip **never transmit it**.

Consequence: on a heavily intermediated property overall coverage can fall below 30%, and a source-market ranking computed across all channels is really a ranking of direct bookings with some noise on top. **Filter `ChannelType = Direct`** and say so.

It exists only as a **dimension**, not as a filter: you cannot isolate a single market, you read it from the bucket. And the vocabulary is **not normalised** — variants of the same country (`GB` / `UK`) can coexist as separate buckets in the same data.

**`CustomerCountryName` no longer exists as a facet** (confirmed live, 2026-09-08: the tool rejects it in a `terms` dimension with a validation error listing the current enum). Earlier revisions of this file documented a `CustomerCountryName` / `CustomerCountryCode` pair; only the code remains. There is no resolved, human-readable country name available from this tool any more — normalise the ISO code yourself if a report needs a readable market name.

### `TotalReservationServicesRevenue` is exactly zero on intermediated bookings

Always, on every property: an OTA does not sell booking-engine services. Ancillary penetration must be computed on **direct only**, otherwise it is halved for no reason.

`TotalReservationServicesRevenue` is **not filterable** (it is not among the filter facets): you cannot count how many reservations contain at least one service. Penetration is measurable in currency, not as a share of reservations. `Average` and `Max` are the available proxy — a low average with a high maximum means a few valuable purchases, not many small ones.

Formerly named `TotalServices` — the connector renamed the measure (confirmed in production 2026-08-26); same meaning, same value.

**Itemized detail is now available.** A `Service` terms facet (nested-scope, non-additive, same
family as `RoomType`/`RatePlan`/`Offer`) groups by the individual product sold — names resolve
(`Transfer Florence`, `Early check in`, `Buffet Breakfast`, ...) — with two nested-scope measures,
`ServiceRevenue` (Sum/Average/Max per product) and `ServiceQuantitySold`. This is what turns "how
much ancillary" into "which product" — see `mechanics.md` and `use-cases.md` Case 13. It does not
lift the filtering limit above: you still cannot isolate "reservations that bought service X" as
a filter clause, only read it from the bucket.

### `Portal` is almost always empty — use `Source`, or `DistributionChannel` for a clean name

`Portal` is only populated for reservations coming through the *portal* edition of Simple Booking, which is barely used today: in practice it produces no buckets.

**Read the originating portal from `Source`**, which covers 100% of intermediated bookings with the channel code (`EXPEDIA`, `BOOKINGXML`, `AGODAV7`, `HotelBedsXml`, and dozens of others depending on which connections are live).

**Not to be confused with `DistributionChannel`** (below) — a different, newer field despite the
similar-sounding name. `Portal` is the near-dead one; `DistributionChannel` is fully populated on
indirect bookings.

### `DistributionChannel`: resolved OTA names, indirect only

A terms facet, root-scope and additive like `Source` — not nested. Bucket keys resolve to a
readable `Name (Code)`, e.g. `Booking.com (XML) (BOOKINGXML)`.

**Coverage is not guaranteed on direct bookings.** On a property tested end to end,
`ChannelType = Indirect` bookings had 100% coverage, while `ChannelType = Direct`
bookings had 0% — the field is simply not populated on the direct side. On indirect
bookings its counts matched `Source` one for one (same OTAs, same counts), the only
difference being a readable brand name instead of a code.

**Prefer it for an OTA mix that will be read by someone**, since it needs no normalization or
code-to-brand lookup. `Source` remains the only field with content on direct, and the one to
cross-reference against `CommissionAmount` per portal.

### Ignore `TotalTaxes`

Its content is undetermined and its population irregular: in real data the field was populated almost exclusively by one portal, for a tiny fraction of revenue.

**Operating rule: keep it out of every calculation.** In particular, do **not** use `(TotalStay − TotalTaxes) / RoomNights` for a net ADR: that would subtract an amount of unknown nature, unevenly distributed across channels, producing a silent and non-uniform error. Report ADR **as recorded**.

### Currencies are summed without warning

`TotalStay` and `TotalReservationRevenue` are summed across different currencies with no signal in the output. Over a multi-country perimeter the total is meaningless — a single high-denomination currency can dominate the aggregate.

**Two-second check:** a `terms: { "facet": "Currency" }` dimension. If more than one bucket comes back, either filter `CurrencyCode` or do not sum amounts.

---

## Property configuration — measure it every time

| Variable | Why it varies |
|---|---|
| **Commission rate** | it is contractual. The same OTA can charge very different rates to two properties: **never reuse** a rate observed elsewhere |
| **Connected portals** | from three to more than a dozen. The intermediated `Source` vocabulary must be censused per property |
| **Dominant portal** | never assumable: different OTAs dominate on different properties depending on the markets served |
| **Direct share** | enormous range, from a few percentage points to more than half of revenue |
| **`PaymentMethod` coverage** | from around 5% to over 90% depending on the property |
| **Ancillary penetration** | from near zero to more than 20% of direct revenue. Not a platform limitation — a commercial choice |
| **UTM usage** | depends on which integrations are active |

---

## `Source`: a field with two natures

**On intermediated bookings** it is a system field: portal code, full coverage, controlled vocabulary. It is the key to the real OTA mix and to per-portal cost.

**On direct bookings** it is a **hybrid**, partly written by the system and partly populated **via query string** on the link into the booking engine, when the visit converts. Typical coverage is roughly a quarter to a third.

Three families of values coexist in the same field:

| Family | Who writes it | What it indicates |
|---|---|---|
| Interface | system | the device or surface used to book |
| Manual entry (`PrenMan`) | system | reservation **typed by staff in Back Office** — phone, email, walk-in, groups |
| Tracking | whoever builds the link | the origin or campaign the hotel wants to track — metasearch, newsletter, CRM, QR code |

**The field therefore mixes different semantic levels**: an "interface" bucket sits next to a "campaign" bucket and a "typed by hand" bucket. They do not answer the same question and their shares are not comparable with each other. On a new property, ask the hotel **what its values mean** — the hotel defines them.

### `PrenMan` as an indicator

It identifies **manual Back Office entry**, always — that part of the indicator is unchanged and clean. **Correction (2026-09-08, supersedes the earlier claim on this line): a CRM / Quote Manager push is not automatically excluded from it.** For Converto (SimpleBooking's own built-in CRM & Quote Manager — see "Converto quote provenance" below), the business model explains exactly why:

- **The guest converts the quote autonomously.** Staff draft a quote in Converto from the guest's request; the guest independently opens it, lands on their own dedicated mini-site, chooses among the proposals, optionally adds services, and books **without any human step at the close**. This reservation carries `FromConvertoQuote = true` / `ConvertoQuoteId`, and `Source` is **not** `PrenMan` (it reflects the booking interface instead — typically `MOBILE`, or no value at all on desktop).
- **The guest instead confirms by phone (or otherwise, off the mini-site).** Staff, starting from the same quote, key the confirmed reservation into Back Office by hand. This reservation **also** carries `FromConvertoQuote = true` / `ConvertoQuoteId` — **and** `Source = PrenMan`, because a human did in fact type it in. The two facts are not in tension: `PrenMan` records *how* it entered the system, `ConvertoQuoteId` records *where the demand came from*.

Confirmed live, platform-wide (2026-09-08): of every `ConvertoQuoteId hasValue: true` reservation, `Channel = Website` accounts for 639,226 and `Channel = Mobile` for 409,122 (both interface values, additive, always populated); of the `Website` share, exactly 336,609 carry `Source = PrenMan` — the operator-confirmed path — and the remainder converted with no staff involvement at the close. `Channel` reconciles exactly to the `ConvertoQuoteId` total; `Source` does not, because it is optional on direct bookings generally (see above) — the gap is not a third, unexplained path, it is the ordinary Source-coverage gap.

Manual entry should stay **residual** once the Converto share is accounted for. When what remains weighs heavily, it usually means: the property has meaningful phone or repeat-guest volume **without a dedicated tool** and is handling it by hand, or staff are bypassing the booking engine. `ConvertoQuoteId hasValue: true AND Source = PrenMan` isolates the operator-confirmed quote share precisely; everything else in `PrenMan` is the older, less legible kind.

In an **attribution** analysis, `PrenMan` reservations are conventionally excluded because they never had a web session. That convention now needs a carve-out: the operator-confirmed Converto share **did** originate from an identifiable source — a staff-drafted quote — and dropping it along with genuine phone/walk-in noise understates real CRM/quote-tool business. `sb-direct-attribution` implements this carve-out (see its `SKILL.md` — band "Vendita assistita da persone" — and `scripts/engine.py`); a manual query should do the same by filtering `ConvertoQuoteId` before excluding the rest of `PrenMan`.

### Two `Source` values worth knowing by name

Most values are self-explanatory from their code. Two are not, and both were confirmed live on
2026-08-27:

- **`rezmate.ai`** — the AI concierge embedded natively in Simple Booking on the hotel's own
  website. It answers questions about the property from an extended knowledge base and can walk
  a guest into a same-session booking on the engine. To measure what it drove, filter `Source`
  `equalTo` `"rezmate.ai"` — verify the exact spelling per property first (`Source` is free
  text), same discipline as any other census. Adoption varies widely: a platform-wide scan
  (2024-09 to 2026-08, no `propertyIds`) returned 146 bookings across roughly 50 properties, from
  a single booking up to 22 on the busiest one.
- **The channel referred to informally as "Imperatore" or "Imperatore Travel" has changed
  `Source` more than once.** It has moved connection platform to the channel manager several
  times, leaving **three** distinct codes behind: `IVECTOR`, `IMPERATOUR`, `IMPERATOREJUN`
  (confirmed live, platform-wide: 1,956 / 538 / 10 bookings respectively). **A question about
  "Imperatore" volume must aggregate all three** (the keyword `in` operator) — reading only one silently
  misses the other eras, and `DistributionChannel` does not merge them into one brand either
  (`IVector (XML)`, `Imperatour (XML)`, `Imperatore Juniper (XML)` are three separate buckets).
  Ask whether a newer code has appeared if the property is still active on that channel.

### Converto quote provenance — `ConvertoQuoteId` / `FromConvertoQuote`

New (confirmed live, 2026-09-08): the tool can now identify reservations that originated as a
quote converted through Converto, SimpleBooking's own CRM & Quote Manager. Exposed **two ways**,
not one:

| Form | Kind | How to use it |
|---|---|---|
| `FromConvertoQuote` | **dimension only** (`terms`), boolean bucket keys `true`/`false` | group by it; **rejected as a filter facet** |
| `ConvertoQuoteId` | **numeric filter only** (`hasValue`, `equalTo`, `in`, `between`) | `hasValue: true` isolates the converted-quote reservations; **not a dimension, not a metric, not a `distinctCountOf` target** |

Root-scope and additive — `docCount` equals `reservationsCount` on the `FromConvertoQuote`
dimension, unlike the nested `RoomType`/`RatePlan`/`Offer`/`Service` family.

**Platform-wide adoption is real, not a rounding artefact**: a scan with no `propertyIds`
(2026-09-08) returned 1,050,914 reservations with `FromConvertoQuote = true` out of 11,996,303
total — about 8.8%. Nearly all of it is direct: filtering `ConvertoQuoteId hasValue: true` by
`ChannelType` gave 1,050,868 `Direct` against 54 `Indirect`.

**The two exposures do not reconcile exactly.** `FromConvertoQuote = true` bucketed 1,050,914;
`ConvertoQuoteId hasValue: true` matched 1,050,916 — a gap of 2 out of over a million, with no
known cause. Same discipline as the `TotalReceived` / `TransactorPaidAmount` gap elsewhere in
this file: report the figure, flag the gap, do not explain it away.

**It does not correlate with any distinct `Source` tag — by design, not by gap in the data.**
Grouping `ConvertoQuoteId hasValue: true` reservations by `Source` (platform-wide, 2026-09-08)
returned `MOBILE` (409,092), `PrenMan` (336,566), `REENGAGEMENT` (1), and roughly 305,000 with no
`Source` value at all. There is no "Converto" or "Quote Manager" string anywhere in `Source` —
the field records the technical interface or the manual-entry marker, which is a different
question from whether a Converto quote sat behind the booking. **A Source-based lookup can never
identify these reservations**; `ConvertoQuoteId` is the only way.

**The business model behind the split** (confirmed with the product team, 2026-09-08): a Converto
quote converts in one of two ways, and both carry `ConvertoQuoteId` regardless of which.

1. **The guest converts autonomously.** Staff draft the quote in Converto; the guest opens it
   independently, lands on their own dedicated mini-site, chooses among the proposals — optionally
   adding services — and books with no human step at the close. `Source` reflects the technical
   interface here (`MOBILE` on a phone, no value on desktop), never `PrenMan`.
2. **The guest confirms off the mini-site — by phone, typically —** and staff, starting from the
   same quote, key the confirmed reservation into Back Office by hand. This carries `ConvertoQuoteId`
   **and** `Source = PrenMan`: a human did type it in, that part of `PrenMan`'s meaning holds:
   see the correction above.

`Channel` (not `Source`) reconciles exactly to the two paths: `Website` (639,226) and `Mobile`
(409,122) together account for the full `ConvertoQuoteId` population, and of the `Website` share,
exactly 336,609 carry `Source = PrenMan` — the operator-confirmed path. `Source`'s own coverage
gap (the ~305,000 with no value) is the ordinary direct-booking Source gap documented above, not
a third unexplained path.

See `sb-direct-attribution`'s `config/known-sources.yaml`, where the "Converto CRM & Quote
Manager" comment now documents that no `Source` tag will ever exist for this product — and its
`scripts/engine.py`, which implements the operator-confirmed / autonomous split as its own
classification path, independent of `Source`/utm string matching.

---

## `PaymentMethod`

Six values, closed and confirmed vocabulary:

| Code | Meaning |
|---|---|
| `CC` | **Credit Card** — card taken **as a guarantee**, no charge made by the platform |
| `TR` | **Transactor** — transaction **actually executed** through the payment gateway |
| `BT` | **Bank Transfer** |
| `NM` | **No Method** — no payment method recorded |
| `PT` | National Postal Transfer — legacy Italian instrument, **effectively extinct** |
| `MT` | Postal Money Transfer — legacy Italian instrument, **effectively extinct** |

`PT` and `MT` are statistically irrelevant: treat them as noise, not as categories.

**The field distinguishes platform-handled collection from a mere guarantee, not prepaid from pay-at-hotel.** A `CC` reservation may well have been charged manually by the hotel later: the field records what the platform did, not what the property did.

The vocabulary **in use** varies by property: some use only `CC`, others the full range. Always start with a census call.

### The amount actually collected — `TotalReceived` and `TransactorPaidAmount`

Two measures expose it: `TotalReceived` (root-scope, any payment method) and
`TransactorPaidAmount` (root-scope, gateway settlements only). A `PaymentTransactor` terms facet
resolves **which gateway** processed the payment (`Carta Si - Nexi Online`, `ScalaPay`, and so
on) — a fifth nested-style facet alongside `RoomType`/`RatePlan`/`Offer`/`Service`? **No** —
unlike those, `PaymentTransactor` is **root-scope and additive**: bucket counts sum to the
matched total, same as `ChannelType` or `PaymentMethod`.

**Coverage is concentrated on `TR`, not universal — validated on two properties.** `TotalReceived`
was essentially zero on `CreditCard` (consistent with `CC` being a guarantee, never a platform
charge) and negligible on `BankTransfer` and `NoMethod`, but substantial wherever `PaymentMethod`
is `Transactor`. Read `TotalReceived` as **"what the gateway settled"**, not as a generic
collected-amount figure that covers every payment method despite its generic name — measure the
coverage per property before leaning on it, same as any other field here.

**`TotalReceived` and `TransactorPaidAmount` do not always match, even filtered to `Transactor`
alone.** A gap of roughly 1% was observed with no known cause. Do not assume they reconcile:
report `TotalReceived` as the headline figure, and if both are shown, flag the discrepancy rather
than explaining it away.

This still does not make a full cash forecast possible: on a `TR` booking there is no way to tell
from these figures alone whether a given reservation's collected amount is the full stay or a
partial deposit with the balance due on arrival — `TotalReceived` gives the aggregate collected,
not a per-booking prepaid/pay-at-hotel split.

---

## Tracking fields (UTM)

Coverage is typically **low**: across a broad sample, fewer than one in five direct bookings carries a UTM. Always read the campaign ranking *within* that coverage, never as a distribution of direct business.

**The missing value comes back as an empty-key bucket**, not as an absent row: coverage is readable straight from the output.

**The vocabulary is heavily fragmented** — hundreds of distinct values, with duplicates differing only in capitalisation or language. Variants of the same concept sit in separate buckets, so **normalisation is a prerequisite**, not a polish step: without it a channel is split across several rows and understated.

Values that are not sources also appear: error strings such as `undefined` (a malformed link, worth flagging to the hotel) and **referrer domains captured automatically**, recognisable because they carry no `utm_medium`.

**`TrackingUtmMedium` is far cleaner than `TrackingUtmSource`** and often the better root dimension: starting from medium and descending into source gives a readable ranking without normalising first.

Finally: these counts are **last-touch, booking-engine side**. They are not additive with, or comparable to, Google Ads, Meta or GA4, which use different attribution models.

---

## The principle to apply to any field

**When a field is empty, absent or ambiguous in content, ask someone who knows the system — do not infer it.**

The experience behind this rule: repeatedly, the most elegant interpretation of an ambiguous value turned out to be wrong, and every time **the resulting number still looked plausible**. A misread field does not produce a visible error — it produces a sensible, false table.

In practice: a field whose content you do not know stays **out of the calculation** and goes back to the user as a question, rather than being filled with the assumption that makes the figures work.
