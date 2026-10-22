# Privacy Policy: Simple Booking Claude Plugin

## 1. Who we are

This plugin is provided by QNT S.r.l. a Single Shareholder, Via Lucca 52, 50142 Florence, Italy, VAT 02333620488 (the "Provider").

- Privacy contact: privacy@qnt.it

## 2. Scope

This policy covers the Simple Booking plugin for Claude, which includes the skills `sb-reservation-insights`, `sb-revenue-lens`, `sb-hotel-content-audit`, and `sb-demand-capture`, together with the two SimpleBooking connectors and the local scripts described in the plugin documentation. The SimpleBooking connectors can also be used from other AI assistants that support them. When you use a connector in another assistant, that assistant's own terms and privacy policy apply to that conversation. This policy covers only use of the plugin with Claude.

It does not cover the Provider's website, the Simple Booking booking engine when used by guests, or Anthropic's own services. Those are governed by their own privacy policies. For the website, see https://www.simplebooking.travel/privacy-policy.

The Simple Booking platform itself processes guest reservation data, including the transmission of reservations to online travel agencies through the channel manager. That processing is governed by the platform's contract and data processing terms with the hotel, not by this plugin policy. This plugin policy covers only the additional processing that occurs when the plugin is used.

## 3. Roles

The plugin is used by hotel operators who hold a SimpleBooking account. For personal data about the hotel's guests, the hotel is generally the **data controller**, and the Provider acts as **data processor** under Article 28 GDPR when it provides SimpleBooking services.

When you use the plugin, you are responsible for how you use the results it produces, including any further sharing of them. The plugin runs on the Claude plan you choose. Section 8 explains how the plan affects the legal basis for transfers to Anthropic, and you should review it with your privacy advisor before connecting the plugin to your account.

## 4. Data processed

The plugin reads data through the account you are signed in with. It processes:

- **Account and access data:** your SimpleBooking login, which is handled by the connector's authentication flow. The plugin does not store your password.
- **Technical logs:** records of connector requests (time, tool called, account, and IP address), kept for security, abuse prevention, and troubleshooting.
- **Property and operational data:** property details, room types, rates, availability, restrictions, and content such as descriptions and translations.
- **Aggregated reservation data:** counts, room nights, revenue by period, booking channel, market of origin, lead time, length of stay, cancellations, and similar figures.
- **Booking engine search data:** aggregated search and demand information from the property's booking engine.
- **Area demand and traffic data:** aggregated searches for stays within a radius of the property, from the SimpleBooking IBE connector, and, where the Google Analytics connector is available in your account, website traffic by language and country.
- **Queries and results:** the parameters of each request sent to the connectors and the aggregated figures returned. Your Claude conversation itself is handled by Anthropic, as described in section 7.

The connectors are available only to the hotel operator, after authentication via OAuth, and return only data relating to the hotel the operator is authorised for. Responses consist mainly of aggregated counts, sums, and averages for statistical analysis of the property.

Responses may also contain technical identifiers in pseudonymous form, relating to bookings or visits of the operator's own hotel: internal reservation codes, and online tracking click identifiers (for example Google, Facebook, Microsoft, and TikTok click IDs). These identifiers do not identify a guest directly, but they can be linked to a booking or a visit within the hotel's own systems. Because the operator already has access to the same data in the Back Office, no disclosure to a third party occurs through the connectors. However, when a response containing such identifiers is part of your Claude conversation, it is transmitted to Anthropic for processing, as described in section 7.

For Converto quotes and customer requests, responses may also show the staff member who handled the item, as the first three letters of the first name and an internal user identifier. This is personal data of property staff, and it is handled under the connector privacy policy.

The plugin does not intentionally collect special categories of data (Article 9 GDPR), and it is not designed to process them. Please do not ask the plugin to process such data.

## 5. Purposes and legal basis

| Purpose | Legal basis (GDPR) |
|---|---|
| Providing the reporting, revenue, and content analysis you request | Performance of a contract (Art. 6(1)(b)) and, where the controller is the hotel, the hotel's legitimate interest in managing its business (Art. 6(1)(f)) |
| Security, troubleshooting, and service integrity | Legitimate interest (Art. 6(1)(f)) |
| Compliance with legal obligations | Art. 6(1)(c) |

## 6. How the plugin works

- The plugin is **read-only**. It runs queries and aggregations against SimpleBooking. It does not write, change, or delete data in SimpleBooking.
- Requests are sent to the SimpleBooking connectors in your name, using your own permissions.
- Responses are processed by Anthropic's model to produce the answer in your conversation.
- Three local scripts run on your device. They use only the Python standard library, make no network calls, and write output files only where you choose.
- The HTML report loads the Chart.js 4.4.1 library from a public content delivery network when opened in a browser. No hotel or guest data is sent to the network. The only data involved is the standard connection information that any website request carries.
- **Additional services used by the skills:**
  - After the audit report, `sb-hotel-content-audit` checks whether a Google Analytics connector is available in your Claude account, by listing the Analytics accounts it can access. In the current version this check runs without a separate confirmation. If you then choose an option that includes website traffic, it queries Google Analytics for website traffic by language and country.
  - `sb-revenue-lens` can use Claude's web search, when it is available, to suggest events that may explain a demand spike. Search queries are sent to the search provider. Any result is presented as a hypothesis, not as a fact.

  The processing by these services is governed by the relevant provider's terms.

## 7. Recipients and sub-processors

- **Anthropic, PBC** (USA): provides the Claude model that processes your conversation. Query parameters and responses from the SimpleBooking connectors and from the additional services described in section 6, including any pseudonymous booking or click identifiers they contain, are transmitted to Anthropic as part of that conversation. The transfer basis depends on your Claude plan, as described in section 8.
- **QNT S.r.l. / Zucchetti Group:** operates the SimpleBooking connectors and the plugin.
- **Optional, when available in your account:** Google LLC, for the Google Analytics connector; and the search provider used by Claude's web search, when it is used.

We do not sell personal data, and we do not use it for advertising.

## 8. International transfers

Anthropic processes data in the United States. The legal basis for that transfer depends on the Claude plan you use:

- **Commercial Claude products** (for example Claude for Work and the Claude API): transfers are covered by Anthropic's Data Processing Addendum, which incorporates the EU Standard Contractual Clauses.
- **Consumer Claude products** (for example Claude Free and Claude Pro): Anthropic's consumer terms and privacy policy apply instead, and the Data Processing Addendum does not. If you use the plugin on a consumer plan, you are responsible for assessing whether that is appropriate for the guest data in your account.

## 9. Retention

- **Plugin:** the plugin does not keep a copy of your data outside your Claude conversation and any report files you save.
- **SimpleBooking connectors:** do not store your Claude conversation. Technical logs of requests are kept for the period set by the SimpleBooking service terms.
- **Claude conversations:** handled by Anthropic in the Claude product, and retained according to your Claude account settings and Anthropic's retention policy. This is separate from the SimpleBooking connectors.
- **Report files:** stored on your device until you delete them.
- **SimpleBooking data:** retained according to your SimpleBooking contract and the Provider's retention policies.

## 10. Security

- Access is limited to the permissions of your SimpleBooking account.
- The plugin runs read-only queries.
- Data is transmitted over HTTPS.
- Local scripts make no network calls.

## 11. Your rights

Under Articles 15 to 22 of the GDPR, you have the right to access, rectify, erase, restrict, or object to the processing of your personal data, and the right to data portability. You also have the right to lodge a complaint with the Italian Data Protection Authority (Garante per la protezione dei dati personali, www.garanteprivacy.it).

Where the hotel is the controller for guest data, guest requests should be directed to the hotel. We will assist the hotel in responding.

To exercise your rights, contact privacy@qnt.it.

## 12. Changes

We may update this policy. Material changes will be notified through the SimpleBooking account email. The version and date at the top of this document show when it was last updated.

## 13. Contact

QNT S.r.l. a Single Shareholder
Via Lucca 52, 50142 Florence, Italy
privacy@qnt.it
