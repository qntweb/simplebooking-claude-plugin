# Le 7 lenti incrociate — specifica formale

Ogni lente: **due input (uno per fonte) → confronto → classificazione → narrazione**. La
classificazione usa sempre le soglie di `config/defaults.yaml`, mai un giudizio a occhio.
Se `scripts/verify.py` non conferma il calcolo, la lente non produce un output — dichiara
"non riconciliato" ed elenca i numeri grezzi così come sono arrivati dalle due fonti.

## Due guardrail aggiunti dopo la validazione su 4 property reali (X1/X3/X6)

1. **Base minima (`min_gap_base_n`, default 20).** Hotel E: una base STLY
   di 14 prenotazioni ha prodotto un gap di +150pp, corretto aritmeticamente ma senza
   significato pratico. Passa sempre `sales_base_n` a `scripts/verify.py`: sotto soglia,
   riporta i conteggi assoluti accanto alla percentuale, mai la percentuale da sola.
2. **Doppia base, RoomNights e reservationsCount.** Hotel C: le due
   basi hanno classificato la stessa settimana in due modi diversi ("da verificare" vs
   "scostamento marcato"). Calcola sempre entrambe e passa `other_basis_classification` a
   `scripts/verify.py`: se disaccordano, riportale entrambe, non sceglierne una in silenzio.

## X1 — Pace comparativo

- **Input:** domanda d'area per una finestra **quest'anno** e per la stessa finestra **un
  anno fa** (±364gg, stesso raggio), da `sb-revenue-lens`; OTB reale per la finestra oggi e
  STLY (registrate entro lo snapshot di un anno fa meno cancellate entro lo stesso
  snapshot) per la stessa finestra, da `sb-reservation-insights`. **Mai** settimane diverse
  di uno stesso snapshot in avanti nel tempo — vedi il warning in
  `references/orchestration.md`: il conteggio di domanda declina meccanicamente più la
  settimana di soggiorno è lontana da oggi, per via della finestra di osservazione fissa a
  91 giorni del demand report. Confrontare la settimana N con la N+1 dello stesso snapshot
  scambia questo artefatto per un segnale di mercato — verificato su 4 property reali.
- **Confronto:** `gap_pp = delta_vendite_pct_YoY - delta_domanda_pct_YoY`.
- **Classificazione** (soglie `gap_thresholds`): `|gap_pp| <= aligned_pp` → "in linea col
  mercato"; `aligned_pp < |gap_pp| <= notable_pp` → "da verificare"; oltre → "scostamento
  marcato" (dichiara solo che c'è, mai la causa).
- **Nota:** se domanda e vendite calano insieme YoY, è probabile stagionalità/anno debole
  per l'intera destinazione — dillo prima di suggerire un problema della struttura. Il
  segnale interessante è quando **divergono**.
- **Validato su dati reali** — stessa settimana (2026-08-31→2026-09-06 vs 2025-09-01→
  2025-09-07), 4 property, riconciliato da `scripts/verify.py`:

  | Property | Domanda YoY | Vendite YoY (RN) | Vendite YoY (res) | gap (RN) | Classificazione |
  |---|---|---|---|---|---|
  | Hotel D | −12,25% | +12,50% | +21,98% | +24,75pp | scostamento marcato |
  | Hotel E | +2,00% | +152,00% | +121,43% | +150,00pp | scostamento marcato (base 14, sotto `min_gap_base_n` — vedi sopra) |
  | Hotel F | −12,25% | −24,24% | −17,39% | −11,99pp | da verificare |
  | Hotel C | +14,86% | +4,60% | −30,65% | −10,27pp (RN) / −45,51pp (res) | disaccordo fra basi — vedi sopra |

  Nessun "in linea" nel campione: copertura ancora parziale del dominio della lente. Un
  punto reale interessante trovato per caso: Hotel D e Hotel F sono
  nella stessa destinazione e hanno rilevato la **stessa** domanda d'area (−12,25% YoY, raggio 12
  km) — conferma diretta del caveat già documentato in `sb-revenue-lens`
  ("hotel vicini nello stesso raggio ottengono numeri quasi identici") — eppure una
  struttura ha guadagnato quota e l'altra l'ha persa: la lente distingue le due situazioni
  correttamente.

## X2 — Freni alla conversione

- **Input:** insieme di notti segnalate da L3 di `sb-revenue-lens` (MinLOS troppo
  stringente rispetto alla domanda, gap night) e insieme di notti reali a bassa
  vendita/cancellazione alta da `sb-reservation-insights`, stesso periodo.
- **Confronto:** intersezione dei due insiemi.
- **Output:** solo le notti presenti in **entrambi** gli insiemi sono un freno confermato;
  quelle presenti in uno solo restano un'ipotesi, e vanno dichiarate come tale, non
  presentate come conferma.
- **Bug reale trovato e corretto (Hotel D, 2026-08-31):** `Can Stay: No` su
  `property_get_availability_calendar` **non implica una restrizione**. Su tutte le date
  "No" della finestra 2026-08-31→2026-10-11 la colonna Restrictions era vuota ("—") — nessun
  MinLOS/MaxLOS/CI/CO dichiarato. Verificato con `property_query_bookable_options` su una di
  quelle notti (2026-09-07→08): "There are no bookable options" — è **sold-out**, non un
  vincolo di policy. Un sold-out è l'opposto del segnale che X2 cerca (piena occupazione,
  non domanda respinta da una regola). **Correzione obbligatoria alla lente:** conta come
  "freno" candidato solo una notte con un **codice di restrizione esplicito** in
  `Restrictions` (in particolare `MinLOS N`), mai una notte "Can Stay: No" con
  `Restrictions` vuota. Su questa property, in questa finestra, non c'era nessuna
  restrizione esplicita impostata: la lente avrebbe prodotto zero freni confermati — corretto,
  ma solo dopo questa correzione (prima della correzione avrebbe segnalato erroneamente
  decine di notti sold-out come "freni").

## X3 — Prezzo e parità realizzata

- **Input:** scostamento di parità per data/canale (L4 di `sb-revenue-lens`) e ADR reale
  per canale su un periodo più ampio (`sb-reservation-insights`).
- **Confronto corretto — due fatti affiancati, non una sottrazione.** La specifica
  originale ("prezzo diretto in parità − ADR realizzato") sottraeva due numeri di scopo
  diverso: un prezzo puntuale su UNA data e UN room type (parità) contro un ADR medio su
  un intero trimestre e più canali (realizzato). La differenza non ha un'unità di misura
  interpretabile. **Riporta invece due fatti distinti fianco a fianco**: (a) lo stato di
  parità live sulle date campionate, (b) il gap di ADR realizzato per canale sul periodo
  storico — lasciando alla narrazione, non all'aritmetica, il compito di collegarli.
- **Guardrail:** se `rate_match_enabled` è falso lato booking engine, la parte (a) non gira
  — dillo, non stimare uno scostamento senza il dato di parità.
- **Validato su dati reali** — Hotel D, tutte e 4 le property test avevano
  `rate_match_enabled = true`:
  - (a) Parità 2026-09-05→06, 2 adulti: diretto 394,00€, Expedia 395,00€ (+0,3%),
    Hotels.com 395,00€ (+0,3%) — diretto leggermente più economico di entrambe le OTA,
    nessuna disparità.
  - (b) ADR realizzato giu-ago 2026 (ultimi 3 mesi conclusi): Direct 252,15€
    (312.406,58€ TotalStay / 1.239 RoomNights), Indirect 235,56€ (575.709,81€ / 2.444) —
    il diretto realizza un ADR **+7,05%** più alto dell'indiretto sullo stesso trimestre.
  - Lettura coerente: il diretto non solo è a parità/leggermente sotto le OTA oggi, ma ha
    storicamente venduto a un prezzo medio più alto — nessuna pressione sulla distribuzione
    rilevabile su questo campione.

## X4 — Prodotto vs domanda

- **Input:** periodi di picco domanda (quartile alto, da L1/L2) incrociati con presenza di
  un pacchetto/offerta attivo in quel periodo (catalogo, letto da `sb-revenue-lens`) e con
  le vendite reali di quel pacchetto nello stesso periodo (`sb-reservation-insights`).
- **Output:** qualitativo, due segnali distinti da non confondere — "il catalogo non copre
  il picco" (nessun pacchetto attivo su quelle date) è diverso da "il pacchetto è a
  catalogo ma non si vende" (copertura c'è, la domanda non lo sceglie).
- **Rischio non ancora testato:** se "picco domanda" è letto come quartile alto fra
  settimane consecutive di uno stesso snapshot in avanti, rischia lo stesso artefatto di
  X1 (settimane più vicine a oggi hanno meccanicamente più domanda accumulata — vedi
  `references/orchestration.md`). Preferisci individuare i picchi stagionali su una
  finestra ampia con lo stesso search_period per tutte le settimane confrontate (es. un
  intero anno, un solo snapshot), non su poche settimane consecutive in avanti da oggi.
- **Verificato su dati reali (parziale):** `property_get_packages_list` su Hotel C
  e Hotel F ha restituito **zero pacchetti** su
  entrambi — "packages" è spesso un catalogo vuoto/non usato, va gestito come caso normale
  e non come errore. Hotel F ha invece **29 offerte attive**
  (`property_get_offers_list`) — il concetto che le property usano davvero è "offer", non
  "package". **Correzione alla lente:** trattare packages e offers come due popolazioni di
  dimensione molto diversa, non assumere che un catalogo vuoto di uno implichi un problema
  — verifica quale dei due concetti la property usa prima di leggere "il catalogo non
  copre il picco" come un difetto. Il confronto vero e proprio con la domanda e con le
  vendite reali resta non testato.

## X5 — Mercati e segmenti

- **Input:** quota % di un `countryCode`/`guestType`/`device` nella domanda d'area (L6) e
  quota % dello stesso segmento nelle prenotazioni reali, stesso periodo.
- **Confronto:** `quota_domanda_pct − quota_vendite_pct`, per segmento.
- **Guardrail:** dichiara sempre la copertura del campo lato Back Office (mercato di
  provenienza reale non è sempre popolato — sotto `min_field_coverage` la lente si astiene)
  prima di leggere il confronto.
- **Validato su dati reali** — Hotel D, finestra 2026-08-31→2026-10-11,
  raggio 12km: domanda US 39,4% / IT 19,1% del totale; prenotazioni reali con
  `CustomerCountryCode` popolato US 155/525 (29,5%), IT 18/525 (3,4%). **Copertura reale
  del campo: 267/525 = 50,9%** (267 = somma di tutti e 29 i codici paese distinti
  restituiti — non c'è coda lunga oltre quelli, il resto è proprio assenza di valore).
  50,9% **supera** `min_field_coverage` (0,25): la lente non si asterrebbe. Ma il gap
  apparente su IT (19,1% domanda vs 3,4% vendite, quasi 16pp) resta interpretabile in due
  modi opposti — un vero deficit di conversione degli italiani, oppure il campo è
  semplicemente meno popolato sulle prenotazioni italiane (es. inserite via canali diversi
  dal form web) — e con metà dei dati assenti non si può escludere la seconda. **La
  soglia da sola non basta**: anche sopra floor, dichiara sempre il numero di copertura
  esatto nella risposta (non solo se sotto soglia) — la specifica lo prevedeva già, questo
  è solo la controprova su un caso reale.

## X6 — Pacing

- **Causa del problema originale — due popolazioni diverse, non un bug aritmetico.**
  `daysAhead` medio della domanda è la media su *tutti gli eventi di ricerca*: la
  stragrande maggioranza è traffico leggero (sfoglio, confronto, controllo prezzo) che è
  strutturalmente a ridosso della data. `DaysInAdvanced` reale è la media solo di chi **ha
  prenotato davvero** — un sottoinsieme molto più piccolo e più "pianificatore". Le due
  medie misurano popolazioni diverse per natura: confrontarle in valore assoluto non dice
  nulla sul pacing di QUESTA struttura, dice solo quanto è largo il funnel del mercato.
- **Prova su dati reali (Hotel D) che il bias è strutturale, non rumore:**

  | Periodo | Domanda `daysAhead` | Reale `DaysInAdvanced` | Rapporto reale/domanda |
  |---|---|---|---|
  | Luglio 2026 (concluso) | 39,01 gg | 109,12 gg | 2,80× |
  | Luglio 2025 (concluso) | 40,00 gg | 116,31 gg | 2,91× |

  Il rapporto resta ~2,8-2,9× a distanza di un anno — la firma di un bias costante, non
  di un segnale specifico della property. Confermato anche su una finestra futura (56,0
  vs 166,1 giorni, censura + stesso bias).
- **⚠️ Ma il rapporto NON è sempre così stabile — secondo test reale, Hotel G,
  stesso metodo, stesso mese:**

  | Periodo | Domanda `daysAhead` | Reale `DaysInAdvanced` | Rapporto reale/domanda |
  |---|---|---|---|
  | Luglio 2026 (concluso) | 23,68 gg | 45,15 gg | 1,91× |
  | Luglio 2025 (concluso) | 21,12 gg | 31,57 gg | 1,50× |

  Qui il rapporto si è mosso del **+27,6%** in un anno (contro il 3,8% di Hotel D)
  — su una base di 195-196 prenotazioni, non piccola. Il metodo YoY-delta resta l'unico
  corretto (il livello assoluto è ancora incomparabile), ma **l'assunzione che il bias
  resti costante non regge ovunque allo stesso modo**: qui potrebbe riflettere un vero
  allungamento della finestra di prenotazione dei suoi ospiti (spa/wellness, forse più
  gruppi/pacchetti prenotati con largo anticipo) più che rumore — ma non è distinguibile
  dall'altro caso senza indagare oltre.
- **Corretta con lo stesso principio già usato per X1: confrontare il delta YoY di
  ciascun lato, non il valore assoluto.** Se il bias è stabile nel tempo, il delta YoY di
  ciascuna metrica contro se stessa lo elimina.
- **Input:** delta % YoY di `daysAhead` medio della domanda (L5 di `sb-revenue-lens`,
  stessa finestra tradotta di un anno) e delta % YoY di `DaysInAdvanced` medio reale
  (`sb-reservation-insights`, `RegistrationDate` sottostante, stessa finestra), **solo su
  periodi già conclusi** — mai su una finestra futura, per lo stesso motivo per cui
  `sb-reservation-insights` dice "rifallo solo sui mesi già conclusi" sull'anticipo di
  prenotazione (censura: i bookers a breve termine di un periodo futuro non sono ancora
  arrivati).
- **Confronto:** `gap_pp = delta_vendite_pct_YoY − delta_domanda_pct_YoY`, stesse soglie e
  stesso `scripts/verify.py` (blocco `gap`) di X1, **più** i due campi opzionali
  `basis_ratio_a`/`basis_ratio_b` (il rapporto reale/domanda in ciascuno dei due anni):
  se il rapporto si sposta oltre `max_ratio_drift_pct` (default 15%), `verify.py` avvisa
  che l'assunzione di stabilità del bias non regge qui, e il gap va trattato come ipotesi
  da verificare, non come lettura confermata.
- **Validato su dati reali — due property, esiti diversi:**
  - Hotel D, luglio 2026 vs luglio 2025 — domanda −2,46% YoY, reale −6,18%
    YoY, gap −3,72pp, "in linea col mercato", rapporto stabile (drift 3,8%) →
    riconciliato da `scripts/verify.py` **senza** avviso di instabilità.
  - Hotel G, stesso mese — domanda +12,10% YoY, reale +43,01% YoY,
    gap **+30,90pp**, "scostamento marcato", ma rapporto instabile (drift 27,6%) →
    `scripts/verify.py` segnala l'avviso: il gap è aritmeticamente corretto ma
    l'assunzione di base della lente qui è debole, va presentato come ipotesi da
    verificare con l'albergatore, non come fatto.
  - **Lettura pratica:** il metodo YoY-delta è l'unica correzione valida al problema
    originale (le due popolazioni restano incomparabili in assoluto, sempre), ma non è
    infallibile — verifica sempre `basis_ratio_a`/`basis_ratio_b` prima di presentare un
    gap di X6 come una lettura solida.

## X7 — Portafoglio

- **Input:** X1 (o la lente richiesta) ripetuta per ciascuna property del gruppo.
- **Confronto:** ranking delle strutture per `gap_pp` (o per la metrica della lente
  richiesta).
- **Guardrail:** stessa regola di `sb-monday-brief` — se l'output è per un cliente singolo,
  nessun dato di altre property nominato; il ranking multi-struttura è solo per chi
  gestisce l'intero portafoglio.
- **Validato su dati reali:** le 4 property della validazione X1 non sono un vero
  "portafoglio" (non appartengono allo stesso gruppo), ma la tabella X1 sopra è già,
  meccanicamente, il ranking che X7 dovrebbe produrre — non è stata scritta una riga di
  codice in più per ottenerlo. Ordinando per `gap_pp` (base RoomNights): Hotel E
  (+150pp, da leggere con cautela per la base ridotta), Hotel D (+24,75pp),
  Hotel C (−10,27pp), Hotel F (−11,99pp). Non validato invece
  l'aspetto specifico di X7 — il guardrail "nessun dato di altre property se il cliente è
  singolo" — perché richiede un contesto di output reale (report per un cliente) non
  ricreabile in questa validazione.
