# Notion writeback protocol

## Enter writeback only from an approved v2 package

Require all of the following:

- lifecycle `APPROVED_FOR_WRITEBACK`;
- current-run `authorization.writeback_approved: true`;
- exact authorized stock codes, decisions, and actions;
- a reviewed preview manifest and matching package SHA-256;
- successful `--mode writeback` validation.

Pilot-method approval and batch-expansion approval do not authorize mutation. Old logs, pages, and approvals never carry forward.

## Refresh live Notion state

Immediately before mutation:

1. Find both current target databases/data sources by title.
2. Fetch both schemas, property types, and option labels.
3. Read `notion://docs/enhanced-markdown-spec` completely.
4. Normalize each schema and store its hash, fetch date, title, and current data-source ID.
5. Compare the 13 logical properties with both live schemas.
6. Rebuild the keyed option-label snapshot.

Do not hard-code old data-source IDs, views, property types, or option labels. Stop if a logical field is missing or materially changed; do not create or coerce properties silently.

## Logical company properties

Require these 13 fields:

1. `公司名稱`
2. `公司立場`
3. `地區`
4. `資本額`
5. `人數`
6. `出版次數`
7. `報告書認證`
8. `基本資訊`
9. `福利類別`
10. `符合什麼條件？`
11. `公益 / 機率加分`
12. `什麼時候追進度`
13. `註記`

Keep numbers numeric. Use exact live select/multi-select spellings. Put assurance provider, standard, scope, and caveats in the page body or notes; do not invent a new select value.

## Route by current market

- Send listed and OTC companies to `listed_otc`.
- Send emerging companies to `emerging`.
- Do not pre-classify a company as listed merely because it has applied for listing.

## Deduplicate both data sources

For every company, query both data sources using:

- exact legal name;
- exact stock code.

Save query strings, check time, both data-source keys, hit counts, matching page IDs, normalized comparison, and one resolution:

- `CREATE`
- `SKIP`
- `CONFLICT`
- `UPDATE_REQUIRES_AUTH`

A view, workspace search, exported list, or before/after row count is not a complete duplicate check. Treat code match/name difference as possible rename; treat name match/different code as conflict. Never create a second page merely because the first is in another view or target.

## Enforce authorization and package identity

Generate the run-scoped Markdown, CSV, and manifest with `build_writeback_preview.py`. Before mutation, compare the canonical package SHA-256 with `source_package_sha256` in that manifest and run:

```bash
python3 scripts/validate_candidate_package.py candidate-package.json \
  --mode writeback \
  --expected-sha256 <reviewed hash>
```

If the package changed, stop, regenerate previews, and re-review material changes.

Default to PASS plus CREATE only. Require exact current authorization for REVIEW or UPDATE. Never write REJECT unless the user explicitly requests a separate audit/rejection destination.

## Create the page and contacts

- Use the current data source as parent.
- Populate all 13 properties from canonical validated values.
- Write the detailed evidence-backed page body from `research-profile.md`.
- Preserve null/unknown distinctions in prose; never turn unknown into `無`.

Create an inline contact database under the company page with exactly:

- `名稱` — TITLE
- `聯絡電話` — PHONE_NUMBER
- `轉接` — NUMBER
- `電子郵件` — EMAIL

Add the best public ESG/sustainability route first, then governance/IR, then switchboard/general contact. Omit private data and all complaint/whistleblowing/privacy/ethics contacts.

## Read back after each write

Fetch the company page and contact data source immediately. Save an intended-versus-actual comparison covering:

- all 13 property names, types, and values;
- exact select/multi-select labels;
- decision, employee basis, female data, contacts, evidence URLs, unknowns, and caveats in the body;
- inline contact schema and every contact row.

Classify the record `VERIFIED`, `PARTIAL`, or `FAILED`. Stop the batch on the first PARTIAL or FAILED result. Repair only the affected record and read it back again before continuing.

## Writeback receipt

Append a run-specific local receipt containing:

- run ID, package hash, rule/as-of versions, authorization source, and timestamp;
- target titles and current data-source IDs;
- per-company action, decision, page ID/URL, contact data-source ID, and contact row IDs;
- dedup queries and resolution;
- intended-versus-actual diff and verification result;
- created, updated, skipped, partial, failed, and deleted counts.

Record deletions as zero unless explicitly authorized and actually performed. A successful prior receipt is audit history, not future authorization.
