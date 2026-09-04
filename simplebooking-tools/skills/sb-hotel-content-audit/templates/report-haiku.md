# Template Report — Haiku (Semplificato)

## Regole Haiku

1. **MICRO-BATCH PROCESSING:** Per ogni sezione × lingua:
   chiama API → confronta con master → scrivi riga → butta dati grezzi.
   NON accumulare dati in memoria.

2. **SOLO REGOLE MECCANICHE:** Applica Regole 1→6 (config/rules.md).
   NON fare analisi qualitative (USP, tone, creatività).
   NON suggerire riscritture di testo.

3. **TEMPLATE RIGIDO:** Compila esattamente questa struttura.
   NON aggiungere sezioni narrative. NON aggiungere commenti discorsivi.

4. **Se il contesto diventa lungo:** scrivi un risultato parziale
   e continua. Meglio report in due parti che report incompleto.

---

Copia e compila ESATTAMENTE:

# 🏨 Content Audit Report — [NOME_HOTEL]
📅 [DATA] | 🆔 ID: [PROPERTY_ID] | 🌍 Master: [MASTER_LANG]

## 📊 Executive Summary

| Sezione | [L1] (M) | [L2] | [L3] | [LN] |
|---------|:---:|:---:|:---:|:---:|
| Hotel Info | [S] | [S] | [S] | [S] |
| Room Types | [S] | [S] | [S] | [S] |
| Rate Plans | [S] | [S] | [S] | [S] |
| Offers | [S] | [S] | [S] | [S] |
| Packages | [S] | [S] | [S] | [S] |
| Services | [S] | [S] | [S] | [S] |
| Meal Plans | [S] | [S] | [S] | [S] |
| Cancellation | [S] | [S] | [S] | [S] |

[S] = stato peggiore della sezione per quella lingua.
❌ almeno 1 critico | ⚠️ almeno 1 warning (0 critici) | ✅ tutto ok | ➖ non auditata

**Totali: ✅ [n] | ⚠️ [n] | ❌ [n] | ⚪ [n]**
**Completezza: [X]%** (campi ✅+⚪ / totale × 100)

## 🔍 Dettaglio per Sezione

(Solo se REPORT_DETAIL = "dettagliato")
Ripeti PER OGNI sezione auditata:

### [EMOJI] [NOME_SEZIONE]

| Elemento | Campo | [L1](M) | [L2] | [L3] | [LN] |
|----------|-------|:---:|:---:|:---:|:---:|
| [nome] | nome | ✅ | ✅ | ❌ vuoto | ✅ |
| [nome] | descrizione | ✅ 420c | ⚠️ =M | ❌ vuoto | ⚠️ 85c |

## 📋 Lista Issue

| # | Severity | Sezione | Elemento | Campo | Lingua | Problema |
|---|:---:|---------|----------|-------|--------|----------|
| 1 | ❌ | [sez] | [elem] | [campo] | [lang] | [problema] |

Ordinata per: severity (❌ prima) → sezione → elemento → lingua.
Includere TUTTE le issue. NON riassumere o raggruppare.

---

## Step 9 — Output semplificato

### 9A — Triage (se problemi significativi)

| # | Lingua | ❌ | ⚠️ | Compl.% | Traffico% | Domanda% | Priorità |
|---|--------|---|---|---------|-----------|----------|----------|
| 1 | FR | 5 | 3 | 28% | 22% | 18% | 🔴 ALTA |

Priorità = ranking: (❌×3 + ⚠️) × (Traffico% + Domanda%) DESC.
🔴 top 33% | 🟡 mid 33% | 🟢 bottom 33%.
Colonne analytics solo se tool disponibile. Nessuna narrativa.

### 9B — Opportunità (se audit buono)

| # | Paese | Lingua | Abilitata? | Traffico% | Domanda% | Opportunità |
|---|-------|--------|:---:|-----------|----------|-------------|
| 1 | South Korea | KO | ❌ | 8% | 12% | 🔴 ALTA |

Solo mercati >= 5% traffico O domanda con lingua NON abilitata.
Nessuna narrativa. Solo tabella.

---

## Export

PDF → /mnt/skills/public/pdf/SKILL.md
Excel → /mnt/skills/public/xlsx/SKILL.md — Fogli: "Summary", "Issues", "Triage"/"Opportunities"
CSV → Header: Section,Item,Field,Language,Status,Issue,Severity,CharCount,MasterCharCount,IsMaster,TrafficPct,DemandPct,PriorityScore
JSON → meta + summary + issues[] + triage[] + opportunities[]
