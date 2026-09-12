# Research profile and candidate-package v2

## Use v2 for new work

Version 1 remains valid only for historical research previews. Use version 2 for every new run and all live writeback.

Represent unknown facts with `null` plus a status/explanation. Never use zero, `無`, an empty string, or a missing key to mean unknown.

## Top-level package

Store one canonical JSON object with:

- `version: 2`
- `run_id`
- `run_scope`: `OFFICIAL_UNIVERSE`, `USER_SEEDED_CANDIDATES`, or `FOLLOWUP_EXISTING_RUN`
- `parent_run_id` for a follow-up
- `as_of` in `YYYY-MM-DD`
- `rule_version`
- `lifecycle_status`
- `authorization`
- `notion_targets`
- `notion_option_labels`
- `universe_manifest` for an official-universe run
- `profiles`

In research mode, set `notion_targets` and `notion_option_labels` to `null` when live Notion access is unavailable. The validator will warn but can still validate the research package. Never invent a snapshot to silence that warning. Both fields must contain current live data before writeback validation.

### Authorization

Keep three approvals independent:

```json
{
  "pilot_method_approved": false,
  "batch_expansion_approved": false,
  "writeback_approved": false,
  "approval_source": null,
  "approved_at": null,
  "approved_rule_version": null,
  "approved_as_of": null,
  "authorized_stock_codes": [],
  "allowed_decisions": ["PASS"],
  "allowed_actions": ["CREATE"]
}
```

When writeback is approved, populate the source, timezone-aware timestamp, exact rule/as-of versions, stock codes, decisions, and actions from the current instruction. Do not self-declare authorization.

### Live Notion snapshot

Capture both logical targets, never fixed historical IDs:

```json
{
  "listed_otc": {
    "title": "live title",
    "data_source_id": "live data source id",
    "schema_fetched_at": "2026-08-05",
    "schema_hash": "sha256 of normalized schema",
    "properties": {"公司名稱": "title", "資本額": "number"}
  },
  "emerging": {
    "title": "live title",
    "data_source_id": "live data source id",
    "schema_fetched_at": "2026-08-05",
    "schema_hash": "sha256 of normalized schema",
    "properties": {"公司名稱": "title", "資本額": "number"}
  }
}
```

Store `notion_option_labels` as a field-to-options object for `公司立場`, `福利類別`, `符合什麼條件？`, and `報告書認證`.

Each target's `properties` object must copy the live property type for all 13 logical fields: `公司名稱`, `公司立場`, `地區`, `資本額`, `人數`, `出版次數`, `報告書認證`, `基本資訊`, `福利類別`, `符合什麼條件？`, `公益 / 機率加分`, `什麼時候追進度`, and `註記`. Do not guess the types. A partial snapshot is invalid; use `null` until it can be fetched in full.

### Universe manifest

For `OFFICIAL_UNIVERSE`, record:

- official listed, OTC, and emerging source URLs and fetch dates;
- counts by market;
- `pagination_complete: true` only after every page is reconciled;
- paths to exclusion and unmatched lists.

## Profile contract

Each profile must contain:

- `stock_code`, `legal_name`, `short_name`, `market`
- `target_database_key`: `listed_otc` or `emerging`
- `decision`, `decision_code`, `decision_reason`
- `writeback_action`: `CREATE`, `UPDATE`, or `SKIP`
- `dedup`
- `metrics`
- `gates` and `gate_followups`
- `notion_fields`
- `analyst_classifications`
- `company`, `workforce`, `welfare`, `esg`, `organization`
- `contacts`, `outreach`, `open_questions`, `evidence`

`notion_fields` always uses these value shapes; exact option spellings still come from the live schema:

```json
{
  "公司名稱": "股份有限公司",
  "公司立場": "single option string",
  "地區": "string or null",
  "資本額": 500000000,
  "人數": 78,
  "出版次數": 0,
  "報告書認證": "single option string",
  "基本資訊": "string or null",
  "福利類別": ["multi-select option"],
  "符合什麼條件？": ["multi-select option"],
  "公益 / 機率加分": "string or null",
  "什麼時候追進度": null,
  "註記": "string or null"
}
```

### Dedup manifest

Record both target searches:

```json
{
  "checked_database_keys": ["listed_otc", "emerging"],
  "checked_at": "2026-08-05",
  "legal_name_query": "exact legal name",
  "stock_code_query": "1234",
  "legal_name_hits": 0,
  "stock_code_hits": 0,
  "match_page_ids": [],
  "resolution": "CREATE"
}
```

Use `SKIP`, `CONFLICT`, or `UPDATE_REQUIRES_AUTH` when appropriate. View row counts and workspace search are not substitutes for data-source queries.

When Notion is unavailable during research, set `dedup` to `null`; research validation warns and the preview remains non-writable. Never enter fabricated zero-hit searches. A complete current exact-name/code search across both targets is mandatory before writeback.

## Employee observations

Keep normalized fields for Notion and a lossless observation list:

```json
{
  "capital_twd": 500000000,
  "employee_count": 78,
  "employee_scope": "台灣申請法人",
  "employee_scope_code": "APPLICANT_ENTITY",
  "employee_measure": "期末",
  "employee_measure_code": "PERIOD_END",
  "employee_resolution_status": "RESOLVED",
  "employee_reference_date": "2025-12-31",
  "employee_evidence_ids": ["1234-02"],
  "employee_current_corrob_evidence_ids": [],
  "selected_employee_observation_id": "emp-2025-parent",
  "employee_selection_reason": "newest applicant-entity period-end total",
  "employee_observations": [
    {
      "id": "emp-2025-parent",
      "value": 78,
      "scope": "台灣申請法人",
      "scope_code": "APPLICANT_ENTITY",
      "measure": "期末",
      "measure_code": "PERIOD_END",
      "reference_date": "2025-12-31",
      "verified_at": "2026-08-05",
      "evidence_ids": ["1234-02"],
      "eligible_for_gate": true,
      "derivation": null
    }
  ]
}
```

Use `GROUP` and `eligible_for_gate: false` for group observations. Use `CONFLICT` when comparable applicant observations cross a threshold. For a derived value, store `derivation.formula` and `derivation.basis`. An annual-average PASS requires dated current applicant-entity corroboration.

## Gates and follow-ups

Use stable hard-gate keys:

- `market_status`
- `employee_count`
- `capital`
- `official_esg` for listed/OTC only
- `festival_gift_box`
- `festival_cash_bonus`
- `funeral_support`
- `parental_leave`
- `labor_health_insurance`

Store `gates` as a list. Each item uses the exact key `gate`, a `status` of `PASS`, `REVIEW`, or `REJECT`, plus `result` and `evidence_ids`:

```json
{
  "gates": [
    {
      "gate": "employee_count",
      "status": "PASS",
      "result": "165 current applicant-entity employees",
      "evidence_ids": ["1234-02"]
    }
  ],
  "gate_followups": {}
}
```

PASS and REJECT require compatible direct evidence. For every REVIEW gate, add an actionable question to `gate_followups` keyed by the same gate name.

## Evidence records

Each v2 evidence item must include:

```json
{
  "id": "1234-02",
  "fields": ["employee_count"],
  "source_type": "official annual report",
  "source_title": "report title",
  "source_url": "https://example.com/report.pdf",
  "subject_stock_code": "1234",
  "reference_period": "2025-12-31",
  "pdf_page": 64,
  "printed_page": 62,
  "excerpt": "faithful short paraphrase",
  "verified_at": "2026-08-05",
  "source_updated_at": null,
  "local_path": "/absolute/path/report.pdf",
  "confidence": "HIGH",
  "scope_note": "applicant entity; period-end",
  "strength": "DIRECT",
  "source_tier": 1,
  "entity_scope_code": "APPLICANT_ENTITY",
  "beneficiary_scope": "NOT_APPLICABLE",
  "supports": ["employee_count"],
  "claim_codes": []
}
```

Use source tiers 1–5 from `screening-rules.md`. A direct hard-gate item must identify the candidate as subject, use applicant-entity scope, support the exact gate, and use employee beneficiary scope for welfare gates.

For festival evidence, use only these claim codes:

- `THREE_FESTIVAL_GIFT_BOXES_EXPLICIT`
- `THREE_SEPARATE_EMPLOYEE_BOX_DISTRIBUTIONS`
- `THREE_FESTIVAL_CASH_EXPLICIT`
- `CASH_AND_BOX_EXPLICIT`
- `GENERIC_FESTIVAL_BOX`
- `AMBIGUOUS_CASH_OR_GIFT`

Keep screenshots as support artifacts, not the only citation. Preserve the source URL and PDF/printed pages.

## Analyst classifications and business facts

Store `company_stance`, `welfare_categories`, and `fit_tags` under `analyst_classifications`. Each needs a value equal to the intended Notion field, a rationale, and evidence IDs.

Store revenue/customer/product shares as `company.revenue_claims[]` with:

- metric and value;
- explicit denominator;
- period and entity scope;
- evidence IDs.

Never convert `100% of sales` into `100% of total revenue` unless the denominators are identical.

## ESG report and assurance

Store:

- `esg.report_count` and the exact companion key `esg.report_count_evidence_ids`;
- `esg.report_assurance.status`: `VERIFIED`, `NONE_FOUND`, `UNKNOWN`, or `CONFLICT`;
- the live Notion value, provider/standard details, evidence IDs, and note.

Do not treat greenhouse-gas verification, ISO certification, parent assurance, or another entity's report as the candidate's report assurance.

Minimal shape:

```json
{
  "report_count": 0,
  "report_count_evidence_ids": ["1234-esg-search"],
  "report_assurance": {
    "status": "NONE_FOUND",
    "notion_value": "live option value",
    "provider": null,
    "standard": null,
    "evidence_ids": ["1234-esg-search"],
    "note": "company report and assurance search result"
  }
}
```

## Workforce and female data

For female employees and managers, store status, count, denominator, reported and computed percentages, scope, period, evidence IDs, and note. Allowed statuses are `VERIFIED`, `NOT_DISCLOSED`, `UNKNOWN`, and `CONFLICT`. `UNKNOWN` means not yet researched or inconclusive; `NOT_DISCLOSED` means relevant official sources were checked and the metric was not found. Keep all quantities null and explain the state for both; VERIFIED and CONFLICT require evidence. Use `CONFLICT` with the preserved range when official values disagree. Never mix female workforce and female management denominators.

Apply `員工女性為主` only when the relevant verified workforce share exceeds 50%.

## Contact records

Capture public business routes in this order:

1. sustainability/ESG team or report contact;
2. governance, corporate communications, or investor relations;
3. public switchboard/general corporate email.

Each contact needs name, role, phone, extension, email, website, purpose, `outreach_allowed`, and evidence IDs. State `ESG 專責聯絡未公開` when necessary. Never make complaint, whistleblowing, ethics, privacy, harassment, or grievance channels outreach-eligible.

## Detailed Notion page body

Include:

1. decision, code, as-of date, and decisive caveat;
2. public contacts near the top;
3. industry, products/services, and denominator-safe revenue/market claims;
4. employee observations and selection, female employees/managers, age mix, and conflicts;
5. gate-by-gate welfare evidence and analyst welfare tier;
6. report history, assurance, training, supply chain, and organization/foundation;
7.公益 evidence, fit analysis, outreach angle, and cautions;
8. official sources with dates/pages;
9. explicit unknowns and follow-up questions.

Make every meaningful label traceable to a fact or clearly identify it as an analyst inference.
