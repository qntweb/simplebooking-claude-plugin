# Classification Rules

For EVERY field of EVERY item, apply these rules in order.
STOP AT THE FIRST ONE THAT MATCHES. A field has ONE status only.

## Rule 1 — Empty field?
If the field is empty, null, or contains only whitespace/empty HTML tags:
→ **❌ CRITICAL** | Note: "[Language]: empty field"

## Rule 2 — Identity field?
If the field is an IDENTITY_FIELD AND the text is identical to the master language:
→ **⚪ EXPECTED** | Note: "Identical (expected)"

### IDENTITY_FIELDS list:
- Addresses, postal codes, city (local form)
- Phone numbers, fax
- Emails, URLs, social links
- GPS coordinates
- Codes (room IDs, rate codes)
- Brand, platform, chain names
- Hours (numeric format)
- Prices and currencies

## Rule 3 — Text identical to master?
If the field is NOT identity AND the text is identical to the master:
→ **⚠️ WARNING** | Note: "[Language]: identical to [MASTER] — suspected copy"

## Rule 4 — Length threshold? (only if the formal check is active)
Count the characters in the text (excluding HTML tags).

### Hotel Description:
| Characters | Status | Note |
|-----------|-------|------|
| < 200     | ❌ CRITICAL | "[N]c — below minimum (200)" |
| < 500     | ⚠️ WARNING | "[N]c — below recommended (500)" |
| >= 500    | ✅ OK | "[N]c" |

### Room Description:
| Characters | Status | Note |
|-----------|-------|------|
| < 80      | ❌ CRITICAL | "[N]c — below minimum (80)" |
| < 200     | ⚠️ WARNING | "[N]c — below recommended (200)" |
| >= 200    | ✅ OK | "[N]c" |

### Offer/Package Description:
| Characters | Status | Note |
|-----------|-------|------|
| < 100     | ⚠️ WARNING | "[N]c — below recommended (100)" |
| >= 100    | ✅ OK | "[N]c" |

## Rule 5 — Broken HTML? (only if the formal check is active)
Look for opening tags without a closing tag: `<p>` without `</p>`, `<b>` without `</b>`,
`<div>` without `</div>`, unclosed `<ul>`/`<li>`.
If found:
→ **❌ CRITICAL** | Note: "Broken HTML: unclosed [tag]"

## Rule 6 — No issue
If none of the previous rules apply:
→ **✅ OK** | Note: "[N]c"

## Qualitative Quality Check (Sonnet/Opus ONLY)

If AUDIT_TYPE includes "quality", these ADDITIONAL rules apply AFTER the mechanical
rules 1→6:

- **No identifiable USP** in the description → ⚠️ WARNING
- **Non-hospitality tone** (too technical/cold) → ⚠️ WARNING
- **No clear CTA or benefit** in offers/packages → ⚠️ WARNING
- **Lack of sensory/emotional words** → 💡 SUGGESTION
- Issues on the master language → absolute priority (cascading impact)

For Haiku: IGNORE these qualitative rules. Rules 1→6 only.

## Status emoji

| Emoji | Meaning |
|-------|------------|
| ✅ | OK — no issue |
| ⚠️ | Warning — minor issue |
| ❌ | Critical — missing translation or serious error |
| ⚪ | Expected identical — identity field, normal |
| ➖ | N/A — section not applicable |
| 💡 | Suggestion — optional improvement |

## Aggregated status per section (Executive Summary)

To assign the status of a SECTION for a language:
- ❌ if at least 1 critical field
- ⚠️ if at least 1 warning AND 0 critical
- ✅ if everything is ok
- ➖ if the section wasn't audited
