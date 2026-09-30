# SimpleBooking IBE connector

Read-only access to the SimpleBooking booking engine (IBE) for the hotels a user
manages: property content, availability, prices and area demand.

| | |
|---|---|
| Server | `https://mcp.ibe.simplebooking.it` |
| Transport | Streamable HTTP |
| Authentication | OAuth 2.0 with a SimpleBooking Back Office account |
| Access | read-only — no tool creates, changes or deletes anything |
| Provider | QNT S.r.l. — SimpleBooking, Zucchetti Group |
| Support | helpdesk@simplebooking.it |

## Who can use it

Anyone with a SimpleBooking Back Office account. Signing in grants access only to the
properties that account is authorised for by each property; the connector cannot reach
any other hotel.

## What data it returns

Most of what this connector returns is what any traveller already sees on the
property's public booking engine: descriptions, photos, room types, rates, offers,
packages, services and the availability calendar. On top of that it adds two kinds of
aggregated data:

- **Area demand** — the number of searches travellers ran on booking engines for stays
  around the property, grouped by date, length of stay, party size, country of origin
  or device. Counts only: no individual search and no traveller identity.
- **OTA price comparison** — for properties with Rate Match enabled, the prices the
  same stay is sold at on online travel agencies, which are public prices.

The connector never returns guest names, email addresses, postal addresses, phone
numbers or payment details.

## Tools

All tools are read-only.

### Properties
| Tool | What it does |
|---|---|
| `booking_engine_get_accessible_properties` | Lists the properties the signed-in account can access |
| `booking_engine_search_properties` | Finds an accessible property by name or ID |
| `booking_engine_get_supported_currencies` | Lists the currencies prices can be shown in |
| `property_get_basic_info` | Name, stars, address, contacts, description and booking links of a property |

### Content
| Tool | What it does |
|---|---|
| `property_get_room_types_list` | Room types with capacity and features |
| `property_get_room_type_full_details` | Full description, features, images and videos of one room type |
| `property_get_rate_plans_list` | Rate plans and their cancellation policies |
| `property_get_meal_plans_list` | Board options (room only, B&B, half board…) |
| `property_get_offers_list` | Active promotional offers |
| `property_get_packages_list` | Pre-built stay packages |
| `property_get_services_list` | Bookable extras (spa, parking, transfers…) |

### Availability and prices
| Tool | What it does |
|---|---|
| `property_get_availability_calendar` | Day-by-day availability and stay restrictions |
| `property_query_bookable_options` | Bookable combinations of room, rate and board for a stay, with prices |
| `property_get_ota_prices` | Direct price compared with OTA prices for the same stay (Rate Match only) |

### Area demand
| Tool | What it does |
|---|---|
| `property_destination_demands_run_report` | Aggregated searches for stays within a radius of the property |
| `destination_get_report_options` | The fields and groupings the demand report accepts |

### Calendar helpers
| Tool | What it does |
|---|---|
| `calendar_get_current_time` | Current date and time, to resolve "next month", "this weekend" |
| `calendar_get_month_summary` | Summary of a calendar month |
| `calendar_get_dates_range_summary` | Summary of a date range |
| `calendar_get_dates_range_details` | Day-by-day details of a date range |
| `calendar_get_individual_dates_details` | Details of specific dates |

## Example questions

- "Which dates in December do I still have rooms available?"
- "Is my direct price cheaper than Booking.com for a weekend in May?"
- "Where do the travellers searching for my area in summer come from?"
- "Which offers and packages are online right now?"

## Privacy

See the [privacy policy](https://github.com/qntweb/simplebooking-claude-plugin/blob/main/docs/privacy-policy-mcp.md).
