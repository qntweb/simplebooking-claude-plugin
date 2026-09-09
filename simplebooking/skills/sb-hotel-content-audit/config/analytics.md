# Step 9 — Analytics & Smart Next Step

## Step 8.5 — MCP Probe (Silent, INVISIBLE to the user)

Runs AFTER the report (Step 8) and BEFORE proposing the Next Step.

### Probe procedure

1. **Google Analytics MCP:**
   Call `get_account_summaries()`.
   - Responds → GA4_AVAILABLE = true. Save the result for reuse.
   - Error → GA4_AVAILABLE = false.

2. **Zucchetti Travel Data Lake MCP:**
   Call `destination_get_report_options()`.
   - Responds → DATALAKE_AVAILABLE = true.
   - Error → DATALAKE_AVAILABLE = false.

If FORCE_GA4_AVAILABLE or FORCE_DATALAKE_AVAILABLE are set → use them.

### Critical rules
- Do NOT show probe errors to the user.
- Do NOT ask the user whether they have the tools installed.
- If BOTH false → skip Step 9, go to Step 10.
- NEVER mention missing tools. Transparent experience.

---

## Step 9 — Branching

Prerequisite: at least 1 optional tool available.

### Scenario 9A — TRIAGE ("Which languages to FIX first?")

Triggers when the audit found significant issues:
- >= 3 ❌ issues on languages other than master, OR
- >= 5 ⚠️ issues on languages other than master, OR
- >= 2 languages with completeness < 50%

### Scenario 9B — OPPORTUNITY ("Which languages to ADD?")

Triggers when 9A does NOT apply (good audit).
Checks whether markets with significant traffic/demand exist that are NOT
covered by the hotel's enabled languages.

### User options (only available tools)

| GA4 | DL | Options shown |
|-----|----|-----------------|
| ✅ | ✅ | 📊🔮 Full / 📊 GA4 only / 🔮 DL only / ❌ No |
| ✅ | ❌ | 📊 Yes, analyze traffic / ❌ No |
| ❌ | ✅ | 🔮 Yes, analyze demand / ❌ No |

---

## API calls

### Google Analytics (if selected)

Find the GA4 ID: hotels.md table → probe result → ask the user.

**1. Traffic by language:**
```
run_report(
  property_id = [GA4_ID],
  date_ranges = [{"start_date": "[N]daysAgo", "end_date": "yesterday"}],
  dimensions = ["language"],
  metrics = ["sessions", "totalUsers", "screenPageViews",
             "averageSessionDuration", "bounceRate"],
  order_bys = [{"metric": {"metric_name": "sessions"}, "desc": true}],
  limit = 20
)
```

**2. Traffic by country:**
```
run_report(
  property_id = [GA4_ID],
  date_ranges = [{"start_date": "[N]daysAgo", "end_date": "yesterday"}],
  dimensions = ["country"],
  metrics = ["sessions", "totalUsers", "screenPageViews",
             "averageSessionDuration", "bounceRate"],
  order_bys = [{"metric": {"metric_name": "sessions"}, "desc": true}],
  limit = 20
)
```

**3. Monthly trend (Sonnet/Opus only):**
```
run_report(
  property_id = [GA4_ID],
  date_ranges = [{"start_date": "180daysAgo", "end_date": "yesterday"}],
  dimensions = ["month", "language"],
  metrics = ["sessions", "totalUsers"],
  order_bys = [{"dimension": {"dimension_name": "month", "order_type": 1}, "desc": false}],
  limit = 200
)
```

### Zucchetti Travel Data Lake (if selected)

Use the hotel's GPS coordinates (from SimpleBooking basic_info).

**1. Future demand by country:**
```
destination_demands_run_report(
  center_lat = [LAT], center_lon = [LON],
  radius_km = 5,
  search_period_from = [90 days ago], search_period_to = [today],
  stay_date_from = [today], stay_date_to = [+90 days],
  buckets = '[{"aggregationType":"Terms","field":"user.countryCode","order":"Desc","size":20}]',
  metrics = '[{"aggregationType":"Count"},{"aggregationType":"Average","field":"numberOfNights"},{"aggregationType":"Average","field":"numberOfPersons"}]'
)
```

**2. Monthly demand trend:**
```
destination_demands_run_report(
  center_lat = [LAT], center_lon = [LON],
  radius_km = 5,
  search_period_from = [180 days ago], search_period_to = [today],
  stay_date_from = [today], stay_date_to = [+90 days],
  buckets = '[{"aggregationType":"DateHistogram","field":"searchTimestampUTC","order":"Asc","interval":"1M"},{"aggregationType":"Terms","field":"user.countryCode","order":"Desc","size":10}]',
  metrics = '[{"aggregationType":"Count"}]'
)
```

**3. (Optional) Actual reservations:**
```
destination_reservations_run_report(
  center_lat = [LAT], center_lon = [LON],
  radius_km = 5,
  stay_date_from = [90 days ago], stay_date_to = [today],
  buckets = '[{"aggregationType":"Terms","field":"user.countryCode","order":"Desc","size":20}]',
  metrics = '[{"aggregationType":"Count"},{"aggregationType":"Average","field":"numberOfNights"}]'
)
```

---

## Country → Language mapping

| Country                   | Language |
|--------------------------|--------|
| France                   | FR     |
| Germany, Austria, CH(DE) | DE     |
| Spain, Latinoamerica     | ES     |
| UK, US, AU, CA, IE       | EN     |
| Italy                    | IT     |
| Portugal, Brazil         | PT     |
| Netherlands, Belgium(NL) | NL     |
| Russia                   | RU     |
| Japan                    | JA     |
| China                    | ZH     |
| South Korea              | KO     |
| Poland                   | PL     |
| Czech Republic           | CS     |
| Sweden                   | SV     |
| Denmark                  | DA     |
| Romania                  | RO     |
| Hungary                  | HU     |
| Croatia                  | HR     |
| Slovenia                 | SL     |
| Israel                   | HE     |
| Turkey                   | TR     |
| Arab countries           | AR     |

Note: multilingual countries (Belgium, Switzerland, Canada) → flag ambiguity.

---

## Scenario 9A Output — Priority Matrix

### Formula (weights adapted to available tools)
- Both: ISSUES=40%, TRAFFIC=30%, DEMAND=30%
- GA4 only: ISSUES=50%, TRAFFIC=50%
- DL only: ISSUES=50%, DEMAND=50%

### Table
| # | Language | Issues ❌ | Issues ⚠️ | Compl.% | Traffic% | Demand% | Trend | 🏆 Priority |
Traffic/Demand/Trend columns only if the respective tool is available.

### Recommendation (Sonnet/Opus only)
Narrative with a rationale for each priority level.
Haiku: table only, no narrative.

## Scenario 9B Output — Opportunity Map

### Uncovered markets
Countries with >= 5% traffic OR demand whose language is NOT in ALL_ENABLED_LANGUAGES.

### Undervalued markets
Enabled languages where traffic/demand is surprisingly high.

### Recommendation tone
Data-driven insight, NEVER investment recommendations.
"The data suggests", "could capture", "worth evaluating based on your
commercial strategy".
