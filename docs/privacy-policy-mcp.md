# Privacy Policy — SimpleBooking MCP connectors

*Last updated: 30 September 2026*

This policy explains how QNT S.r.l. handles data when you use the SimpleBooking MCP
connectors — **SimpleBooking IBE** (`mcp.ibe.simplebooking.it`) and **SimpleBooking
BackOffice** (`mcp.backoffice.simplebooking.it`) — from an AI assistant such as Claude
or ChatGPT.

## 1. Who we are

QNT S.r.l. a socio unico — Via Lucca 52, 50142 Firenze, Italy — VAT IT02333620488
("QNT", "we"). SimpleBooking is a QNT product, part of the Zucchetti Group.

Privacy contact: **privacy@qnt.it**

## 2. What the connectors do

The connectors let an authorised SimpleBooking user ask an AI assistant questions about
the properties they manage. Both are **read-only**: they return data, and never create,
change or delete anything in SimpleBooking.

## 3. Who can access data

Access requires signing in with OAuth 2.0 using a **SimpleBooking Back Office account**.
Each account reaches only the properties it has been authorised for by each property.
No data of any other property is ever returned.

## 4. What data the connectors return

**Public booking-engine data (IBE connector).** Property descriptions, photos, room
types, rates, offers, packages, services, availability and prices: the same information
any traveller sees on the property's public booking engine. OTA prices are public prices
of online travel agencies.

**Aggregated statistics (both connectors).** Counts, sums and averages over
reservations, booking-engine searches, Converto quotes and customer requests, grouped by
date, channel, room, rate, market, device and similar attributes. Area demand is the
aggregated count of travellers' searches around a property, with no individual search
and no traveller identity.

**What is never returned.** Guest names, email addresses, postal addresses, phone
numbers, identity documents or payment card details.

**Pseudonymous identifiers.** Some aggregations can return identifiers that the
property already holds in its own Back Office: reservation codes, advertising click IDs
used for campaign attribution, and — for Converto quotes and requests — the handling
staff member, shown as the first three letters of the first name and an internal user
ID. They cannot identify a person without access to the property's Back Office, which
only that property's authorised users have.

## 5. Personal data we process

- **Account data of the signed-in user** (Back Office user identifier, and the data
  needed to authenticate and authorise the OAuth session), to grant access to the right
  properties. Legal basis: performance of the SimpleBooking service contract.
- **Technical logs** of connector requests (time, tool called, account, IP address),
  for security, abuse prevention and troubleshooting, kept as provided for the
  SimpleBooking service. Legal basis: legitimate interest in the security of the service.
- **Pseudonymous identifiers** returned by the aggregations (section 4), processed on
  behalf of the property under the existing SimpleBooking agreement, in which QNT acts as
  data processor and the property as data controller.

The connectors are part of the SimpleBooking service. The processing, retention and
location of data follow the same terms that already apply to the property's use of
SimpleBooking under its agreement with QNT.

## 6. The AI assistant you use

When you use a connector, its answers are delivered to the AI assistant you connected it
to (for example Claude by Anthropic or ChatGPT by OpenAI) and become part of your
conversation there. That provider processes the conversation under its own terms and
privacy policy, which QNT does not control. You choose which assistant to connect and
which questions to ask.

## 7. Your rights

Under the GDPR (Regulation (EU) 2016/679) you can request access to, correction or
deletion of your personal data, restrict or object to its processing, and ask for
portability, by writing to **privacy@qnt.it**. You can also lodge a complaint with the
Italian Data Protection Authority (Garante per la protezione dei dati personali,
www.garanteprivacy.it).

For data about guests or staff of a property, the property is the controller: requests
should be addressed to it, and QNT will support it as processor.

## 8. Revoking access

You can disconnect a connector at any time from your AI assistant's settings. Access
also ends when the SimpleBooking account is disabled or loses its authorisation for a
property.

## 9. Changes

If new tools change the data the connectors return, we will update this policy and its
date before they are released.
