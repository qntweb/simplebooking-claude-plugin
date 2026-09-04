# sb-revenue-lens — Specifica formale dei detector

Ogni lente è **input → regola → output**. Il modello *narra* il risultato della
regola; non inventa la regola. Tutte le soglie sono in `config/defaults.yaml` e
sono **relative** al periodo/hotel.

---

## Regola trasversale R0 — Riconciliazione disponibilità (OBBLIGATORIA)

`availability_calendar` e `query_bookable_options` **non sempre concordano**, e
"nessuna opzione" ha tre cause diverse da distinguere prima di concludere:

1. **Sold-out reale** — `Can Stay = No` nel calendario.
2. **Tagliata da restrizione** — calendario `Can Stay = Yes` ma `query` multi-notte
   vuota perché una notte interna è MinLOS/sold-out (→ vedi L3 gap-night).
3. **Mismatch allocazione** — nessuna camera per quella composizione ospiti.

Procedura: se una `query` multi-notte torna vuota ma il calendario dà disponibile,
**ri-prova con 1 notte** sulle singole date dell'intervallo. La notte che fallisce
da sola è il blocco. (Test: Hotel D 23→25 giu vuoto, ma 23→24 = 324€ → il blocco era
il 24; Hotel B 19→21 giu vuoto, ma 19→20 = 295€ → il blocco era il 20.)

> Non fidarsi mai del solo calendario: nel test diceva "Can Stay: Yes" su notti
> che in pratica spezzavano i soggiorni.

---

## L1 — Money-leak ("dove sto lasciando soldi?")

**Input:** demand per settimana; availability calendar; prezzi su date interessanti + 1 baseline soft.

**Regola — segnala una notte se almeno uno:**
- **L1a Ultima-camera-a-tariffa-piatta:** `tight` (max disponibili su tutte le
  categorie ≤ `tight_max_available`) **E** prezzo notte ≤ mediana_periodo ×
  (1 + `premium_expected_min`). → scarsità non prezzata.
- **L1b Orphan night ad alto valore:** notte libera adiacente a un sold-out (vedi
  R0/L3) in una settimana ad alta domanda (top tercile). → notte cara che diventa
  invendibile in un multi-notte.
- **L1c Domanda alta / io largo & cheap:** settimana top-tercile di domanda **E**
  copertura categorie alta **E** prezzo quartile basso. → potresti spingere il prezzo.

**Output:** lista notti ordinata per valore stimato, con il **tipo** (a/b/c) e una
domanda di verifica (mai un ordine).

**Edge/control:** se l'hotel è largo ma i prezzi sono già differenziati weekend↔soft
(es. Hotel A: Jun 19 ~447€ vs Jul 26 ~395€) **non** segnalare L1c: il pricing sta
già lavorando. Evita il falso allarme.

---

## L2 — Rischio invenduto ("quali date rischiano l'invenduto?")

**Input:** demand per settimana + `daysAhead`; availability; prezzo campione.

**Regola — segnala un blocco di date se TUTTI:**
- domanda d'area bottom-tercile (o in calo monotono verso fine periodo);
- copertura categorie ≥ `wide_open_room_types_min`;
- prezzo quartile basso;
- **dentro/oltre** la booking window (`giorni_residui < anticipo_medio_settimana`).

**Output:** date soft + "quanto sei in ritardo sul ciclo" + leve come **opzioni**
(offerta breve, MinLOS basso, pacchetto), non prescrizioni.

**Test:** fine luglio su tutti i 4 hotel = domanda minima + molte camere + prezzo
più basso del periodo (Hotel D 184€, Hotel B 241€, Hotel A 370€). Scatta in modo coerente.

---

## L3 — Restrizioni vs LOS della domanda ("le mie regole mi tagliano fuori?")

**Input:** demand `numberOfNights` (distribuzione); availability calendar (MinLOS + gap night via R0).

**Regola — due varianti:**
- **L3a Gap-night:** esiste una notte `Can Stay = Yes` non vendibile in 2-3 notti
  perché una notte adiacente è sold-out. Quantifica la notte persa (prezzo notte ×
  numero notti orfane). *Test Hotel B: notti 7 e 20 giugno isolate → la notte del 19
  (295€) non vendibile a chi cerca ven-dom.*
- **L3b MinLOS vs short-stay:** quota ricerche short-stay (≤ `short_stay_nights_max`)
  ≥ `short_stay_share_flag` **E** MinLOS sulle date > `short_stay_nights_max`.
  → stai rifiutando domanda matchabile.

**Output:** quanta domanda *matchabile* stai rifiutando e dove; per L3a suggerisci
apertura 1-notte/orphan; per L3b **presenta come TRADE-OFF, non errore**.

**Nota critica (test Hotel C):** MinLOS 4 a luglio blocca i 2-3 notti, ma in
quella destinazione la ricerca #1 è 7 notti (26k). Tuttavia short-stay 1-3 notti pesa
~38k ricerche. Quindi la regola scatta, ma la lettura corretta è: *"rifiuti molta
domanda corta; se la domanda 7-notti non riempie luglio, le MinLOS 4 ti lasciano
scoperto. È una scelta voluta?"* — mai dire "sbagli", perché long-stay può essere
strategia di stagione.

---

## L4 — Parità OTA ("il mio diretto batte le OTA?")

**Pre-condizione:** `rate_match_enabled = true` (i 4 hotel test ce l'hanno; se no, salta e dillo).
**Input:** `query_bookable_options` → Query ID → `get_ota_prices` su date chiave.
**Regola:** segnala le date dove una OTA è sotto il diretto.
**Output:** elenco date di disparità con scarto assoluto/%.

---

## L5 — Runway / anticipo ("quanto tempo ho per agire?")

**Input:** demand `daysAhead` per periodo; calendar (giorni mancanti).
**Regola:** `anticipo_medio` vs `giorni_residui` → urgenza (agire ora / c'è tempo / finestra chiusa).
**Output:** per blocco di date, livello di urgenza.

---

## L6 — Posizionamento domanda (lente soft, opzionale)

**Input:** demand `user.countryCode`, `guestType`, `numberOfKids`, `device`; room types/servizi/lingue.
**Regola:** grande domanda di un mercato/segmento vs contenuto/camere/lingue non allineati.
**Output:** gap di posizionamento. Esplicitamente qualitativa.

---

## Note di robustezza (apprese dal test)

- **Domanda d'area = destinazione, non proprietà.** Hotel a 200m hanno demand uguale (Hotel A=Hotel B). Non spacciarla per domanda dell'hotel.
- **"Available N"** è per categoria+tariffa, non inventario di casa.
- **Struttura tariffaria varia:** alcuni hotel espongono *Offerte* (Hotel D, Hotel A, Hotel B), altri *Rate Plan* (Hotel C). Il detector legge il "cheapest" a prescindere dalla struttura.
- **Tasse/extra** (es. city tax €6/notte su un hotel del test) possono non essere nel prezzo esposto: non sommarle a mano, segnala solo che esistono.
- **Mese corrente:** parti da oggi (date passate non interrogabili) e dillo.
- **Controllo falsi allarmi:** un hotel sano e ben prezzato (Hotel A) deve produrre poche o zero segnalazioni. Se una lente "spara" su tutto, la soglia è sbagliata.
