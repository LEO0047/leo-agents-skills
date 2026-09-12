# Screening rules

## Authority

Use the three authority tracks in `run-lifecycle.md`. Current Notion governs rules, schema, and option labels; official/company evidence governs company facts; only a current explicit instruction governs mutation. Reconfirm volatile facts whenever the as-of date changes.

## Decision axes

Maintain two independent axes:

1. Hard-gate decision: `PASS`, `REVIEW`, or `REJECT`.
2. Business assessment: welfare tier, company stance, fit tags,公益 probability, and outreach angle.

`基礎之下` is not a rejection. It can indicate an unmet need and a viable outreach opportunity.

## Hard-gate decisions

- `PASS`: every applicable gate has direct, scope-compatible evidence.
- `REVIEW`: no directly failed gate, but at least one gate is missing, ambiguous, stale, or conflicted.
- `REJECT`: at least one applicable gate has direct evidence of failure.

Use reason subcodes such as `REVIEW_EMPLOYEE_SCOPE`, `REVIEW_BOX_ONLY`, or `REVIEW_BOX_SCOPE` to explain REVIEW. Do not treat them as a fourth decision level.

## Listed and OTC gates

- Current listed or OTC status.
- Employee count 40–99 inclusive; prioritize 50–99 operationally.
- Paid-in capital at or below TWD 1,000,000,000.
- An official ESG/sustainability webpage or equivalent official disclosure.
- Direct evidence of employee three-festival gift boxes.
- Three-festival cash bonus or clearly stated cash gifts.
- Funeral, bereavement, or condolence support.
- Parental, maternity, or childcare leave.
- Labor and health insurance.

A resolved, scope-compatible applicant-entity count below 40 or above 99 directly fails the listed/OTC employee gate. Do not carry the emerging-market no-upper-limit rule into listed/OTC screening.

## Emerging-market gates

- Current emerging-market status.
- Employee count at least 50, with no upper limit.
- Paid-in capital at or below TWD 1,000,000,000.
- The same five welfare gates as listed/OTC.
- ESG report or official ESG page is supplemental, not a rejection gate. Record `無ESG報告書` when that exact option exists in the current Notion schema.

Exclude public-only, private/unlisted, and companies whose eligible current status has ended. Keep unmatched records in an audit list.

## Employee-count basis

Prefer the newest comparable source for the Taiwan applicant legal entity. Preserve every meaningful observation rather than overwriting conflicts. Record for each observation:

- value;
- legal-entity or group scope;
- period-end, current, or annual-average measure;
- effective date/reporting year;
- source-field update date when available;
- retrieval/verification date and evidence IDs;
- whether it is eligible for the gate;
- any derivation formula and its operands.

Company-maintained 104/1111 data can be used as current corroboration. Official filings remain the preferred scope evidence. If comparable sources cross a gate boundary, set REVIEW. If one source clearly includes subsidiaries and another is the applicant entity, do not manufacture a conflict.

Select one normalized employee value and explain why. Label an annual average as an average, never as a period-end count. If a financial-report employee basis explicitly includes non-employee directors, derive the employee value only when the formula and disclosed inputs are preserved. Do not inherit a group/applicant scope conclusion from another document, field, or period without a direct bridge.

Never convert an unknown employee count to zero.

## Welfare evidence

Evaluate each gate separately.

- A policy explicitly saying `三節禮盒`, or direct records of employee gift-box distribution at Lunar New Year, Dragon Boat Festival, and Mid-Autumn Festival, can support the gift-box gate.
- `三節獎金／禮品` is ambiguous. It does not prove both cash and gift-box gates.
- `三節禮金 & 禮盒` can support both when it comes from an official or company-maintained source, but seek an independent distribution record and note confidence.
- Three separately named cash gifts plus a generic `節日禮盒` proves the cash gate but not that Lunar New Year, Dragon Boat Festival, and Mid-Autumn Festival each had an employee gift box. Keep the box gate as `REVIEW_BOX_SCOPE`.
- Accounting examples mentioning gift boxes do not prove actual distribution.
- Gifts to customers, shareholders, suppliers, or event guests are not employee welfare.

For package v2, classify welfare evidence with structured claim codes. A gift-box PASS needs `THREE_FESTIVAL_GIFT_BOXES_EXPLICIT`, `THREE_SEPARATE_EMPLOYEE_BOX_DISTRIBUTIONS`, or `CASH_AND_BOX_EXPLICIT`. A cash PASS needs `THREE_FESTIVAL_CASH_EXPLICIT` or `CASH_AND_BOX_EXPLICIT`. `GENERIC_FESTIVAL_BOX` and `AMBIGUOUS_CASH_OR_GIFT` cannot support PASS by themselves.

## Source hierarchy

1. Official ESG/sustainability reports, annual reports, prospectuses, and government market filings.
2. Official company websites, official news, recruiting pages, and official social accounts.
3. Company-maintained 104/1111 pages.
4. Dated, role-specific employee submissions with editorial controls, only as corroboration.
5. Search snippets, aggregators, and anonymous discussion only as leads.

Do not let a lower-level source silently override a higher-level source. Explain scope or timing differences.

Record the evidence subject, entity scope, beneficiary, source tier, supported gates, effective period, and verification date. Source tiers 4–5 can corroborate or provide leads but cannot be the sole direct hard-gate evidence.

## Business-metric denominator and assurance controls

- State the numerator and denominator for every revenue, customer, market, or product percentage. `100% of product sales` is not `100% of total revenue` when product sales are only part of revenue.
- Keep reporting period, entity scope, currency, and units attached to the claim.
- Distinguish company sustainability-report assurance from greenhouse-gas verification, ISO certification, parent-company assurance, or another entity's report. Do not set report assurance to verified unless the candidate's own report is the assured subject.

## Female data

Capture female employee count/percentage and female manager count/percentage when disclosed. Record denominator, scope, report year, page, and evidence ID.

- Apply `員工女性為主` only with evidence that women exceed 50% of the relevant workforce.
- Preserve an official table's reported percentage and an independently computed percentage when rounding differs.
- Preserve official internal inconsistencies as a range or conflict; do not choose the convenient value.
- Keep female workforce and female management measures separate.

## Classification controls

Treat `公司立場`, `福利類別`, and match tags as analyst classifications. Explain the public facts that justify them. Do not write them as if the company used those labels.

Before writeback, obtain exact option spellings from Notion. Historically sensitive labels include:

- `願意做員工活動的公司`
- `員工多為中壯年為主`
- `員工女性為主`
- `無ESG報告書`

Never substitute shortened variants without confirming the live schema.
