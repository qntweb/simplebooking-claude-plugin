# Report Template — Full (Sonnet/Opus)

Use this template to generate the report. Replace the [...] placeholders.
You can add narrative sections and qualitative suggestions.

---

# 🏨 Content Audit Report — [HOTEL_NAME]
📅 Date: [DATE] | 🆔 Property ID: [ID] | 🌍 Master Language: [MASTER_LANG]

## 📊 Executive Summary

| Section | [LANG_1] (M) | [LANG_2] | [LANG_3] | ... |
|---------|:---:|:---:|:---:|:---:|
| Hotel Info | [S] | [S] | [S] | ... |
| Room Types | [S] | [S] | [S] | ... |
| Rate Plans | [S] | [S] | [S] | ... |
| Offers | [S] | [S] | [S] | ... |
| Packages | [S] | [S] | [S] | ... |
| Services | [S] | [S] | [S] | ... |
| Meal Plans | [S] | [S] | [S] | ... |
| Cancellation | [S] | [S] | [S] | ... |

**📈 Overall Score: [X]% completeness | [Y] issues found**
**🔴 Critical: [n] | 🟡 Warning: [n] | 🟢 OK: [n]**

## 🌍 Master Language Analysis ([MASTER_LANGUAGE])

(Only if AUDIT_TYPE includes "quality")
Status of the source texts. If the master language has issues,
highlight that ALL derived translations will be impacted.
This section has the highest priority in the suggestions.

## 🔍 Missing Translations

(If AUDIT_TYPE includes "translations")
For each section, a table comparing against the master language.

| Field | [MASTER] | [LANG_2] | [LANG_3] | Note |
|-------|:---:|:---:|:---:|------|
| Hotel Description | ✅ 850c | ✅ 720c | ❌ empty | [LANG_3]: missing |
| Room "Deluxe" desc | ✅ 420c | ⚠️ =M | ❌ empty | [LANG_2]: suspected copy |
| Address | ✅ | ⚪ =M | ⚪ =M | Identical (expected) |

## ✨ Quality Check

(If AUDIT_TYPE includes "quality")
For each section, issues found with severity and suggestions.

| Item | Language | Issue | Severity | Suggestion |
|----------|--------|-------|:---:|--------------|
| [name] | [lang] | [description] | [emoji] | [hospitality-tone suggestion] |

## 📝 Detailed Suggestions

(Only if REPORT_DETAIL = "detailed")
For each critical issue:
- Current text (truncated, with character count)
- Suggested/corrected text (hospitality tone of voice)
- Rationale
- If the issue is on master → cascading impact

## 🎯 Prioritized Action Items

1. ❌ [CRITICAL — MASTER] ...
2. ❌ [CRITICAL] ...
3. ⚠️ [IMPORTANT] ...
4. 💡 [SUGGESTION] ...

Issues on MASTER always at the top. Then by decreasing severity.

## 💡 Recommended Next Step

(Filled in after Step 9 if run — see config/analytics.md)

---

## Export formats

### PDF
Read /mnt/skills/public/pdf/SKILL.md. Include the priority matrix/opportunity map if generated.

### Excel
Read /mnt/skills/public/xlsx/SKILL.md.
Sheets: "Summary", 1 per section, "Action Items",
"Priority Matrix" (if 9A), "Opportunities" (if 9B), "Analytics Data" (if 9A/9B).
Conditional formatting by severity.

### CSV
Header: Section,Item,Field,Language,Status,Issue,Severity,Suggestion,
IsMasterLanguage,CharCount,MasterCharCount,TrafficShare,DemandShare,
DemandTrend,PriorityScore,IsOpportunity,OpportunityLevel
UTF-8 BOM. Comma. Quoting.

### JSON
Structure: meta → summary → issues[] → action_items[] →
priority_matrix (if 9A) → opportunity_map (if 9B).
Include "available_tools" in meta.
