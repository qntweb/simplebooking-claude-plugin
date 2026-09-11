# sb-revenue-lens — Branded report structure (`report` mode)

The report is signed **SimpleBooking** and written for the hotelier. Formats:
PDF/HTML (reusing the existing docx/pdf/HTML helpers). Language = conversation.

## Sections (in order)

1. **Header** — SimpleBooking logo, hotel name, stars, city, period analyzed,
   analysis date, area demand radius used.

2. **The question** — the hotelier's question in plain language (e.g. "Where
   am I leaving money on the table in June?") and which lenses were triggered.

3. **One-line summary** — the key message for the property.

4. **Period overview** — area demand curve per week (table + chart), average
   lead time, requested LOS distribution. Label: "destination demand, not the
   hotel's own".

   *Tier 2, when available:* a **second, separate** block — searches on this
   property's own booking engine per night, with the average number of
   solutions found. Two labelled blocks, never one overlaid chart: the two
   series count different populations (a radius full of properties against one
   booking engine) and their levels are not comparable. Lead time comes from
   your own searchers when this tier is present; say which source was used.
   When the tier was unavailable, this block is simply absent — don't leave a
   placeholder.

5. **Signals per lens** — a subsection for each triggered lens:
   - what the detector found (rule → dates),
   - evidence table (Date | Availability | Nightly price | Weekly demand),
   - plain-language reading,
   - operational options (not prescriptions).

6. **Date map** — calendar of the period with coding:
   🔴 sold-out · 🟠 tight/leak · 🟡 gap-night/MinLOS · 🟢 soft/unsold.

7. **What this analysis does NOT see** — fixed block: no on-the-books, no
   pickup, no real competitors (only OTA parity if active), no events source.
   Fact vs inference.

   Add, always: **no price the guest was shown**, **no product identity**
   (offers and meal plans are counted, not named), **no link between a search
   and a booking** — neither demand series is sales.

   And, when Tier 2 was unavailable, one line saying so: first-party demand was
   not read in this run, so L3c did not run and L1b/L1c/L2/L5 used their
   area-demand form. State it once, here, and nowhere else.

8. **Events** — space for the hotelier: "you're full/empty on these dates —
   do you know of any events or fairs?" (the skill never asserts them).

9. **Next steps** — options + offer of a scheduled scan / portfolio batch.

## Style rules
- No RMS jargon. Short sentences.
- Every number has its source in the evidence table.
- Recommendations are **conditional options** ("if demand holds, …"), never orders.
- Section 7 (limits) is always present.
