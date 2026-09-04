# sb-revenue-lens — Struttura report brandizzato (modalità `report`)

Il report è firmato **SimpleBooking** e scritto per l'albergatore. Formati:
PDF/HTML (riuso degli helper docx/pdf/HTML esistenti). Lingua = conversazione.

## Sezioni (in ordine)

1. **Intestazione** — logo SimpleBooking, nome hotel, stelle, città, periodo
   analizzato, data analisi, raggio domanda d'area usato.

2. **La domanda** — la domanda dell'albergatore in chiaro (es. "Dove sto
   lasciando soldi a giugno?") e quali lenti sono state attivate.

3. **Sintesi in una riga** — il messaggio chiave per la proprietà.

4. **Quadro del periodo** — curva di domanda d'area per settimana (tabella +
   grafico), anticipo medio, distribuzione LOS richiesta. Etichetta: "domanda di
   destinazione, non dell'hotel".

5. **Segnali per lente** — una sottosezione per ogni lente attivata:
   - cosa ha trovato il detector (regola → date),
   - tabella evidenze (Data | Disponibilità | Prezzo notte | Domanda settimana),
   - lettura in linguaggio naturale,
   - opzioni operative (non prescrizioni).

6. **Mappa date** — calendario del periodo con codifica:
   🔴 sold-out · 🟠 tight/leak · 🟡 gap-night/MinLOS · 🟢 soft/invenduto.

7. **Cosa NON vede questa analisi** — blocco fisso: no on-the-books, no pickup,
   no competitor reali (solo parità OTA se attiva), no fonte eventi. Fatto vs
   inferenza.

8. **Eventi** — spazio per l'albergatore: "su queste date sei pieno/vuoto — sai
   se ci sono eventi/fiere?" (la skill non li afferma).

9. **Prossimi passi** — opzioni + offerta di scan schedulato / batch portfolio.

## Regole di stile
- Niente gergo RMS. Frasi brevi.
- Ogni numero ha la sua fonte nella tabella evidenze.
- Le raccomandazioni sono **opzioni con condizione** ("se la domanda regge, …"),
  mai ordini.
- Sempre presente la sezione 7 (limiti).
