# Orchestrazione — quale fonte chiamare per ciascuna lente incrociata

Ogni lente incrociata (X1-X7) mette insieme **una risposta di `sb-revenue-lens`** e **una
risposta di `sb-reservation-insights`** sullo stesso periodo e, dove possibile, sulla
stessa granularità. Non chiamare mai un tool MCP direttamente da questa skill: il valore
di `sb-demand-capture` sta nel confronto, non nell'accesso ai dati. Se una delle due skill
non è disponibile in sessione, fermati e dichiaralo — non stimare il lato mancante.

## Due anomalie verificate su dati reali (2026-08-31, 4 property) — leggere prima di tutto

**1. `radius_km` è obbligatorio e non ha un default di sistema.** Passarlo sempre in modo
esplicito (vedi `config/defaults.yaml:radius_km`), mai omesso. Un test con `radius_km=0`
è stato silenziosamente riscritto in 2 km dal tool — comportamento non documentato, da non
fare affidamento. Usa lo **stesso raggio su entrambi i lati** di qualunque confronto YoY.

**2. Il confronto valido di domanda è sempre anno-su-anno, mai settimana-su-settimana
entro un solo snapshot.** `search_period_from/to` di default copre sempre i 91 giorni
prima di **oggi**, non prima della settimana di soggiorno interrogata. Di conseguenza, il
conteggio di domanda per settimane di soggiorno via via più lontane nel futuro declina
quasi meccanicamente — verificato su tutte e 4 le property (Hotel D, Hotel E, Hotel F,
Hotel C): la domanda
della sesta settimana in avanti era sempre inferiore alla prima, dal −14% al −81% a
seconda della property, indipendentemente da qualunque stagionalità reale. **Questo non è
un segnale di mercato: è un artefatto della finestra di osservazione fissa.** La lente X1
(e ogni altra lente che legga un trend di domanda: X4, X6, X7) deve quindi sempre
confrontare la **stessa finestra di soggiorno un anno fa vs oggi**, mai due settimane
diverse dello stesso snapshot — è lo stesso metodo che `sb-monday-brief` usa già per il
proprio Detector 1 (`raw/demand_now.md` / `raw/demand_ly.md`), non va reinventato.

| Lente | Chiedi a `sb-revenue-lens` | Chiedi a `sb-reservation-insights` | Confronto |
|---|---|---|---|
| **X1** — Pace comparativo | Domanda per {periodo} **quest'anno** e domanda per la stessa finestra **un anno fa** (±364gg), stesso raggio (L1/L2 di `sb-revenue-lens`, non "per settimana in avanti" — vedi warning sopra) | OTB reale per {periodo} oggi, e STLY per la stessa finestra un anno fa (registrate entro lo snapshot meno cancellate entro lo snapshot — metodo di `sb-reservation-insights`/`sb-monday-brief`, non reinventarlo) | Delta % domanda YoY vs delta % vendite YoY, sulla stessa finestra |
| **X2** — Freni alla conversione | L3 — Restrizioni vs LOS, **solo notti con un codice di restrizione esplicito** (`MinLOS N` in `Restrictions`) — mai un "Can Stay: No" a `Restrictions` vuota, che è sold-out, non un freno (vedi warning "X2" in `references/cross-lenses.md`) | Cancellazioni e soggiorni di una notte su {periodo}, per data | Intersezione fra le notti segnalate da L3 e le notti con vendite reali basse/cancellazioni alte |
| **X3** — Prezzo e parità realizzata | L4 — Parità OTA su date campione (richiede `rate_match_enabled`) | ADR reale per canale su un periodo storico più ampio (es. ultimo trimestre concluso) | **Due fatti affiancati**, non una sottrazione (vedi "X3" in `references/cross-lenses.md`): stato di parità live + gap di ADR realizzato per canale |
| **X4** — Prodotto vs domanda | L1/L2 per individuare i picchi di domanda (su un solo snapshot ampio, mai settimane consecutive in avanti), più il catalogo pacchetti **e** offerte (chiamata interna di `sb-revenue-lens`, non nostra — molte property non usano affatto "packages", verifica quale dei due concetti la property usa) | Quali pacchetti/offerte si vendono davvero su {periodo} | Catalogo nei periodi di picco vs venduto reale in quei periodi |
| **X5** — Mercati e segmenti | L6 — Posizionamento domanda (`countryCode`, `guestType`, `device`) | Mercati di provenienza e composizione ospiti reali su {periodo} — dichiara sempre la copertura esatta del campo, anche sopra `min_field_coverage` (vedi "X5" in `references/cross-lenses.md`) | Quota % di un mercato/segmento nella domanda vs quota % nelle prenotazioni reali |
| **X6** — Pacing | Delta % YoY di `daysAhead` medio (L5), **stessa finestra un anno fa**, **solo periodi già conclusi** (mai una finestra futura — censura) | Delta % YoY di `DaysInAdvanced` medio reale, stessa finestra, stesso vincolo "solo concluso" | Delta YoY vendite − delta YoY domanda — **mai il valore assoluto dei due anticipi**, la scala è strutturalmente diversa (2-3× a seconda della property). Calcola anche il rapporto reale/domanda nei due anni e passalo a `scripts/verify.py`: se si è spostato di molto, il gap è un'ipotesi da verificare, non una lettura confermata — vedi "X6" in `references/cross-lenses.md` |
| **X7** — Portafoglio | X1-X6 ripetute per ciascuna property del gruppo | Confronto multi-struttura: quota diretta, ADR, permanenza, pace (già supportato nativamente) | Ranking delle strutture per cattura della domanda locale |

## Allineamento delle finestre — l'errore più facile

`sb-revenue-lens` non vede l'on-the-books reale: la sua "domanda" è sempre una **ricerca**,
futura o passata, sul booking engine — mai una prenotazione. Quando chiedi a
`sb-reservation-insights` il lato vendite, distingui sempre `CheckInDate` (soggiorno) da
`RegistrationDate` (prenotazione) — la stessa distinzione che quella skill impone alla
propria utenza. Per un confronto con la domanda d'area (sempre riferita a date di
soggiorno cercate), usa `CheckInDate`, non `RegistrationDate` — l'eccezione è **X6**, dove
serve l'anticipo reale di prenotazione e quindi `RegistrationDate` è corretto.

`sb-revenue-lens` aggrega la domanda **per settimana** di default nella sua passata
leggera: se chiedi a `sb-reservation-insights` una scomposizione settimanale, usa la
stessa granularità su entrambi i lati — ma per X1/X4/X6/X7 la granularità che conta
davvero è "stessa finestra, due anni", non le sotto-settimane interne alla finestra.

## Esempio reale validato — X1 su Hotel D, 2026-08-31

Finestra: 2026-08-31 → 2026-09-06 (quest'anno) vs 2025-09-01 → 2025-09-07 (un anno fa,
−364 giorni, stesso lunedì-domenica), raggio 12 km su entrambi i lati.

| | Quest'anno | Un anno fa | Delta % |
|---|---|---|---|
| Domanda d'area (searches, radius 12km) | 27.141 | 30.929 | **−12,25%** |
| OTB reale (RoomNights, Active / STLY registrate−cancellate) | 288 | 256 | **+12,50%** |
| OTB reale (prenotazioni, stesso metodo) | 111 | 91 | **+21,98%** |

`gap_pp` (base RoomNights) = 12,50 − (−12,25) = **+24,75pp** → sopra `notable_pp` (15) →
**"scostamento marcato"**, confermato da `scripts/verify.py`. Lettura: per questa
settimana specifica, la domanda dell'intera destinazione è scesa del 12% anno su anno, ma
questa struttura ha comunque venduto il 12-22% in più — sta catturando più della propria
quota di un mercato che si è ristretto. Non è detto che regga per altre finestre: è un
solo punto dato, non una conferma della lente su tutto il suo dominio d'uso.

## Se una lente lato mercato non è applicabile

- **L4** (parità) salta se `rate_match_enabled` è falso: dillo, non stimare uno scostamento.
- **L6** è qualitativa in `sb-revenue-lens`: non trasformarla in una percentuale che il
  dato non sostiene — X4 e X5 restano confronti di quota/presenza, non di importo.
- **Copertura del campo lato Back Office** (mercato di provenienza, in particolare): prima
  di leggere il confronto di X5, verifica la copertura come faresti in
  `sb-reservation-insights` — sotto `config/defaults.yaml:min_field_coverage`, la lente si
  astiene e lo dichiara invece di produrre una quota fragile.
