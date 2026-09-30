# SimpleBooking BackOffice connector

Read-only analytics on a hotel's SimpleBooking Back Office: reservations, searches on
the property's own booking engine, and Converto quotes and customer requests — always as
aggregated reports.

| | |
|---|---|
| Server | `https://mcp.backoffice.simplebooking.it` |
| Transport | Streamable HTTP |
| Authentication | OAuth 2.0 with a SimpleBooking Back Office account |
| Access | read-only — no tool creates, changes or deletes anything |
| Provider | QNT S.r.l. — SimpleBooking, Zucchetti Group |
| Support | helpdesk@simplebooking.it |

## Who can use it

Anyone with a SimpleBooking Back Office account. Signing in grants access only to the
properties that account is authorised for by each property; every query is restricted
to them, and the connector cannot reach any other hotel's data.

## What data it returns

Every tool is an **aggregation**: it filters records, groups them (by date, channel,
room type, rate plan, market, device…) and returns counts, sums and averages. It does
not return individual guest records.

- No guest names, email addresses, postal addresses, phone numbers or payment card
  details are ever returned.
- Guests appear only through non-contact attributes: country of origin, party size,
  length of stay, booking channel.
- Some groupings return **pseudonymous identifiers** the property already holds in its
  own Back Office: reservation codes, advertising click IDs (for campaign attribution),
  and, for Converto, the handling staff member as the first three letters of the first
  name plus a user ID.

## Tools

All tools are read-only.

| Tool | What it aggregates |
|---|---|
| `run_reservation_aggregation` | Reservations: pick-up, on the books, revenue, ADR, channel and portal mix, commissions, cancellations, booking window, length of stay, source markets, services, payment methods, campaign tracking |
| `run_property_demand_aggregation` | Availability searches on the property's own booking engine: volume, dates requested, party size, device, country, searches that found no availability |
| `run_converto_quote_aggregation` | Converto quotes sent to guests: status, conversion, revenue, rooms and rates proposed, handling staff |
| `run_customer_request_aggregation` | Enquiries guests send the property: volume, status, requested stay, source, handling staff |

## Example questions

- "How is September going compared to last year?"
- "How much am I paying OTAs in commission this year?"
- "How many searches on my booking engine found no availability last month?"
- "What share of Converto quotes turned into reservations?"

## Privacy

See the [privacy policy](https://github.com/qntweb/simplebooking-claude-plugin/blob/main/docs/privacy-policy-mcp.md).
