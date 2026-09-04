---
name: sb-demand-capture
metadata:
  author: Sergio Farinelli
  organization: QNT — SimpleBooking — Zucchetti Group
description: >
  Diagnostico che incrocia la domanda d'area del booking engine con le prenotazioni reali
  del Back Office: dice se una struttura sta catturando la domanda della propria
  destinazione o la sta lasciando andare. Orchestra sb-revenue-lens (domanda,
  disponibilità, restrizioni, parità OTA) e sb-reservation-insights (pickup, mix canale,
  mercati, anticipo reali) sullo stesso periodo, senza ricalcolarne la logica: possiede
  solo il confronto fra le due risposte e il caveat che la domanda è di destinazione, non
  di struttura. Usa SEMPRE per: "sto seguendo il mercato", "ho domanda ma non vendo", "il
  mio catalogo intercetta la domanda", "chi cerca vs chi prenota", "apro troppo tardi le
  vendite", "quale struttura del gruppo cattura meglio la domanda". NON usare per: una
  metrica reale isolata (sb-reservation-insights); domanda/disponibilità/prezzo senza le
  vendite reali (sb-revenue-lens); il brief settimanale fisso (sb-monday-brief);
  provenienza del diretto (sb-direct-attribution).
---

# 🎯 sb-demand-capture — Diagnostico incrociato domanda × vendite reali

## Panoramica

`sb-revenue-lens` sa leggere la **domanda di mercato** (ricerche sul booking engine,
disponibilità, restrizioni, prezzo). `sb-reservation-insights` sa leggere le **vendite
reali** (pickup, mix canale, mercati, cancellazioni) dal Back Office. Nessuna delle due,
da sola, può rispondere a "la domanda per le mie date c'è, ma io la sto vendendo?" — la
prima non vede una singola prenotazione, la seconda non vede il mercato.

`sb-demand-capture` esiste **solo** per rispondere a questa classe di domande: prende la
stessa domanda dell'albergatore, la instrada a entrambe le skill sullo stesso periodo, e
possiede **solo** la logica di confronto fra le due risposte.

## Vincolo architetturale non negoziabile (come sb-monday-brief)

**Questa skill orchestra, non ricalcola.** Non chiama mai un tool MCP direttamente: ogni
numero viene da un'invocazione agentica di `sb-revenue-lens` o di `sb-reservation-insights`,
citata verbatim. Se un domani una delle due cambia una formula o una soglia, questa skill
non deve essere toccata — eredita il cambiamento automaticamente, perché non ne possiede
una copia.

Questa skill possiede solo: **il router delle 7 lenti incrociate, l'allineamento delle
finestre temporali, l'aritmetica del confronto (delta/quota), le soglie di classificazione
del gap, e il caveat destinazione-vs-struttura.**

## Relazione con sb-monday-brief — sovrapposizione dichiarata

Il Detector 1 di `sb-monday-brief` ("opportunità mancate") già incrocia OTB/STLY con la
domanda di destinazione IBE — è, di fatto, una versione ridotta della lente **X1** qui
sotto, calcolata ogni lunedì con soglie fisse e un solo esito sì/no. Questa skill è la
versione **on-demand, guidata dalla domanda dell'utente, su 7 lenti e periodi qualsiasi**.
La sovrapposizione è voluta, non un difetto da correggere subito: non spostare qui la
logica del Detector 1 finché quel detector resta l'unico validato su dati reali per
l'alert settimanale. Se in futuro si consolidano, il Detector 1 dovrebbe richiamare X1 di
questa skill invece di ricalcolare la propria versione — annotalo come debito tecnico, non
farlo silenziosamente.

## Le due fonti (mai duplicate qui)

| Fonte | Cosa fornisce | Come si invoca |
|---|---|---|
| `sb-revenue-lens` | Domanda d'area, disponibilità, restrizioni MinLOS/MaxLOS, parità OTA, posizionamento di segmento — lenti L1-L6 | Agentica: le poni la stessa domanda/periodo che porresti a un consulente, o nomini direttamente la lente (es. "usa la lente L3 su luglio") |
| `sb-reservation-insights` | Pickup, on-the-books, mix canale, ADR reale per canale, mercati di provenienza, anticipo reale, cancellazioni — dal Back Office | Agentica: stessa logica, in linguaggio naturale, sullo stesso periodo |

Non risolvere tu il Property ID: passa lo stesso nome/ID a entrambe le invocazioni e lascia
che ciascuna faccia la propria risoluzione (la usano già in modo affidabile, e gli ID sono
condivisi fra i due MCP — non serve una terza risoluzione qui).

## Prima di iniziare

Servono **hotel** e **periodo**, esattamente come per `sb-revenue-lens`. Se il periodo non
è chiaro né deducibile dal contesto, chiedilo — non tirarlo a caso. Se esiste un default
ragionevole (vedi `config/defaults.yaml:default_window`), usalo e dichiara sempre quale
periodo hai usato.

## Router delle 7 lenti incrociate

Mappa la domanda dell'utente su una o più lenti. Se ambigua, chiedi con scelta multipla.
Se l'utente non fa una domanda specifica ("guarda giugno"), esegui X1 (la più universale)
e offri le altre.

| Trigger nella domanda | Lente |
|---|---|
| "sto seguendo il mercato", "vendo abbastanza rispetto alla domanda", "domanda vs vendite" | **X1 — Pace comparativo** |
| "ho domanda ma non vendo", "perché non converto", "cosa mi blocca" | **X2 — Freni alla conversione** |
| "il mio prezzo tiene", "sto perdendo quota su un canale", "parità e vendite reali" | **X3 — Prezzo e parità realizzata** |
| "i miei pacchetti coprono la domanda", "il catalogo intercetta il mercato" | **X4 — Prodotto vs domanda** |
| "chi cerca vs chi prenota", "mercato scoperto", "segmento non intercettato" | **X5 — Mercati e segmenti** |
| "apro troppo tardi/presto le vendite", "finestra di vendita vs mercato" | **X6 — Pacing** |
| "quale struttura cattura meglio la domanda", "confronto portafoglio" | **X7 — Portafoglio** |

Dettaglio di ciascuna lente (input, confronto, classificazione): `references/cross-lenses.md`.
Quale invocazione esatta fare a ciascuna fonte, per ciascuna lente: `references/orchestration.md`.

## Workflow

1. **Identifica hotel, periodo e lente** (router sopra).
2. **Invoca `sb-revenue-lens`** con la domanda/lente pertinente sul periodo. Salva la
   risposta (numeri della tabella evidenze inclusi) verbatim.
3. **Invoca `sb-reservation-insights`** con la domanda equivalente sullo stesso periodo e,
   dove possibile, sulla stessa granularità (settimanale — vedi "Allineamento delle
   finestre" in `references/orchestration.md`). Salva la risposta verbatim.
4. **Calcola il confronto** secondo la lente attivata. Scrivi i numeri in un JSON e lancia:

   ```bash
   python3 <skill-dir>/scripts/verify.py claims.json
   ```

   Se esce non-zero, il confronto non va in risposta: correggilo o dichiara cosa non torna.
5. **Rispondi**: fatto (i due numeri, la fonte di ciascuno) e classificazione (in linea /
   da verificare / scostamento marcato) — mai la causa come certezza, solo come ipotesi da
   verificare con l'albergatore. Dichiara sempre il caveat destinazione-vs-struttura quando
   pertinente (quasi sempre, tranne X2 che è puramente meccanico).
6. **Offri il report brandizzato**, se richiesto, riusando lo script di `sb-revenue-lens`
   come base di layout (non scriverne uno nuovo da zero) — estensione futura, vedi sotto.

## Guardrail

- **Non è consulenza prescrittiva.** Come `sb-revenue-lens`: mostra il confronto e 1-3
  domande di verifica, non un "fai X".
- **Cannibalizzazione — stessa regola di `sb-monday-brief`.** "Questo cliente avrebbe
  prenotato comunque in diretto?" non è misurabile qui: non affermarlo mai.
- **Il report va a un cliente.** Nel confronto multi-struttura (X7), nessun dato di altre
  property se l'output è per un singolo hotel; il ranking è solo per chi gestisce l'intero
  portafoglio (stessa regola di `sb-monday-brief`).
- **Fatto vs inferenza sempre distinti**, come in `sb-revenue-lens`.
- **Se una delle due fonti non è disponibile in sessione**, fermati e dichiaralo — non
  stimare il lato mancante con un numero indovinato.

## Estensioni future (non ancora implementate)

- Report brandizzato HTML/PDF (riuso di `sb-revenue-lens/scripts/build_report.py` come base).
- Validazione più ampia delle 7 lenti su altre property, periodi e configurazioni.
- Eventuale consolidamento con il Detector 1 di `sb-monday-brief` (vedi sopra).

## File di supporto

| Percorso | Contenuto |
|---|---|
| `config/defaults.yaml` | finestra di default, soglie di classificazione del gap |
| `references/orchestration.md` | quale invocazione fare a ciascuna fonte, per ciascuna lente; allineamento delle finestre temporali |
| `references/cross-lenses.md` | specifica formale delle 7 lenti incrociate: input, confronto, classificazione |
| `scripts/verify.py` | ricalcola l'aritmetica del confronto (delta, quota, intersezione) prima che un numero vada in risposta |
| `templates/sb-demand-capture-example-questions.html` | catalogo di 23 domande di esempio in 7 categorie, per presentare la skill a un cliente |
