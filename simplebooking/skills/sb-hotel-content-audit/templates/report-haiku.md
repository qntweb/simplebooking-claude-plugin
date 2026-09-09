# Report Template — Haiku (Simplified)

## Haiku Rules

1. **MICRO-BATCH PROCESSING:** For each section × language:
   call API → compare against master → write row → discard raw data.
   Do NOT accumulate data in memory.

2. **MECHANICAL RULES ONLY:** Apply Rules 1→6 (config/rules.md).
   Do NOT perform qualitative analysis (USP, tone, creativity).
   Do NOT suggest text rewrites.

3. **RIGID TEMPLATE:** Fill in exactly this structure.
   Do NOT add narrative sections. Do NOT add discursive comments.

4. **If the context gets long:** write a partial result
   and continue. A report in two parts is better than an incomplete one.

---

Copy and fill in EXACTLY:

# 🏨 Content Audit Report — [HOTEL_NAME]
📅 [DATE] | 🆔 ID: [PROPERTY_ID] | 🌍 Master: [MASTER_LANG]

## 📊 Executive Summary

| Section | [L1] (M) | [L2] | [L3] | [LN] |
|---------|:---:|:---:|:---:|:---:|
| Hotel Info | [S] | [S] | [S] | [S] |
| Room Types | [S] | [S] | [S] | [S] |
| Rate Plans | [S] | [S] | [S] | [S] |
| Offers | [S] | [S] | [S] | [S] |
| Packages | [S] | [S] | [S] | [S] |
| Services | [S] | [S] | [S] | [S] |
| Meal Plans | [S] | [S] | [S] | [S] |
| Cancellation | [S] | [S] | [S] | [S] |

[S] = worst status in the section for that language.
❌ at least 1 critical | ⚠️ at least 1 warning (0 critical) | ✅ all ok | ➖ not audited

**Totals: ✅ [n] | ⚠️ [n] | ❌ [n] | ⚪ [n]**
**Completeness: [X]%** (✅+⚪ fields / total × 100)

## 🔍 Detail by Section

(Only if REPORT_DETAIL = "detailed")
Repeat FOR EACH audited section:

### [EMOJI] [SECTION_NAME]

| Item | Field | [L1](M) | [L2] | [L3] | [LN] |
|----------|-------|:---:|:---:|:---:|:---:|
| [name] | name | ✅ | ✅ | ❌ empty | ✅ |
| [name] | description | ✅ 420c | ⚠️ =M | ❌ empty | ⚠️ 85c |

## 📋 Issue List

| # | Severity | Section | Item | Field | Language | Issue |
|---|:---:|---------|----------|-------|--------|----------|
| 1 | ❌ | [sect] | [item] | [field] | [lang] | [issue] |

Sorted by: severity (❌ first) → section → item → language.
Include ALL issues. Do NOT summarize or group them.

---

## Step 9 — Simplified output

### 9A — Triage (if significant issues)

| # | Language | ❌ | ⚠️ | Compl.% | Traffic% | Demand% | Priority |
|---|--------|---|---|---------|-----------|----------|----------|
| 1 | FR | 5 | 3 | 28% | 22% | 18% | 🔴 HIGH |

Priority = ranking: (❌×3 + ⚠️) × (Traffic% + Demand%) DESC.
🔴 top 33% | 🟡 mid 33% | 🟢 bottom 33%.
Analytics columns only if the tool is available. No narrative.

### 9B — Opportunity (if the audit is good)

| # | Country | Language | Enabled? | Traffic% | Demand% | Opportunity |
|---|-------|--------|:---:|-----------|----------|-------------|
| 1 | South Korea | KO | ❌ | 8% | 12% | 🔴 HIGH |

Only markets with >= 5% traffic OR demand with a language NOT enabled.
No narrative. Table only.

---

## Export

PDF → /mnt/skills/public/pdf/SKILL.md
Excel → /mnt/skills/public/xlsx/SKILL.md — Sheets: "Summary", "Issues", "Triage"/"Opportunities"
CSV → Header: Section,Item,Field,Language,Status,Issue,Severity,CharCount,MasterCharCount,IsMaster,TrafficPct,DemandPct,PriorityScore
JSON → meta + summary + issues[] + triage[] + opportunities[]
