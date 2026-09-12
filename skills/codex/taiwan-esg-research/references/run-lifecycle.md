# Run lifecycle, authority, and artifact isolation

## Use three separate authority tracks

### Rule and schema authority

Apply, in order:

1. current live Notion configuration;
2. the user's latest explicit correction in the current task;
3. the latest operating specification approved for this run;
4. stakeholder transcript;
5. old handoffs, exports, previews, and reports.

Stop before writeback when live Notion and a current explicit correction materially conflict.

### Company-fact authority

Use the evidence hierarchy in `screening-rules.md`. Existing Notion rows are not automatically the best source for current market status, capital, headcount, welfare, report assurance, or contacts. Re-verify volatile facts.

### Mutation authority

Accept live write authorization only from an explicit instruction in the current run. An old writeback log, checked box, existing page, previous approval, or earlier successful write never authorizes a new mutation.

## Start an isolated run

Create a unique lowercase `run_id` and record:

- `as_of` date and timezone;
- `run_scope`: `OFFICIAL_UNIVERSE`, `USER_SEEDED_CANDIDATES`, or `FOLLOWUP_EXISTING_RUN`;
- rule version and instruction source;
- live Notion target/schema snapshots;
- conflicts and their resolution;
- parent run ID for a follow-up.

Keep source project files read-only. Store the new canonical package, previews, evidence, and writeback receipt under a run-specific working directory.

For an official-universe run, save a universe manifest containing official source URLs, fetch dates, market counts, pagination completeness, and paths to exclusion and unmatched lists. Recruitment sites do not prove universe completeness.

## Keep approvals independent

Record these separately:

1. `pilot_method_approved`: the research method and profile depth are accepted.
2. `batch_expansion_approved`: expansion beyond the pilot is accepted.
3. `writeback_approved`: exact Notion mutations are accepted.

For writeback approval, record the current instruction source, timestamp, approved rule version, approved as-of date, exact stock codes, allowed decisions, and allowed actions. Approval for two PASS companies does not approve other PASS companies, REVIEW records, updates, or a larger batch.

## Use explicit lifecycle states

- `DRAFT`: incomplete research.
- `PILOT_REVIEW`: ready for human review; no writeback.
- `APPROVED_FOR_WRITEBACK`: exact scoped mutations approved.
- `SUPERSEDED_DO_NOT_WRITE`: historical audit artifact only.

Only `APPROVED_FOR_WRITEBACK` may enter writeback validation. Mark every derived CSV, Markdown, JSON, or HTML artifact from an obsolete package as superseded, or regenerate it from the current canonical package.

## Bind preview and writeback

Generate run-scoped previews with `build_writeback_preview.py`. Preserve its manifest and package SHA-256. Immediately before mutation, run writeback-mode validation with that same hash. If the package changes after review, regenerate the preview and obtain approval for the changed scope when material.

Do not overwrite another run's preview. Use `--overwrite` only to deliberately regenerate outputs for the same run ID.

## Treat historical artifacts as audit evidence only

Old pilot files, screenshots, PDFs, URLs, page IDs, row counts, and writeback logs may provide leads. They do not establish current facts, current Notion schema, current deduplication, or current authorization.

Never copy fixed company decisions, contacts, target IDs, or old option labels into a new run without live verification.
