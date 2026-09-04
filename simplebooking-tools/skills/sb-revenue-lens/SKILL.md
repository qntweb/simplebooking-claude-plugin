---
name: sb-revenue-lens
metadata:
  author: Sergio Farinelli
  organization: QNT — SimpleBooking — Zucchetti Group
description: >
  Diagnostico revenue domanda-guidato per hotel, solo MCP SimpleBooking.
  L'utente fa una domanda su hotel+periodo e la skill incrocia domanda d'area,
  disponibilità, restrizioni e prezzi: risposta in chat, report brandizzato a
  richiesta. Usa SEMPRE per: "dove perdo/lascio soldi", "rischio invenduto",
  "date deboli", "le mie restrizioni", "MinLOS", "minimum stay", "diretto vs
  OTA", "parità tariffaria", "dove ho ancora camere", "quanto anticipo ho",
  "opportunità revenue", "money leak", "period check", "analizza il periodo X".
  NON usare per: eventi (sb-event-radar), traffico AI (sb-ai-traffic), audit
  contenuti (sb-hotel-content-audit), crawl sito (qnt-site-inspector), confronto con
  prenotazioni reali (sb-demand-capture).
---

# 🔎 sb-revenue-lens — Diagnostico revenue domanda-guidato (SB-only)

## Panoramica

`sb-revenue-lens` risponde a **una domanda dell'albergatore** su un periodo,
incrociando la **domanda d'area** (ricerche dei viaggiatori sul booking engine,
via `property_destination_demands_run_report`) con la **disponibilità,
le restrizioni e i prezzi** della struttura.

A differenza di un report che vomita tutte le metriche, questa skill è
**guidata dall'intento**: l'utente pensa per problemi ("sto perdendo soldi?"),
non per metriche. Un router interno mappa la domanda su una o più **lenti**,
ognuna delle quali è un **detector deterministico** (regola verificabile) +
una narrazione breve.

**Vincolo fondante:** usa SOLO il MCP SimpleBooking. Nessun Zucchetti Travel
Data Lake, nessuna fonte eventi proprietaria. È pensata per essere usata da
albergatori, consulenti e reseller **esterni**. → vedi §"Cosa NON può fare".

Default in **chat** (prima risposta veloce). Report brandizzato **a richiesta**.

## MCP Tools (tutti e soli SimpleBooking)

- `booking_engine_search_properties` / `booking_engine_get_accessible_properties` — risoluzione hotel.
- `property_get_basic_info` — nome, stelle, città, lingue, valuta, **rate_match_enabled**, room types.
- `destination_get_report_options` — valori validi per i campi del demand report.
- `property_destination_demands_run_report` — **motore centrale**: domanda d'area.
- `property_get_availability_calendar` — disponibilità effettiva + restrizioni (MinLOS/MaxLOS/CI/CO).
- `property_query_bookable_options` — prezzi, camere residue, breakdown LOS, Query ID per OTA.
- `property_get_ota_prices` — parità OTA (solo hotel con rate match).
- `property_get_room_types_list` / `property_get_services_list` — solo per la lente "posizionamento".
- `calendar_*` — classificazione date (weekend, festività nazionali, conteggio notti). **Mai** calcolare i giorni della settimana a mente.

## Cosa NON può fare (dichiararlo sempre nell'output)

La skill è un **diagnostico domanda-d'area vs mia disponibilità/prezzo**, NON un RMS. Con il solo MCP SB **non** vede:

- on-the-books reale né passo di pickup (la domanda è *ricerca d'area*, non le tue prenotazioni);
- tariffe dei competitor reali (solo parità OTA, e solo se rate match attivo);
- **fonte eventi**: la skill rileva i pattern (sold-out, gap night) ma **non attribuisce** la causa. Vedi §Eventi.

Tutto ciò che è inferenza va etichettato come tale, distinto dai fatti.

## Parametri di input

### Obbligatori
| Parametro | Tipo | Descrizione |
|---|---|---|
| `hotel` | nome o ID SB | Risolvi nomi noti via mapping; se sconosciuto chiedi il Property ID. |
| `period` | flessibile | Es. "giugno", "giu-lug", "prossime 6 settimane", range esplicito. |

### Opzionali
| Parametro | Default | Descrizione |
|---|---|---|
| `question` | — | La domanda in linguaggio naturale. Se assente, vedi STEP 2 (router/chiedi). |
| `radius_km` | `12` urbano / `25` extra-urbano | Raggio domanda d'area. |
| `room_allocations` | `[{adults:2, children:[]}]` | Composizione per le query prezzo. |
| `output_mode` | `chat` | `chat` = prima risposta; `report` = PDF/HTML brandizzato. |
| `language` | lingua conversazione | Lingua di risposta/report. |
| `promo_code` | null | Codice promo da testare nelle query prezzo. |

## Architettura a due passate (controllo costi/latenza)

`property_query_bookable_options` è **caro**; `availability_calendar` e il demand
report sono **economici**. Quindi:

1. **Passata leggera (sempre):** demand report (per settimana + 1-2 tagli) +
   availability calendar sull'intero periodo. Da qui il detector individua le
   **date interessanti** (sold-out, bordi sold-out, weekend, ultima camera,
   settimane ad alta domanda).
2. **Passata mirata (solo dove serve):** `query_bookable_options` SOLO sulle
   date interessanti, non su tutto il periodo. La parità OTA (`get_ota_prices`)
   solo in modalità `report` e solo se rate match attivo.

## Router degli intenti

Mappa la domanda dell'utente → lente/i. Se ambigua, chiedi con scelta multipla.
Se l'utente non fa una domanda ("analizza giugno"), esegui le lenti L1+L2 (le
più universali) e offri le altre.

| Trigger nella domanda | Lente |
|---|---|
| "dove perdo / lascio soldi", "money leak", "opportunità" | **L1 — Money-leak** |
| "rischio invenduto", "date deboli", "dove ho ancora camere" | **L2 — Rischio invenduto** |
| "restrizioni", "MinLOS", "minimum stay", "soggiorni corti" | **L3 — Restrizioni vs LOS** |
| "diretto vs OTA", "parità", "disparity" | **L4 — Parità OTA** |
| "anticipo", "quanto tempo ho", "runway", "urgenza" | **L5 — Runway/anticipo** |
| "da dove viene la domanda", "famiglie", "mercati", "lingue" | **L6 — Posizionamento domanda** |

## Le lenti (detector deterministici)

Ogni lente: **input → regola → output**. Il modello *narra* il risultato della
regola; non inventa la regola.

### L1 — Money-leak ("dove sto lasciando soldi?")
- **Input:** demand per settimana; availability calendar; prezzi sulle date interessanti.
- **Regola — segnala una data/notte se:**
  - *Ultima-camera-a-tariffa-piatta:* poche camere residue (es. ≤1-2 per la cheapest) **e** prezzo notte ≈ baseline del periodo (nessun premio nonostante la scarsità).
  - *Orphan night ad alto valore:* notte libera incastrata tra notti sold-out (vedi L3 per il dettaglio del meccanismo) in una settimana ad alta domanda.
  - *Domanda alta / io largo & a buon mercato:* settimana con ricerche d'area nel quartile alto **ma** disponibilità ampia e prezzo nel quartile basso.
- **Output:** lista date "leak" ordinata per stima di valore, con il **tipo** di perdita e una domanda di verifica (non un ordine).

### L2 — Rischio invenduto ("quali date rischiano l'invenduto?")
- **Input:** demand per settimana + `daysAhead`; availability calendar; prezzo campione.
- **Regola — segnala se:** domanda d'area bassa/calante **+** disponibilità ampia su molte categorie **+** già **dentro/oltre** l'anticipo medio del periodo (poco runway residuo).
- **Output:** date soft + "quanto sei in ritardo" sul ciclo di prenotazione + leve possibili (offerta breve, MinLOS basso, pacchetto) come opzioni, non prescrizioni.

### L3 — Restrizioni vs LOS della domanda ("le mie regole mi tagliano fuori?")
- **Input:** demand `numberOfNights` (distribuzione); availability calendar (MinLOS + gap night).
- **Regola — segnala se:**
  - la domanda è concentrata su 1-2 notti **ma** ho MinLOS ≥3 su quelle date; oppure
  - esistono **gap night**: una notte libera che non è vendibile in un 2-3 notti perché una notte adiacente è sold-out (es. il 23 libero ma il 24 pieno → il 23→25 fallisce e perdo la notte del 23).
- **Output:** quanta domanda *matchabile* sto rifiutando e su quali notti; suggerimento di apertura 1-notte / orphan-night.
- **Nota di robustezza:** L3 è la più affidabile perché 100% meccanica e SB-only. **Riconcilia sempre** `availability_calendar` (che può dire "Can Stay: Yes") con un `query_bookable_options` multi-notte di verifica: nella simulazione il calendario diceva disponibile ma il 2-notti falliva. Non fidarsi del solo calendario.

### L4 — Parità OTA ("il mio diretto batte le OTA?")
- **Pre-condizione:** `rate_match_enabled = true` (altrimenti salta e dillo).
- **Input:** `query_bookable_options` → Query ID → `get_ota_prices` su date chiave.
- **Regola:** segnala le date dove una OTA è sotto il diretto.
- **Output:** elenco date di disparità con scarto assoluto/%.

### L5 — Runway / anticipo ("quanto tempo ho per agire?")
- **Input:** demand `daysAhead` per periodo; calendar (giorni mancanti).
- **Regola:** confronta anticipo medio del periodo vs giorni residui → mappa di urgenza (agire ora / c'è tempo / finestra chiusa).
- **Output:** per blocco di date, il livello di urgenza.

### L6 — Posizionamento domanda (lente "soft", opzionale)
- **Input:** demand `user.countryCode`, `guestType`, `numberOfKids`, `device`; room types/servizi/lingue.
- **Regola:** grande domanda di un mercato/segmento (es. US, famiglie) vs contenuto/camere/lingue non allineati.
- **Output:** gap di posizionamento sul booking engine. Esplicitamente qualitativa, non un calcolo di prezzo.

## Eventi — come gestire il buco senza ZDL

La skill **non possiede una fonte eventi**. Regola d'oro: **mai affermare** un
evento che non può provare. In ordine di preferenza:

1. **Rileva, non attribuire:** "il 24/6 è sold-out e spezza i 2-notti" — corretto al 100%.
2. **Chiedi all'albergatore:** "Su queste date sei pieno: sai se ci sono eventi/fiere?" Lui conosce il suo calendario meglio del modello.
3. *(Opzionale, fuori MCP SB)* se l'ambiente ha web search, arricchimento "best-effort" etichettato come **ipotesi**. Mai dipendenza, mai presentato come fatto.

## Guardrail

- **Non è consulenza prescrittiva di prezzo.** Inquadra come supporto: "3 cose da verificare", opzioni, non "fai X". Ricorda che la skill non vede costi, allotment, gruppi, contratti, strategia.
- **Mostra sempre la tabella delle evidenze** (date, disponibilità, prezzo, domanda). La trasparenza è il fossato contro i tool "AI revenue" black-box.
- **"Available: N" ≠ inventario di casa.** È N per quella categoria a quella tariffa. Non gridare alla scarsità.
- **Fatto vs inferenza** sempre distinti nel testo.
- **Date passate:** `query_bookable_options` non accetta il passato; per il mese corrente parti da oggi e dillo.

## Output

### Modalità `chat` (default)
1. Una riga di sintesi per la proprietà.
2. La risposta alla lente attivata (lista date + tipo di segnale).
3. Tabella evidenze compatta.
4. 1-3 domande di verifica / opzioni.
5. Offerta: "vuoi il report brandizzato / lo scan schedulato?"

### Modalità `report` (a richiesta)
Generata con lo script incluso, **non** scrivendo HTML a mano:

```
python scripts/build_report.py analisi.json -o report_<hotel>_<periodo>.html
```

Lo script (stdlib only, Chart.js da CDN) produce il layout approvato: header
SimpleBooking, domanda, sintesi, grafici domanda/LOS, segnali per lente con
tabelle evidenze + callout, mappa date a calendario, blocco limiti, spazio
eventi, opzioni. Procedura: esegui le lenti → compila un JSON secondo lo schema
di `scripts/sample_hotel_d.json` → lancia lo script → consegna l'HTML (apribile nel
browser, esportabile in PDF).

Classi colore celle tabella: `t-or` `t-gr` `t-red`. Classi calendario: `red`
(sold-out/MinLOS4), `or` (tight/MinLOS3), `y` (MinLOS2), `gr` (soft), `past`.

## Estensioni
- **Batch multi-hotel** per consulenti/reseller (scan portfolio).
- **Scheduling**: scan del mattino che avvisa solo quando un detector scatta
  (es. ultime camere di un weekend sotto soglia, nuova gap night).

## File di supporto
1. `config/defaults.yaml` — soglie detector, mapping hotel noti, raggi default.
2. `config/lenses.md` — specifica formale di ogni detector (input, regola, edge case).
3. `templates/report-structure.md` — struttura narrativa del report.
4. `scripts/build_report.py` — generatore HTML brandizzato (layout approvato).
5. `scripts/sample_hotel_d.json` — esempio di input completo, runnable.
6. `examples/usage.md` — esempi domanda → risposta sui 4 hotel (suite di regressione).
