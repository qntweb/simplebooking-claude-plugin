# Template Report — Full (Sonnet/Opus)

Usa questo template per generare il report. Sostituisci i placeholder [...].
Puoi aggiungere sezioni narrative e suggerimenti qualitativi.

---

# 🏨 Content Audit Report — [NOME_HOTEL]
📅 Data: [DATA] | 🆔 Property ID: [ID] | 🌍 Lingua Master: [MASTER_LANG]

## 📊 Executive Summary

| Sezione | [LANG_1] (M) | [LANG_2] | [LANG_3] | ... |
|---------|:---:|:---:|:---:|:---:|
| Hotel Info | [S] | [S] | [S] | ... |
| Room Types | [S] | [S] | [S] | ... |
| Rate Plans | [S] | [S] | [S] | ... |
| Offers | [S] | [S] | [S] | ... |
| Packages | [S] | [S] | [S] | ... |
| Services | [S] | [S] | [S] | ... |
| Meal Plans | [S] | [S] | [S] | ... |
| Cancellation | [S] | [S] | [S] | ... |

**📈 Score Complessivo: [X]% completezza | [Y] issues trovate**
**🔴 Critiche: [n] | 🟡 Warning: [n] | 🟢 OK: [n]**

## 🌍 Analisi Lingua Master ([MASTER_LANGUAGE])

(Solo se AUDIT_TYPE include "quality")
Stato dei testi sorgente. Se la lingua master ha problemi,
evidenziare che TUTTE le traduzioni derivate ne saranno impattate.
Questa sezione ha priorità massima nei suggerimenti.

## 🔍 Missing Translations

(Se AUDIT_TYPE include "translations")
Per ogni sezione, tabella con confronto contro la lingua master.

| Campo | [MASTER] | [LANG_2] | [LANG_3] | Note |
|-------|:---:|:---:|:---:|------|
| Hotel Description | ✅ 850c | ✅ 720c | ❌ vuoto | [LANG_3]: mancante |
| Room "Deluxe" desc | ✅ 420c | ⚠️ =M | ❌ vuoto | [LANG_2]: sospetta copia |
| Indirizzo | ✅ | ⚪ =M | ⚪ =M | Identico atteso |

## ✨ Quality Check

(Se AUDIT_TYPE include "quality")
Per ogni sezione, problemi trovati con severity e suggerimenti.

| Elemento | Lingua | Issue | Severity | Suggerimento |
|----------|--------|-------|:---:|--------------|
| [nome] | [lang] | [descrizione] | [emoji] | [suggerimento hospitality] |

## 📝 Suggerimenti Dettagliati

(Solo se REPORT_DETAIL = "detailed")
Per ogni issue critica:
- Testo attuale (troncato, con conteggio caratteri)
- Testo suggerito / corretto (tone of voice hospitality)
- Motivazione
- Se issue su master → impatto a cascata

## 🎯 Action Items Prioritizzati

1. ❌ [CRITICO — MASTER] ...
2. ❌ [CRITICO] ...
3. ⚠️ [IMPORTANTE] ...
4. 💡 [SUGGERIMENTO] ...

Issue su MASTER sempre in cima. Poi per severity decrescente.

## 💡 Next Step Consigliato

(Compilato dopo Step 9 se eseguito — vedi config/analytics.md)

---

## Formati export

### PDF
Leggi /mnt/skills/public/pdf/SKILL.md. Includere matrice/opportunità se generata.

### Excel
Leggi /mnt/skills/public/xlsx/SKILL.md.
Fogli: "Summary", 1 per sezione, "Action Items",
"Priority Matrix" (se 9A), "Opportunities" (se 9B), "Analytics Data" (se 9A/9B).
Formattazione condizionale per severity.

### CSV
Header: Section,Item,Field,Language,Status,Issue,Severity,Suggestion,
IsMasterLanguage,CharCount,MasterCharCount,TrafficShare,DemandShare,
DemandTrend,PriorityScore,IsOpportunity,OpportunityLevel
UTF-8 BOM. Virgola. Quoting.

### JSON
Struttura: meta → summary → issues[] → action_items[] →
priority_matrix (se 9A) → opportunity_map (se 9B).
Includere "available_tools" in meta.
