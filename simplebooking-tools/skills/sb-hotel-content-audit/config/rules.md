# Regole di Classificazione

Per OGNI campo di OGNI elemento, applica queste regole nell'ordine.
FERMARSI ALLA PRIMA CHE CORRISPONDE. Un campo ha UN SOLO stato.

## Regola 1 — Campo vuoto?
Se il campo è vuoto, null, o contiene solo spazi/tag HTML vuoti:
→ **❌ CRITICO** | Nota: "[Lingua]: campo vuoto"

## Regola 2 — Campo identità?
Se il campo è un IDENTITY_FIELD E il testo è identico alla lingua master:
→ **⚪ ATTESO** | Nota: "Identico (atteso)"

### Lista IDENTITY_FIELDS:
- Indirizzi, CAP, città (forma locale)
- Numeri di telefono, fax
- Email, URL, link social
- Coordinate GPS
- Codici (ID camera, codici tariffari)
- Nomi di brand, piattaforme, catene
- Orari (formato numerico)
- Prezzi e valute

## Regola 3 — Testo identico al master?
Se il campo NON è identity E il testo è identico al master:
→ **⚠️ WARNING** | Nota: "[Lingua]: identico a [MASTER] — sospetta copia"

## Regola 4 — Soglia lunghezza? (solo se check formale attivo)
Conta i caratteri del testo (esclusi tag HTML).

### Descrizione Hotel:
| Caratteri | Stato | Nota |
|-----------|-------|------|
| < 200     | ❌ CRITICO | "[N]c — sotto minimo (200)" |
| < 500     | ⚠️ WARNING | "[N]c — sotto consigliato (500)" |
| >= 500    | ✅ OK | "[N]c" |

### Descrizione Camera:
| Caratteri | Stato | Nota |
|-----------|-------|------|
| < 80      | ❌ CRITICO | "[N]c — sotto minimo (80)" |
| < 200     | ⚠️ WARNING | "[N]c — sotto consigliato (200)" |
| >= 200    | ✅ OK | "[N]c" |

### Descrizione Offerta/Pacchetto:
| Caratteri | Stato | Nota |
|-----------|-------|------|
| < 100     | ⚠️ WARNING | "[N]c — sotto consigliato (100)" |
| >= 100    | ✅ OK | "[N]c" |

## Regola 5 — HTML rotto? (solo se check formale attivo)
Cerca tag aperti senza chiusura: `<p>` senza `</p>`, `<b>` senza `</b>`,
`<div>` senza `</div>`, `<ul>`/`<li>` non chiusi.
Se trovati:
→ **❌ CRITICO** | Nota: "HTML rotto: [tag] non chiuso"

## Regola 6 — Nessun problema
Se nessuna regola precedente si applica:
→ **✅ OK** | Nota: "[N]c"

## Quality Check Qualitativo (SOLO Sonnet/Opus)

Se AUDIT_TYPE include "quality", queste regole AGGIUNTIVE si applicano
DOPO le regole meccaniche 1→6:

- **Nessuna USP identificabile** nella descrizione → ⚠️ WARNING
- **Tono non hospitality** (troppo tecnico/freddo) → ⚠️ WARNING
- **Nessuna CTA o benefit** chiaro in offerte/pacchetti → ⚠️ WARNING
- **Mancanza parole sensoriali/emozionali** → 💡 SUGGERIMENTO
- Issue su lingua master → priorità assoluta (impatto a cascata)

Per Haiku: IGNORARE queste regole qualitative. Solo Regole 1→6.

## Emoji di stato

| Emoji | Significato |
|-------|------------|
| ✅ | OK — nessun problema |
| ⚠️ | Warning — problema minore |
| ❌ | Critico — traduzione mancante o errore grave |
| ⚪ | Identico atteso — campo identity, normale |
| ➖ | N/A — sezione non applicabile |
| 💡 | Suggerimento — miglioramento opzionale |

## Stato aggregato per sezione (Executive Summary)

Per assegnare lo stato di una SEZIONE per una lingua:
- ❌ se almeno 1 campo critico
- ⚠️ se almeno 1 warning E 0 critici
- ✅ se tutto ok
- ➖ se sezione non auditata
