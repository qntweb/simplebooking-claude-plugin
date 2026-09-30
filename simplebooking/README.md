# Simple Booking

Four skills that let a hotel ask Claude questions about its own SimpleBooking data —
reservations, revenue, content and demand — and get answers computed from the booking
engine and the Back Office, not estimated. Built for hoteliers, revenue managers and the
agencies that work with them, on the two SimpleBooking MCP connectors.

## Skills

- **sb-reservation-insights** — pick-up, on the books, year-over-year pace, channel mix,
  commission cost, cancellations, booking window, length of stay, arrivals and
  departures, source markets, ancillary services, payment methods.
- **sb-revenue-lens** — demand-driven revenue diagnostic: where money is being lost,
  unsold risk, minimum-stay restrictions against the stays guests search for, direct vs
  OTA rate parity. Answers in chat; on request, a branded HTML report.
- **sb-hotel-content-audit** — completeness and translation audit of the property's
  content (rooms, rates, services, descriptions) across every enabled language.
- **sb-demand-capture** — compares the destination's demand, the searches on the
  property's own booking engine and the reservations actually taken, to tell whether the
  property captures the demand of its destination and, if not, where it loses it.

## Requirements

A SimpleBooking account. The plugin adds two connectors; sign in with that account when
Claude asks:

| Connector | Server | Used for |
|---|---|---|
| SimpleBooking IBE | `https://mcp.ibe.simplebooking.it` | property content, availability, prices, restrictions, area demand |
| SimpleBooking BackOffice | `https://mcp.backoffice.simplebooking.it` | reservations, booking-engine searches |

You only see the properties your account is authorised for.

## What the plugin runs, sends and downloads

- **Network**: the skills call only the two SimpleBooking connectors above, and only
  their read tools (queries and aggregations). Nothing is written back to SimpleBooking.
- **Optional, only if you have connected them yourself**: `sb-hotel-content-audit` can
  add website traffic by language and country from a Google Analytics connector;
  `sb-revenue-lens` can use Claude's web search to suggest events that may explain a
  demand spike, always labelled as a hypothesis. Neither is required, and the plugin
  does not install them.
- **Local scripts**: three Python scripts run on your machine with the standard library
  only and make no network calls — `sb-reservation-insights/scripts/verify.py` and
  `sb-demand-capture/scripts/verify.py` re-check the arithmetic of an answer,
  `sb-revenue-lens/scripts/build_report.py` writes the HTML report to a local file.
- **Downloads**: the HTML report of `sb-revenue-lens` loads Chart.js 4.4.1 from
  `cdnjs.cloudflare.com` when you open it in a browser. Nothing else is downloaded.

## Data

The skills read your property's data through your own SimpleBooking login, with the
permissions that login already has. Reservation figures come from aggregation queries
(counts, room nights, revenue by period, channel, market). The plugin stores nothing
outside your Claude conversation and the report files you choose to generate.

## License

[PolyForm Shield 1.0.0](LICENSE) — © 2025-2026 QNT S.r.l. — Zucchetti Group.
