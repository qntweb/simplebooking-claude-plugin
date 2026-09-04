---
name: sb-hotel-content-audit
metadata:
  author: Sergio Farinelli
  organization: QNT — SimpleBooking — Zucchetti Group
description: >
  Audit strutturato dei contenuti hotel su piattaforma SimpleBooking.
  Verifica traduzioni mancanti, qualità testi, completezza informazioni
  per tutte le lingue abilitate. Usa quando l'utente chiede di controllare,
  auditare, verificare contenuti, traduzioni, localizzazioni di un hotel
  su SimpleBooking, o quando menziona "content audit", "verifica traduzioni",
  "controllo contenuti hotel".
---

# 🏨 Hotel Content Audit — Skill per Claude Cowork

## Panoramica

Questo skill guida un audit strutturato dei contenuti di un hotel nel sistema
SimpleBooking (CRS). Verifica traduzioni mancanti, soglie di lunghezza,
HTML rotto e completezza per tutte le lingue abilitate.

## File di supporto in questa skill

Prima di iniziare, leggi questi file nell'ordine indicato:

1. **config/hotels.md** — Tabella di riferimento Hotel → ID SimpleBooking e GA4
2. **config/default.yaml** — Parametri configurabili (soglie, lookback, ecc.)
3. **config/rules.md** — Regole di classificazione meccanica (Regole 1→6)
4. **templates/report-full.md** — Template report per Sonnet/Opus
5. **templates/report-haiku.md** — Template report semplificato per Haiku
6. **config/analytics.md** — Istruzioni Step 9 (GA4 + Data Lake)

## Quale template usare

- Se stai girando come **Haiku** o il parametro `FORCE_MICRO_BATCH: true`:
  usa `templates/report-haiku.md` e segui le regole micro-batch.
- Altrimenti: usa `templates/report-full.md`.

In caso di dubbio, chiedi all'utente: "Preferisci un audit rapido e
sintetico (checklist) o un audit completo con suggerimenti qualitativi?"

## MCP Tools richiesti

- **SimpleBooking MCP** — OBBLIGATORIO. Senza questo il workflow non parte.
- **Google Analytics MCP** — Opzionale, auto-detect in Step 8.5
- **Zucchetti Travel Data Lake MCP** — Opzionale, auto-detect in Step 8.5

NON chiedere all'utente se ha i tool. Verificali silenziosamente (Step 8.5).

## Workflow — Step by Step

Procedi SEMPRE in ordine. Ad ogni step, attendi la risposta dell'utente.
Usa il tool `ask_user_input_v0` quando possibile.

### STEP 1 — Lingua della conversazione
Chiedi lingua. Opzioni: Italiano, English, Français, Deutsch, Español.
Da qui in poi TUTTO nella lingua scelta.

### STEP 2 — Selezione hotel
Chiedi hotel (nome o ID). Usa `config/hotels.md` per risolvere.
Se non in lista → chiedi Property ID SimpleBooking.

### STEP 3 — Info base + Lingua Master + Lingue audit
1. Chiama `property_get_basic_info` (lingua conversazione)
2. Mostra: nome, stelle, città, lingue abilitate
3. Chiedi **MASTER_LANGUAGE** (default: IT) — la lingua sorgente da cui
   derivano le traduzioni. Tutte le altre confrontate contro questa.
4. Chiedi **AUDIT_LANGUAGES**: tutte o selezione. Master sempre inclusa.
5. Salva anche **ALL_ENABLED_LANGUAGES** (serve per Step 9B)

### STEP 4 — Selezione sezioni
multi_select: Hotel Info, Room Types, Rate Plans, Offers, Packages,
Services, Meal Plans, Cancellation Policies, TUTTO.

### STEP 5 — Tipo di controllo
single_select:
- 🔍 Solo traduzioni mancanti
- 📏 Solo check formale (soglie + HTML)
- ✨ Quality check qualitativo (USP, tone — solo Sonnet/Opus)
- 🔍📏 Traduzioni + Formale (DEFAULT)
- 🔍📏✨ Tutto (solo Sonnet/Opus)

### STEP 6 — Livello dettaglio
single_select:
- ⚡ Quick — tabella riassuntiva + conteggi
- 📝 Dettagliato — tabella per ogni sezione, ogni campo

### STEP 7 — Conferma e avvio
Mostra recap parametri. Chiedi conferma.
Poi procedi con le chiamate API.

**Strategia API:** Per ogni sezione × lingua, chiama il tool appropriato.
Lingua master PRIMA. Leggi `config/rules.md` per le regole di classificazione.

Rispetta `MAX_API_CALLS_PER_BLOCK` (vedi config/default.yaml).
Mostra avanzamento: "✅ [Sezione] completata ([N]/[TOT])"

### STEP 8 — Generazione report
Usa il template appropriato (full o haiku) da `templates/`.
Compila tutti i placeholder con i risultati dell'audit.

### STEP 8.5 — MCP Probe (silenzioso)
INVISIBILE all'utente. Leggi `config/analytics.md` per dettagli.
Prova `get_account_summaries()` e `destination_get_report_options()`.
Se falliscono → salta Step 9. MAI menzionare tool assenti.

### STEP 9 — Next Step Intelligente
Solo se almeno 1 tool opzionale disponibile.
Leggi `config/analytics.md` per la logica completa (9A Triage / 9B Opportunità).

### STEP 10 — Esportazione
Sequenziale: un formato alla volta, poi chiedi se ne serve un altro.
PDF → leggi /mnt/skills/public/pdf/SKILL.md
Excel → leggi /mnt/skills/public/xlsx/SKILL.md

## Regole generali

1. Step-by-step, mai saltare.
2. `ask_user_input_v0` per domande a scelta.
3. Lingua Step 1 = lingua di tutto.
4. Issue su MASTER → priorità massima (impatto a cascata).
5. Identity fields (indirizzi, telefoni, email, GPS, codici) → ⚪ non ⚠️.
6. MAI menzionare tool non disponibili.
7. Probe MCP silenzioso.
8. Step 9 = suggerimento, mai forzato.
9. Esportazioni sequenziali.
10. Tono hospitality nei suggerimenti (solo Sonnet/Opus).
