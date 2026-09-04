# Step 9 — Analytics & Next Step Intelligente

## Step 8.5 — MCP Probe (Silenzioso, INVISIBILE all'utente)

Si esegue DOPO il report (Step 8) e PRIMA di proporre il Next Step.

### Procedura probe

1. **Google Analytics MCP:**
   Chiama `get_account_summaries()`.
   - Risponde → GA4_AVAILABLE = true. Salvare il risultato per riusarlo.
   - Errore → GA4_AVAILABLE = false.

2. **Zucchetti Travel Data Lake MCP:**
   Chiama `destination_get_report_options()`.
   - Risponde → DATALAKE_AVAILABLE = true.
   - Errore → DATALAKE_AVAILABLE = false.

Se FORCE_GA4_AVAILABLE o FORCE_DATALAKE_AVAILABLE impostati → usarli.

### Regole critiche
- NON mostrare errori dei probe all'utente.
- NON chiedere all'utente se ha i tool installati.
- Se ENTRAMBI false → saltare Step 9, andare a Step 10.
- MAI menzionare tool assenti. Esperienza trasparente.

---

## Step 9 — Biforcazione

Prerequisito: almeno 1 tool opzionale disponibile.

### Scenario 9A — TRIAGE ("Quali lingue CORREGGERE per prime?")

Si attiva quando l'audit ha trovato problemi significativi:
- >= 3 issue ❌ su lingue diverse dalla master, OPPURE
- >= 5 issue ⚠️ su lingue diverse dalla master, OPPURE
- >= 2 lingue con completezza < 50%

### Scenario 9B — OPPORTUNITÀ ("Quali lingue AGGIUNGERE?")

Si attiva quando 9A NON si applica (audit buono).
Verifica se esistono mercati con traffico/domanda significativa
NON coperti dalle lingue abilitate sull'hotel.

### Opzioni utente (solo tool disponibili)

| GA4 | DL | Opzioni mostrate |
|-----|----|-----------------|
| ✅ | ✅ | 📊🔮 Completa / 📊 Solo GA4 / 🔮 Solo DL / ❌ No |
| ✅ | ❌ | 📊 Sì, analizza traffico / ❌ No |
| ❌ | ✅ | 🔮 Sì, analizza domanda / ❌ No |

---

## Chiamate API

### Google Analytics (se selezionato)

Trovare GA4 ID: tabella hotels.md → probe result → chiedi utente.

**1. Traffico per lingua:**
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

**2. Traffico per paese:**
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

**3. Trend mensile (solo Sonnet/Opus):**
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

### Zucchetti Travel Data Lake (se selezionato)

Usa coordinate GPS hotel (da basic_info SimpleBooking).

**1. Domanda futura per paese:**
```
destination_demands_run_report(
  center_lat = [LAT], center_lon = [LON],
  radius_km = 5,
  search_period_from = [90gg fa], search_period_to = [oggi],
  stay_date_from = [oggi], stay_date_to = [+90gg],
  buckets = '[{"aggregationType":"Terms","field":"user.countryCode","order":"Desc","size":20}]',
  metrics = '[{"aggregationType":"Count"},{"aggregationType":"Average","field":"numberOfNights"},{"aggregationType":"Average","field":"numberOfPersons"}]'
)
```

**2. Trend domanda mensile:**
```
destination_demands_run_report(
  center_lat = [LAT], center_lon = [LON],
  radius_km = 5,
  search_period_from = [180gg fa], search_period_to = [oggi],
  stay_date_from = [oggi], stay_date_to = [+90gg],
  buckets = '[{"aggregationType":"DateHistogram","field":"searchTimestampUTC","order":"Asc","interval":"1M"},{"aggregationType":"Terms","field":"user.countryCode","order":"Desc","size":10}]',
  metrics = '[{"aggregationType":"Count"}]'
)
```

**3. (Opzionale) Prenotazioni effettive:**
```
destination_reservations_run_report(
  center_lat = [LAT], center_lon = [LON],
  radius_km = 5,
  stay_date_from = [90gg fa], stay_date_to = [oggi],
  buckets = '[{"aggregationType":"Terms","field":"user.countryCode","order":"Desc","size":20}]',
  metrics = '[{"aggregationType":"Count"},{"aggregationType":"Average","field":"numberOfNights"}]'
)
```

---

## Mapping Paese → Lingua

| Paese                    | Lingua |
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

Nota: paesi multilingue (Belgio, Svizzera, Canada) → segnalare ambiguità.

---

## Output Scenario 9A — Matrice di Priorità

### Formula (pesi adattati ai tool disponibili)
- Entrambi: ISSUES=40%, TRAFFIC=30%, DEMAND=30%
- Solo GA4: ISSUES=50%, TRAFFIC=50%
- Solo DL: ISSUES=50%, DEMAND=50%

### Tabella
| # | Lingua | Issues ❌ | Issues ⚠️ | Compl.% | Traffico% | Domanda% | Trend | 🏆 Priorità |
Colonne Traffico/Domanda/Trend solo se rispettivo tool disponibile.

### Raccomandazione (solo Sonnet/Opus)
Narrativa con motivazione per ogni livello di priorità.
Haiku: solo tabella, nessuna narrativa.

## Output Scenario 9B — Mappa Opportunità

### Mercati non coperti
Paesi con >= 5% traffico O domanda la cui lingua NON è in ALL_ENABLED_LANGUAGES.

### Mercati sottovalutati
Lingue abilitate dove traffico/domanda è sorprendentemente alta.

### Tono raccomandazioni
Insight data-driven, MAI raccomandazioni di investimento.
"I dati suggeriscono", "potrebbe intercettare",
"da valutare sulla base della strategia commerciale".
