---
name: taiwan-esg-research
compat: [codex]
description: Research, screen, verify, pilot, approve, and prepare or execute audited Notion writeback for Taiwan listed, OTC, and emerging-market ESG partnership candidates. Use when Codex must apply current Notion-first market rules, build an official universe, distinguish PASS/REVIEW/REJECT, resolve applicant-versus-group employee counts, interpret three-festival welfare evidence, preserve female/workforce and ESG data, deduplicate both target databases, or create and read back company pages and inline public-business contact databases.
---

# Research Taiwan ESG Candidates

## Goal

Produce audit-ready candidate profiles without converting missing evidence into rejection or invention. Keep research, approval, and live Notion mutation as distinct states.

## Load the required guidance

- Read [references/run-lifecycle.md](references/run-lifecycle.md) before starting, resuming, approving, or superseding a run.
- Read [references/screening-rules.md](references/screening-rules.md) before screening or changing a decision.
- Read [references/research-profile.md](references/research-profile.md) before researching companies or building a package.
- Read [references/notion-writeback.md](references/notion-writeback.md) before any Notion query or mutation.
- Run `scripts/self_test.py` after changing this skill package.

## Execute the workflow

### 1. Start an isolated run

- Assign a unique `run_id`, `as_of`, timezone, scope, rule version, and lifecycle state.
- Separate rule/schema authority, company-fact authority, and mutation authority.
- Treat old packages, reports, previews, logs, page IDs, and approvals as historical audit material only.
- Store new artifacts outside read-only source directories.

### 2. Freeze the current rules

- Include current listed, OTC, and emerging companies.
- Apply 40–99 employees to listed/OTC only.
- Apply at least 50 employees with no upper limit to emerging companies. Never reject an emerging company because it exceeds 99 employees.
- Apply capital, ESG, and welfare gates by market exactly as defined in `screening-rules.md`.
- Keep the hard-gate decision separate from business value, welfare tier, and outreach potential.
- Treat missing, stale, ambiguous, or unresolved evidence as REVIEW, not REJECT.

### 3. Build or reconcile the universe

- Use current TWSE/TPEx/MOPS sources for market status, code, legal name, capital, and filings.
- Use the TPEx emerging-company universe, not recruitment sites, as the emerging master list.
- Save official source URLs, fetch dates, counts, pagination status, exclusions, and unmatched records in the universe manifest.
- Preserve delisted, public-only, private/unlisted, and unmatched entities in an audit list instead of silently dropping them.

### 4. Run Stage A

- Apply only current market status, capital, and employee-count gates.
- Record every meaningful employee observation separately, including entity scope, measure, effective period, retrieval date, evidence, eligibility, and derivation.
- Select one gate observation with an explicit rationale; never use group headcount to reject the Taiwan applicant entity.
- Do not propagate a scope label from one document or period to another without a direct bridge.
- Preserve unknown employee values as unresolved, never zero.

### 5. Run Stage B

- Verify every welfare gate independently with applicant-scoped employee evidence.
- Interpret `三節禮盒`, generic `節日禮盒`, slash wording, and explicit cash-and-box wording using `screening-rules.md`.
- Research industry, products, revenue/customer mix with explicit denominators, ESG reports and assurance, sex/age composition, training, supply chain,公益 activity, organization, and public business contacts.
- Separate source facts from analyst classifications such as company stance, welfare tier, and fit tags; attach rationale and evidence IDs.
- Record unknowns and actionable follow-up questions.

### 6. Produce and review a pilot

- Complete three end-to-end profiles before expanding a new workflow unless the user explicitly chooses another size.
- Include a useful mix of PASS and high-value REVIEW cases; never upgrade a decision to fill the sample.
- Present gate evidence, employee observations, female data, contacts, caveats, and intended Notion values at review depth.
- Record pilot-method approval separately from batch-expansion and writeback approval.

### 7. Validate and preview

Run research validation and create run-scoped review artifacts:

```bash
python3 scripts/validate_candidate_package.py candidate-package.json --mode research
python3 scripts/build_writeback_preview.py candidate-package.json --output-dir preview
```

Use package version 2 for all new work. Version 1 remains preview-only for historical compatibility.

Fix errors before presenting a batch. Carry warnings into human review; do not use them as permission to infer missing facts.

### 8. Obtain exact mutation authorization

- Record the current approval source and time, approved rule/as-of versions, exact stock codes, allowed decisions, and allowed actions.
- Default to PASS plus CREATE only.
- Require explicit authorization for REVIEW, UPDATE, or any company outside the reviewed scope.
- Do not infer authorization from prior writes, old logs, unchecked checklists, or existing pages.

### 9. Write to Notion safely

- Re-fetch both target schemas and exact option labels immediately before mutation.
- Read Notion enhanced Markdown guidance before authoring page content.
- Search both target data sources by exact legal name and stock code; record queries, hits, page IDs, and resolution.
- Use the preview manifest hash for final validation:

```bash
python3 scripts/validate_candidate_package.py candidate-package.json \
  --mode writeback \
  --expected-sha256 <source_package_sha256_from_preview_manifest>
```

- Route listed/OTC companies to the listed/OTC target and emerging companies to the emerging target.
- Prefer create-only behavior. Stop before overwriting an existing record without explicit UPDATE authorization.
- Create all 13 logical properties, an evidence-backed page body, and the inline public-business contact database.
- Read back every page and contact row immediately. Compare intended versus actual values, types, option labels, content, evidence links, and contact schema.
- Stop the batch on the first PARTIAL or FAILED readback and repair only the affected record.

## Stop conditions

Stop and ask for direction when:

- live Notion schema conflicts materially with the approved rules;
- a write would exceed current exact authorization;
- name/code deduplication finds a rename, conflict, or existing page without UPDATE permission;
- a contact is personal, non-public, or intended for complaints, privacy, ethics, harassment, or whistleblowing;
- a decisive source is inaccessible and the result would otherwise require guessing.

Do not stop merely because evidence is incomplete. Finish the package as REVIEW with explicit gaps.

## Required handoff

Report:

- run ID, as-of date, rule version, lifecycle, and approval scopes;
- universe coverage and reconciliation when applicable;
- counts by market and PASS/REVIEW/REJECT;
- every unresolved gate and actionable follow-up;
- employee observation selection, female-data availability, and official inconsistencies;
- contact coverage and missing ESG-specific routes;
- duplicate checks and target routing;
- Notion created/updated/skipped/failed counts and readback results;
- paths to the canonical package, preview manifest, previews, evidence, and writeback log.
