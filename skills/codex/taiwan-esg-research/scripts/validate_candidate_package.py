#!/usr/bin/env python3
"""Validate a Taiwan ESG candidate package before review or Notion writeback."""

from __future__ import annotations

import argparse
from datetime import date, datetime
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


EXPECTED_NOTION_FIELDS = {
    "公司名稱",
    "公司立場",
    "地區",
    "資本額",
    "人數",
    "出版次數",
    "報告書認證",
    "基本資訊",
    "福利類別",
    "符合什麼條件？",
    "公益 / 機率加分",
    "什麼時候追進度",
    "註記",
}

NOTION_OPTION_FIELDS = {
    "公司立場",
    "福利類別",
    "符合什麼條件？",
    "報告書認證",
}

COMMON_GATES = {
    "market_status",
    "employee_count",
    "capital",
    "festival_gift_box",
    "festival_cash_bonus",
    "funeral_support",
    "parental_leave",
    "labor_health_insurance",
}
ALLOWED_GATES = COMMON_GATES | {"official_esg"}

MARKET_ALIASES = {
    "上市": "listed",
    "listed": "listed",
    "上櫃": "otc",
    "otc": "otc",
    "興櫃": "emerging",
    "emerging": "emerging",
}
TARGET_BY_MARKET = {
    "listed": "listed_otc",
    "otc": "listed_otc",
    "emerging": "emerging",
}

DECISIONS = {"PASS", "REVIEW", "REJECT"}
GATE_STATUSES = {"PASS", "REVIEW", "REJECT"}
LIFECYCLE_STATUSES = {
    "DRAFT",
    "PILOT_REVIEW",
    "APPROVED_FOR_WRITEBACK",
    "SUPERSEDED_DO_NOT_WRITE",
}
RUN_SCOPES = {"OFFICIAL_UNIVERSE", "USER_SEEDED_CANDIDATES", "FOLLOWUP_EXISTING_RUN"}
WRITEBACK_ACTIONS = {"CREATE", "UPDATE", "SKIP"}
EVIDENCE_STRENGTHS = {"DIRECT", "CORROBORATING", "LEAD"}
ENTITY_SCOPE_CODES = {"APPLICANT_ENTITY", "GROUP", "THIRD_PARTY", "NOT_APPLICABLE", "UNKNOWN"}
BENEFICIARY_SCOPES = {
    "EMPLOYEES",
    "CUSTOMERS",
    "SHAREHOLDERS",
    "SUPPLIERS",
    "PUBLIC",
    "NOT_APPLICABLE",
    "UNKNOWN",
}
EMPLOYEE_SCOPE_CODES = {"APPLICANT_ENTITY", "GROUP", "UNKNOWN"}
EMPLOYEE_MEASURE_CODES = {"CURRENT", "PERIOD_END", "ANNUAL_AVERAGE", "UNKNOWN"}
EMPLOYEE_RESOLUTION_STATUSES = {"RESOLVED", "CONFLICT", "UNKNOWN"}
CLAIM_CODES = {
    "THREE_FESTIVAL_GIFT_BOXES_EXPLICIT",
    "THREE_SEPARATE_EMPLOYEE_BOX_DISTRIBUTIONS",
    "THREE_FESTIVAL_CASH_EXPLICIT",
    "CASH_AND_BOX_EXPLICIT",
    "GENERIC_FESTIVAL_BOX",
    "AMBIGUOUS_CASH_OR_GIFT",
}
GIFT_BOX_PASS_CLAIMS = {
    "THREE_FESTIVAL_GIFT_BOXES_EXPLICIT",
    "THREE_SEPARATE_EMPLOYEE_BOX_DISTRIBUTIONS",
    "CASH_AND_BOX_EXPLICIT",
}
CASH_PASS_CLAIMS = {
    "THREE_FESTIVAL_CASH_EXPLICIT",
    "CASH_AND_BOX_EXPLICIT",
}
WELFARE_GATES = {
    "festival_gift_box",
    "festival_cash_bonus",
    "funeral_support",
    "parental_leave",
    "labor_health_insurance",
}

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RUN_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
PROHIBITED_CONTACT_PURPOSES = {
    "whistleblowing",
    "complaint",
    "ethics",
    "grievance",
    "privacy",
    "harassment",
    "檢舉",
    "申訴",
    "道德",
    "隱私",
    "性騷擾",
}


class Reporter:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, where: str, message: str) -> None:
        self.errors.append(f"{where}: {message}")

    def warn(self, where: str, message: str) -> None:
        self.warnings.append(f"{where}: {message}")


def _parse_date(value: Any, where: str, report: Reporter) -> date | None:
    if not isinstance(value, str) or not DATE_PATTERN.match(value):
        report.error(where, "must use YYYY-MM-DD")
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        report.error(where, "must be a real calendar date")
        return None


def _parse_timestamp(value: Any, where: str, report: Reporter) -> datetime | None:
    if not isinstance(value, str) or not value:
        report.error(where, "must be a non-empty ISO-8601 timestamp")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        report.error(where, "must be a valid ISO-8601 timestamp")
        return None
    if parsed.tzinfo is None:
        report.error(where, "timestamp must include a timezone offset")
    return parsed


def _is_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _as_gate_map(gates: Any, where: str, report: Reporter) -> dict[str, dict[str, Any]]:
    if not isinstance(gates, list):
        report.error(where, "gates must be a list")
        return {}
    result: dict[str, dict[str, Any]] = {}
    for index, gate in enumerate(gates):
        item_where = f"{where}.gates[{index}]"
        if not isinstance(gate, dict):
            report.error(item_where, "gate must be an object")
            continue
        key = gate.get("gate")
        if not isinstance(key, str) or not key:
            report.error(item_where, "missing gate key")
            continue
        if key in result:
            report.error(item_where, f"duplicate gate {key}")
        if key not in ALLOWED_GATES:
            report.error(item_where, f"unknown hard-gate key {key}; keep soft assessments outside gates")
        result[key] = gate
    return result


def _validate_female_metric(
    metric: Any,
    label: str,
    evidence_ids: set[str],
    where: str,
    report: Reporter,
) -> tuple[str | None, float | None]:
    if not isinstance(metric, dict):
        report.error(where, f"{label} must be an object")
        return None, None
    status = metric.get("status")
    if status not in {"VERIFIED", "NOT_DISCLOSED", "UNKNOWN", "CONFLICT"}:
        report.error(
            where,
            f"{label}.status must be VERIFIED, NOT_DISCLOSED, UNKNOWN, or CONFLICT",
        )
    refs = metric.get("evidence_ids", [])
    if not isinstance(refs, list):
        report.error(where, f"{label}.evidence_ids must be a list")
        refs = []
    unknown_refs = sorted(set(refs) - evidence_ids)
    if unknown_refs:
        report.error(where, f"{label} cites unknown evidence IDs: {unknown_refs}")
    reported = metric.get("reported_pct")
    computed = metric.get("computed_pct")
    if status == "VERIFIED" and reported is None and computed is None:
        report.error(where, f"{label} is VERIFIED but has no percentage")
    if status == "VERIFIED" and not refs:
        report.error(where, f"{label} is VERIFIED but has no evidence IDs")
    if status == "CONFLICT" and not metric.get("note"):
        report.error(where, f"{label} conflict must preserve the range/inconsistency in note")
    if status == "CONFLICT" and not refs:
        report.error(where, f"{label} conflict must cite evidence IDs")
    if status in {"UNKNOWN", "NOT_DISCLOSED"} and not metric.get("note"):
        report.error(where, f"{label} {status} requires an explanation in note")
    for field, value in (("reported_pct", reported), ("computed_pct", computed)):
        if value is not None and (not _is_number(value) or not 0 <= value <= 100):
            report.error(where, f"{label}.{field} must be between 0 and 100")
    count = metric.get("count")
    denominator = metric.get("denominator")
    if status in {"UNKNOWN", "NOT_DISCLOSED"} and any(
        value is not None for value in (count, denominator, reported, computed)
    ):
        report.error(
            where,
            f"{label} {status} must keep count, denominator, and percentages null",
        )
    if count is not None and (not _is_number(count) or count < 0):
        report.error(where, f"{label}.count must be a non-negative number or null")
    if denominator is not None and (not _is_number(denominator) or denominator <= 0):
        report.error(where, f"{label}.denominator must be positive or null")
    if _is_number(count) and _is_number(denominator) and count > denominator:
        report.error(where, f"{label}.count cannot exceed denominator")
    pct = reported if _is_number(reported) else computed
    return status, float(pct) if _is_number(pct) else None


def _validate_option_labels(
    value: Any,
    is_v2: bool,
    mode: str,
    report: Reporter,
) -> dict[str, list[str]]:
    if is_v2:
        if value is None:
            if mode == "writeback":
                report.error(
                    "package.notion_option_labels",
                    "writeback mode requires option labels copied from the live Notion schema",
                )
            else:
                report.warn(
                    "package.notion_option_labels",
                    "not captured yet; required before writeback",
                )
            return {}
        if not isinstance(value, dict):
            report.error(
                "package.notion_option_labels",
                "v2 requires a field-to-options object copied from the live Notion schema",
            )
            return {}
        missing = sorted(NOTION_OPTION_FIELDS - set(value))
        if missing:
            report.error("package.notion_option_labels", f"missing option fields: {missing}")
        result: dict[str, list[str]] = {}
        for field, options in value.items():
            if not isinstance(options, list) or not all(isinstance(item, str) and item for item in options):
                report.error("package.notion_option_labels", f"{field} options must be non-empty strings")
                continue
            result[field] = options
        return result

    if value is None:
        report.warn("package", "notion_option_labels missing; re-fetch live Notion schema before writeback")
        return {}
    if not isinstance(value, list):
        report.error("package.notion_option_labels", "v1 expects a fit-tag option list")
        return {}
    return {"符合什麼條件？": value}


def _validate_notion_targets(value: Any, mode: str, as_of: Any, report: Reporter) -> None:
    if value is None:
        if mode == "writeback":
            report.error("package.notion_targets", "writeback mode requires live target data-source snapshots")
        else:
            report.warn("package.notion_targets", "not captured yet; required before writeback")
        return
    if not isinstance(value, dict):
        report.error("package.notion_targets", "must be an object")
        return
    for key in ("listed_otc", "emerging"):
        target = value.get(key)
        where = f"package.notion_targets.{key}"
        if not isinstance(target, dict):
            report.error(where, "target is required")
            continue
        for field in ("title", "data_source_id", "schema_fetched_at", "schema_hash", "properties"):
            if not target.get(field):
                report.error(where, f"{field} is required")
        if target.get("schema_fetched_at"):
            _parse_date(target["schema_fetched_at"], f"{where}.schema_fetched_at", report)
            if mode == "writeback" and target["schema_fetched_at"] != as_of:
                report.error(where, "writeback requires a schema snapshot fetched on package.as_of")
        properties = target.get("properties")
        if isinstance(properties, dict):
            missing = sorted(EXPECTED_NOTION_FIELDS - set(properties))
            if missing:
                report.error(where, f"schema snapshot missing logical properties: {missing}")
            invalid = sorted(key for key, value in properties.items() if not isinstance(value, str) or not value)
            if invalid:
                report.error(where, f"property types must be non-empty strings: {invalid}")


def _validate_universe_manifest(data: dict[str, Any], is_v2: bool, report: Reporter) -> None:
    if not is_v2:
        return
    run_id = data.get("run_id")
    if not isinstance(run_id, str) or not RUN_ID_PATTERN.match(run_id):
        report.error("package.run_id", "use 3-80 lowercase letters/digits plus ._- only")
    run_scope = data.get("run_scope")
    if run_scope not in RUN_SCOPES:
        report.error("package.run_scope", f"must be one of {sorted(RUN_SCOPES)}")
        return
    if run_scope == "FOLLOWUP_EXISTING_RUN" and not data.get("parent_run_id"):
        report.error("package.parent_run_id", "follow-up runs must identify the parent run")
    if run_scope != "OFFICIAL_UNIVERSE":
        return
    manifest = data.get("universe_manifest")
    if not isinstance(manifest, dict):
        report.error("package.universe_manifest", "official-universe runs require a manifest")
        return
    if manifest.get("pagination_complete") is not True:
        report.error("package.universe_manifest", "pagination_complete must be true")
    for key in ("exclusions_path", "unmatched_path"):
        if not manifest.get(key):
            report.error("package.universe_manifest", f"{key} is required")
    sources = manifest.get("sources")
    counts = manifest.get("counts")
    if not isinstance(sources, dict) or not isinstance(counts, dict):
        report.error("package.universe_manifest", "sources and counts objects are required")
        return
    for market in ("listed", "otc", "emerging"):
        source = sources.get(market)
        if not isinstance(source, dict) or not str(source.get("url", "")).startswith(("https://", "http://")):
            report.error("package.universe_manifest", f"{market} requires an official HTTP(S) source URL")
        elif source.get("fetched_at"):
            _parse_date(source["fetched_at"], f"package.universe_manifest.sources.{market}.fetched_at", report)
        else:
            report.error("package.universe_manifest", f"{market}.fetched_at is required")
        count = counts.get(market)
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            report.error("package.universe_manifest", f"{market} count must be a non-negative integer")


def _read_authorization(
    data: dict[str, Any],
    is_v2: bool,
    mode: str,
    report: Reporter,
) -> tuple[bool, list[str], list[str], set[str]]:
    if not is_v2:
        writeback = data.get("writeback_authorized")
        if not isinstance(writeback, bool):
            report.error("package.writeback_authorized", "must be boolean")
            writeback = False
        decisions = data.get("allowed_decisions", ["PASS"])
        if not isinstance(decisions, list) or not set(decisions) <= DECISIONS:
            report.error("package.allowed_decisions", "must contain only PASS/REVIEW/REJECT")
            decisions = []
        codes = data.get("authorized_stock_codes", [])
        codes = [str(item).strip() for item in codes] if isinstance(codes, list) else []
        return writeback, codes, decisions, {"CREATE"}

    authorization = data.get("authorization")
    if not isinstance(authorization, dict):
        report.error("package.authorization", "v2 requires separate pilot, expansion, and writeback authorization")
        return False, [], [], set()
    for key in ("pilot_method_approved", "batch_expansion_approved", "writeback_approved"):
        if not isinstance(authorization.get(key), bool):
            report.error("package.authorization", f"{key} must be boolean")
    writeback = authorization.get("writeback_approved") is True
    codes = authorization.get("authorized_stock_codes", [])
    if not isinstance(codes, list):
        report.error("package.authorization", "authorized_stock_codes must be a list")
        codes = []
    codes = [str(item).strip() for item in codes]
    decisions = authorization.get("allowed_decisions", ["PASS"])
    if not isinstance(decisions, list) or not set(decisions) <= DECISIONS:
        report.error("package.authorization", "allowed_decisions must contain only PASS/REVIEW/REJECT")
        decisions = []
    actions = authorization.get("allowed_actions", ["CREATE"])
    if not isinstance(actions, list) or not set(actions) <= {"CREATE", "UPDATE"}:
        report.error("package.authorization", "allowed_actions may contain only CREATE/UPDATE")
        actions = []
    if writeback:
        if not codes:
            report.error("package.authorization", "writeback approval requires exact stock codes")
        if not authorization.get("approval_source"):
            report.error("package.authorization", "approval_source is required; old logs are not authorization")
        _parse_timestamp(authorization.get("approved_at"), "package.authorization.approved_at", report)
        if authorization.get("approved_rule_version") != data.get("rule_version"):
            report.error("package.authorization", "approved_rule_version must equal package.rule_version")
        if authorization.get("approved_as_of") != data.get("as_of"):
            report.error("package.authorization", "approved_as_of must equal package.as_of")
    if mode == "writeback" and not writeback:
        report.error("package.authorization", "writeback mode requires current explicit writeback approval")
    return writeback, codes, decisions, set(actions)


def _validate_dedup(
    profile: dict[str, Any],
    mode: str,
    where: str,
    report: Reporter,
) -> dict[str, Any]:
    dedup = profile.get("dedup")
    if not isinstance(dedup, dict):
        if mode == "writeback":
            report.error(where, "writeback mode requires a dedup object")
        else:
            report.warn(where, "dedup not recorded; exact code/name search across both targets is required")
        return {}
    checked = dedup.get("checked_database_keys")
    if not isinstance(checked, list) or set(checked) != {"listed_otc", "emerging"}:
        report.error(where, "dedup.checked_database_keys must contain listed_otc and emerging")
    _parse_date(dedup.get("checked_at"), f"{where}.dedup.checked_at", report)
    for key in ("legal_name_hits", "stock_code_hits"):
        value = dedup.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            report.error(where, f"dedup.{key} must be a non-negative integer")
    if dedup.get("legal_name_query") != profile.get("legal_name"):
        report.error(where, "dedup.legal_name_query must use the exact legal_name")
    if str(dedup.get("stock_code_query", "")) != str(profile.get("stock_code", "")):
        report.error(where, "dedup.stock_code_query must use the exact stock code")
    if not isinstance(dedup.get("match_page_ids"), list):
        report.error(where, "dedup.match_page_ids must be a list")
    if dedup.get("resolution") not in {"CREATE", "SKIP", "CONFLICT", "UPDATE_REQUIRES_AUTH"}:
        report.error(where, "dedup.resolution must be CREATE/SKIP/CONFLICT/UPDATE_REQUIRES_AUTH")
    return dedup


def validate_package(data: Any, mode: str = "research") -> Reporter:
    report = Reporter()
    if mode not in {"research", "writeback"}:
        report.error("package", "mode must be research or writeback")
        return report
    if not isinstance(data, dict):
        report.error("package", "top level must be an object")
        return report

    version = data.get("version")
    if version not in {1, 2}:
        report.error("package.version", "must be 1 or 2")
    is_v2 = version == 2
    if version == 1:
        report.warn("package.version", "v1 is preview-only; migrate to v2 before live writeback")
        if mode == "writeback":
            report.error("package.version", "live writeback requires v2")

    if not isinstance(data.get("rule_version"), str) or not data.get("rule_version", "").strip():
        report.error("package.rule_version", "non-empty rule version is required")

    as_of_date = _parse_date(data.get("as_of"), "package.as_of", report)

    _validate_universe_manifest(data, is_v2, report)
    writeback_authorized, authorized_codes, allowed_decisions, allowed_actions = _read_authorization(
        data, is_v2, mode, report
    )

    lifecycle = data.get("lifecycle_status")
    if is_v2 and lifecycle not in LIFECYCLE_STATUSES:
        report.error(
            "package.lifecycle_status",
            f"must be one of {sorted(LIFECYCLE_STATUSES)}",
        )
    if lifecycle == "SUPERSEDED_DO_NOT_WRITE" and writeback_authorized:
        report.error("package", "a superseded package can never authorize writeback")
    if writeback_authorized and lifecycle != "APPROVED_FOR_WRITEBACK":
        report.error("package", "writeback_authorized requires APPROVED_FOR_WRITEBACK lifecycle")
    if is_v2 and lifecycle == "APPROVED_FOR_WRITEBACK" and not writeback_authorized:
        report.error("package", "APPROVED_FOR_WRITEBACK requires current explicit writeback approval")

    option_labels = _validate_option_labels(
        data.get("notion_option_labels"), is_v2, mode, report
    )
    if is_v2:
        _validate_notion_targets(data.get("notion_targets"), mode, data.get("as_of"), report)

    profiles = data.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        report.error("package.profiles", "must be a non-empty list")
        return report

    seen_codes: set[str] = set()
    seen_names: set[str] = set()
    profile_by_code: dict[str, dict[str, Any]] = {}

    for index, profile in enumerate(profiles):
        where = f"profiles[{index}]"
        if not isinstance(profile, dict):
            report.error(where, "profile must be an object")
            continue

        code = str(profile.get("stock_code", "")).strip()
        name = str(profile.get("legal_name", "")).strip()
        if not code:
            report.error(where, "stock_code is required")
        elif code in seen_codes:
            report.error(where, f"duplicate stock_code {code}")
        seen_codes.add(code)
        profile_by_code[code] = profile
        if not name:
            report.error(where, "legal_name is required")
        elif name in seen_names:
            report.error(where, f"duplicate legal_name {name}")
        seen_names.add(name)
        if is_v2 and not str(profile.get("short_name", "")).strip():
            report.error(where, "short_name is required")

        raw_market = profile.get("market")
        market = MARKET_ALIASES.get(str(raw_market).lower())
        if not market:
            report.error(where, "market must be 上市/listed, 上櫃/otc, or 興櫃/emerging")

        decision = profile.get("decision")
        if decision not in DECISIONS:
            report.error(where, "decision must be PASS, REVIEW, or REJECT")
        if not profile.get("decision_code") or not profile.get("decision_reason"):
            report.error(where, "decision_code and decision_reason are required")
        if is_v2:
            for section in ("company", "welfare", "esg", "organization", "outreach"):
                if not isinstance(profile.get(section), dict):
                    report.error(where, f"{section} must be an object")
            if not isinstance(profile.get("open_questions"), list):
                report.error(where, "open_questions must be a list")

        target_key = profile.get("target_database_key")
        expected_target = TARGET_BY_MARKET.get(market or "")
        if is_v2 and target_key != expected_target:
            report.error(where, f"target_database_key must be {expected_target!r} for market {raw_market!r}")

        action = profile.get("writeback_action", "SKIP")
        if is_v2 and action not in WRITEBACK_ACTIONS:
            report.error(where, f"writeback_action must be one of {sorted(WRITEBACK_ACTIONS)}")
        dedup = _validate_dedup(profile, mode, where, report) if is_v2 else {}
        if is_v2 and mode == "writeback" and dedup.get("checked_at") != data.get("as_of"):
            report.error(where, "writeback dedup must be performed on package.as_of")

        evidence = profile.get("evidence")
        evidence_ids: set[str] = set()
        evidence_map: dict[str, dict[str, Any]] = {}
        if not isinstance(evidence, list) or not evidence:
            report.error(where, "evidence must be a non-empty list")
            evidence = []
        for e_index, item in enumerate(evidence):
            e_where = f"{where}.evidence[{e_index}]"
            if not isinstance(item, dict):
                report.error(e_where, "evidence item must be an object")
                continue
            required = {"id", "fields", "source_type", "source_title", "source_url", "verified_at"}
            missing = sorted(key for key in required if not item.get(key))
            if missing:
                report.error(e_where, f"missing required values: {missing}")
            evidence_id = str(item.get("id", ""))
            if evidence_id in evidence_ids:
                report.error(e_where, f"duplicate evidence ID {evidence_id}")
            evidence_ids.add(evidence_id)
            evidence_map[evidence_id] = item
            url = item.get("source_url")
            if url and not str(url).startswith(("https://", "http://")):
                report.error(e_where, "source_url must be an HTTP(S) URL")
            verified_date = _parse_date(item.get("verified_at"), f"{e_where}.verified_at", report)
            if as_of_date and verified_date and verified_date > as_of_date:
                report.error(e_where, "verified_at cannot be later than package.as_of")

            if is_v2:
                required_values = {
                    "subject_stock_code",
                    "reference_period",
                    "excerpt",
                    "confidence",
                    "scope_note",
                    "strength",
                    "source_tier",
                    "entity_scope_code",
                    "beneficiary_scope",
                    "supports",
                }
                missing_values = sorted(key for key in required_values if item.get(key) in (None, "", []))
                if missing_values:
                    report.error(e_where, f"v2 missing required evidence values: {missing_values}")
                for key in (
                    "pdf_page",
                    "printed_page",
                    "local_path",
                    "claim_codes",
                    "source_updated_at",
                ):
                    if key not in item:
                        report.error(e_where, f"v2 requires key {key}; use null/[] when not applicable")
                if item.get("strength") not in EVIDENCE_STRENGTHS:
                    report.error(e_where, f"strength must be one of {sorted(EVIDENCE_STRENGTHS)}")
                source_tier = item.get("source_tier")
                if not isinstance(source_tier, int) or isinstance(source_tier, bool) or not 1 <= source_tier <= 5:
                    report.error(e_where, "source_tier must be an integer from 1 (official filing/report) to 5 (lead only)")
                if item.get("strength") == "DIRECT" and isinstance(source_tier, int) and source_tier > 3:
                    report.error(e_where, "source tiers 4-5 cannot be DIRECT hard-gate evidence")
                if item.get("entity_scope_code") not in ENTITY_SCOPE_CODES:
                    report.error(e_where, f"entity_scope_code must be one of {sorted(ENTITY_SCOPE_CODES)}")
                if item.get("beneficiary_scope") not in BENEFICIARY_SCOPES:
                    report.error(e_where, f"beneficiary_scope must be one of {sorted(BENEFICIARY_SCOPES)}")
                if not isinstance(item.get("fields"), list) or not item.get("fields"):
                    report.error(e_where, "fields must be a non-empty list")
                if item.get("confidence") not in {"HIGH", "MEDIUM", "LOW"}:
                    report.error(e_where, "confidence must be HIGH, MEDIUM, or LOW")
                source_updated_at = item.get("source_updated_at")
                if source_updated_at is not None:
                    updated_date = _parse_date(source_updated_at, f"{e_where}.source_updated_at", report)
                    if verified_date and updated_date and updated_date > verified_date:
                        report.error(e_where, "source_updated_at cannot be later than verified_at")
                supports = item.get("supports", [])
                if not isinstance(supports, list):
                    report.error(e_where, "supports must be a list")
                claim_codes = item.get("claim_codes", [])
                if not isinstance(claim_codes, list):
                    report.error(e_where, "claim_codes must be a list")
                else:
                    unknown_claims = sorted(set(claim_codes) - CLAIM_CODES)
                    if unknown_claims:
                        report.error(e_where, f"unknown claim codes: {unknown_claims}")

        gate_map = _as_gate_map(profile.get("gates"), where, report)
        required_gates = set(COMMON_GATES)
        if market in {"listed", "otc"}:
            required_gates.add("official_esg")
        missing_gates = sorted(required_gates - set(gate_map))
        if missing_gates:
            report.error(where, f"missing gates: {missing_gates}")

        required_statuses: list[str] = []
        for key, gate in gate_map.items():
            g_where = f"{where}.gates.{key}"
            status = gate.get("status")
            if status not in GATE_STATUSES:
                report.error(g_where, "status must be PASS, REVIEW, or REJECT")
                continue
            if key in required_gates:
                required_statuses.append(status)
            refs = gate.get("evidence_ids", [])
            if not isinstance(refs, list):
                report.error(g_where, "evidence_ids must be a list")
                refs = []
            if status in {"PASS", "REJECT"} and not refs:
                report.error(g_where, f"{status} gate requires direct evidence")
            unknown_refs = sorted(set(refs) - evidence_ids)
            if unknown_refs:
                report.error(g_where, f"cites unknown evidence IDs: {unknown_refs}")
            if not gate.get("result"):
                report.error(g_where, "result is required")
            elif str(gate.get("result")).strip().upper() == status:
                report.warn(g_where, "result should explain the evidence, not repeat the status")

            if is_v2 and status in {"PASS", "REJECT"} and refs:
                direct_items = [
                    evidence_map[ref]
                    for ref in refs
                    if ref in evidence_map
                    and evidence_map[ref].get("strength") == "DIRECT"
                    and evidence_map[ref].get("source_tier") in {1, 2, 3}
                    and str(evidence_map[ref].get("subject_stock_code")) == code
                    and evidence_map[ref].get("entity_scope_code") == "APPLICANT_ENTITY"
                    and (
                        key not in WELFARE_GATES
                        or evidence_map[ref].get("beneficiary_scope") == "EMPLOYEES"
                    )
                    and key in evidence_map[ref].get("supports", [])
                ]
                if not direct_items:
                    report.error(
                        g_where,
                        f"{status} requires applicant-scoped DIRECT evidence whose supports includes this gate",
                    )
                if status == "PASS" and key == "festival_gift_box" and not any(
                    set(item.get("claim_codes", [])) & GIFT_BOX_PASS_CLAIMS for item in direct_items
                ):
                    report.error(
                        g_where,
                        "gift-box PASS requires explicit three-festival boxes, three separate employee distributions, or explicit cash-and-box wording",
                    )
                if status == "PASS" and key == "festival_cash_bonus" and not any(
                    set(item.get("claim_codes", [])) & CASH_PASS_CLAIMS for item in direct_items
                ):
                    report.error(
                        g_where,
                        "cash PASS requires explicit three-festival cash or explicit cash-and-box wording",
                    )

        if decision == "PASS" and any(status != "PASS" for status in required_statuses):
            report.error(where, "PASS decision requires every applicable hard gate to PASS")
        if decision == "REVIEW" and "REJECT" in required_statuses:
            report.error(where, "REVIEW decision cannot contain a directly failed hard gate")
        if decision == "REVIEW" and "REVIEW" not in required_statuses:
            report.error(where, "REVIEW decision requires at least one REVIEW hard gate")
        if decision == "REJECT" and "REJECT" not in required_statuses:
            report.error(where, "REJECT decision requires at least one REJECT hard gate")
        if is_v2:
            gate_followups = profile.get("gate_followups")
            if not isinstance(gate_followups, dict):
                report.error(where, "gate_followups must be an object keyed by REVIEW gate")
                gate_followups = {}
            review_keys = {
                key for key in required_gates if gate_map.get(key, {}).get("status") == "REVIEW"
            }
            missing_followups = sorted(
                key for key in review_keys if not isinstance(gate_followups.get(key), str) or not gate_followups[key].strip()
            )
            if missing_followups:
                report.error(where, f"missing actionable follow-up questions for REVIEW gates: {missing_followups}")
            extra_followups = sorted(set(gate_followups) - review_keys)
            if extra_followups:
                report.warn(where, f"gate_followups contains non-REVIEW gates: {extra_followups}")

        metrics = profile.get("metrics")
        if not isinstance(metrics, dict):
            report.error(where, "metrics must be an object")
            metrics = {}
        capital = metrics.get("capital_twd")
        employee_count = metrics.get("employee_count")
        if capital is not None and (
            not isinstance(capital, int) or isinstance(capital, bool) or capital < 0
        ):
            report.error(where, "capital_twd must be a non-negative integer or null")
        if employee_count is not None and (
            not isinstance(employee_count, int) or isinstance(employee_count, bool) or employee_count < 0
        ):
            report.error(where, "employee_count must be a non-negative integer or null")
        for key in ("employee_scope", "employee_measure", "employee_reference_date"):
            if employee_count is not None and not metrics.get(key):
                report.error(where, f"metrics.{key} required when employee_count is known")

        employee_refs = metrics.get("employee_evidence_ids", [])
        if not isinstance(employee_refs, list):
            report.error(where, "metrics.employee_evidence_ids must be a list")
            employee_refs = []
        if employee_count is not None and not employee_refs:
            report.error(where, "known employee_count requires employee_evidence_ids")
        unknown_employee_refs = sorted(set(employee_refs) - evidence_ids)
        if unknown_employee_refs:
            report.error(where, f"metrics cites unknown employee evidence IDs: {unknown_employee_refs}")
        gate_employee_refs = set(gate_map.get("employee_count", {}).get("evidence_ids", []))
        if employee_refs and gate_employee_refs and not set(employee_refs) & gate_employee_refs:
            report.error(where, "employee metric and employee gate must share at least one evidence ID")

        if is_v2:
            scope_code = metrics.get("employee_scope_code")
            measure_code = metrics.get("employee_measure_code")
            resolution_status = metrics.get("employee_resolution_status")
            if scope_code not in EMPLOYEE_SCOPE_CODES:
                report.error(where, f"employee_scope_code must be one of {sorted(EMPLOYEE_SCOPE_CODES)}")
            if measure_code not in EMPLOYEE_MEASURE_CODES:
                report.error(where, f"employee_measure_code must be one of {sorted(EMPLOYEE_MEASURE_CODES)}")
            if resolution_status not in EMPLOYEE_RESOLUTION_STATUSES:
                report.error(
                    where,
                    f"employee_resolution_status must be one of {sorted(EMPLOYEE_RESOLUTION_STATUSES)}",
                )
            current_refs = metrics.get("employee_current_corrob_evidence_ids", [])
            if not isinstance(current_refs, list):
                report.error(where, "employee_current_corrob_evidence_ids must be a list")
                current_refs = []
            unknown_current_refs = sorted(set(current_refs) - evidence_ids)
            if unknown_current_refs:
                report.error(where, f"current employee corroboration cites unknown IDs: {unknown_current_refs}")
            if decision == "PASS" and scope_code != "APPLICANT_ENTITY":
                report.error(where, "PASS employee count must be scoped to the applicant legal entity")
            if decision == "PASS" and resolution_status != "RESOLVED":
                report.error(where, "PASS employee count requires RESOLVED employee observations")
            if decision == "PASS" and measure_code == "ANNUAL_AVERAGE" and not current_refs:
                report.error(where, "annual-average PASS requires dated current applicant-entity corroboration")

            observations = metrics.get("employee_observations")
            selected_id = metrics.get("selected_employee_observation_id")
            if not isinstance(observations, list) or not observations:
                report.error(where, "v2 requires non-empty employee_observations")
                observations = []
            observation_map: dict[str, dict[str, Any]] = {}
            for o_index, observation in enumerate(observations):
                o_where = f"{where}.metrics.employee_observations[{o_index}]"
                if not isinstance(observation, dict):
                    report.error(o_where, "observation must be an object")
                    continue
                observation_id = str(observation.get("id", "")).strip()
                if not observation_id:
                    report.error(o_where, "id is required")
                    continue
                if observation_id in observation_map:
                    report.error(o_where, f"duplicate observation ID {observation_id}")
                observation_map[observation_id] = observation
                if not _is_number(observation.get("value")) or observation.get("value") < 0:
                    report.error(o_where, "value must be a non-negative number")
                observation_scope = observation.get("scope_code")
                observation_measure = observation.get("measure_code")
                if observation_scope not in EMPLOYEE_SCOPE_CODES:
                    report.error(o_where, f"scope_code must be one of {sorted(EMPLOYEE_SCOPE_CODES)}")
                if observation_measure not in EMPLOYEE_MEASURE_CODES:
                    report.error(o_where, f"measure_code must be one of {sorted(EMPLOYEE_MEASURE_CODES)}")
                if not observation.get("scope") or not observation.get("measure"):
                    report.error(o_where, "scope and measure descriptions are required")
                if not observation.get("reference_date"):
                    report.error(o_where, "reference_date/reporting period is required")
                observation_verified = _parse_date(
                    observation.get("verified_at"), f"{o_where}.verified_at", report
                )
                if as_of_date and observation_verified and observation_verified > as_of_date:
                    report.error(o_where, "verified_at cannot be later than package.as_of")
                obs_refs = observation.get("evidence_ids", [])
                if not isinstance(obs_refs, list) or not obs_refs:
                    report.error(o_where, "evidence_ids must be a non-empty list")
                    obs_refs = []
                unknown_obs_refs = sorted(set(obs_refs) - evidence_ids)
                if unknown_obs_refs:
                    report.error(o_where, f"cites unknown evidence IDs: {unknown_obs_refs}")
                if not isinstance(observation.get("eligible_for_gate"), bool):
                    report.error(o_where, "eligible_for_gate must be boolean")
                if observation_scope == "GROUP" and observation.get("eligible_for_gate") is True:
                    report.error(o_where, "group observation cannot be eligible for applicant-entity gate")
                derivation = observation.get("derivation")
                if derivation is not None:
                    if not isinstance(derivation, dict) or not derivation.get("formula") or not derivation.get("basis"):
                        report.error(o_where, "derived observations require formula and basis")

            selected = observation_map.get(str(selected_id))
            if not selected:
                report.error(where, "selected_employee_observation_id must match an observation")
            else:
                if selected.get("value") != employee_count:
                    report.error(where, "selected employee observation value must equal employee_count")
                if selected.get("scope_code") != scope_code or selected.get("measure_code") != measure_code:
                    report.error(where, "selected observation scope/measure must match normalized metrics")
                if selected.get("eligible_for_gate") is not True:
                    report.error(where, "selected employee observation must be eligible_for_gate")
                if not set(selected.get("evidence_ids", [])) <= set(employee_refs):
                    report.error(where, "selected observation evidence must be included in employee_evidence_ids")
            if not metrics.get("employee_selection_reason"):
                report.error(where, "employee_selection_reason is required")

            for ref in current_refs:
                item = evidence_map.get(ref, {})
                if item.get("strength") not in {"DIRECT", "CORROBORATING"} or "employee_count" not in item.get("supports", []):
                    report.error(where, "current corroboration must support employee_count and not be LEAD-only")

        if decision == "PASS":
            if not _is_number(capital) or capital > 1_000_000_000:
                report.error(where, "PASS requires capital_twd <= 1,000,000,000")
            if not _is_number(employee_count):
                report.error(where, "PASS requires a numeric employee_count")
            elif market in {"listed", "otc"} and not 40 <= employee_count <= 99:
                report.error(where, "listed/OTC PASS requires 40-99 employees")
            elif market == "emerging" and employee_count < 50:
                report.error(where, "emerging PASS requires at least 50 employees; there is no upper limit")

        if is_v2 and _is_number(capital):
            expected_capital_status = "PASS" if capital <= 1_000_000_000 else "REJECT"
            if gate_map.get("capital", {}).get("status") != expected_capital_status:
                report.error(where, f"capital gate must be {expected_capital_status} for selected capital_twd")
        if is_v2 and _is_number(employee_count) and metrics.get("employee_scope_code") == "APPLICANT_ENTITY":
            employee_in_range = (
                40 <= employee_count <= 99
                if market in {"listed", "otc"}
                else employee_count >= 50
                if market == "emerging"
                else False
            )
            expected_employee_status = (
                "PASS" if employee_in_range else "REJECT"
            ) if metrics.get("employee_resolution_status") == "RESOLVED" else "REVIEW"
            if gate_map.get("employee_count", {}).get("status") != expected_employee_status:
                report.error(
                    where,
                    f"employee gate must be {expected_employee_status} for the selected applicant-entity count; emerging has no upper limit",
                )

        notion_fields = profile.get("notion_fields")
        if not isinstance(notion_fields, dict):
            report.error(where, "notion_fields must be an object")
            notion_fields = {}
        field_names = set(notion_fields)
        if field_names != EXPECTED_NOTION_FIELDS:
            report.error(
                where,
                f"notion_fields mismatch; missing={sorted(EXPECTED_NOTION_FIELDS-field_names)}, extra={sorted(field_names-EXPECTED_NOTION_FIELDS)}",
            )
        if is_v2:
            if notion_fields.get("公司名稱") != name:
                report.error(where, "Notion 公司名稱 must equal legal_name")
            if employee_count is not None and notion_fields.get("人數") != employee_count:
                report.error(where, "Notion 人數 must equal metrics.employee_count")
            if capital is not None and notion_fields.get("資本額") != capital:
                report.error(where, "Notion 資本額 must equal metrics.capital_twd")
            if not _is_number(notion_fields.get("出版次數")) or notion_fields.get("出版次數") < 0:
                report.error(where, "Notion 出版次數 must be a non-negative number")

        for field in ("福利類別", "符合什麼條件？"):
            value = notion_fields.get(field, [])
            if not isinstance(value, list):
                report.error(where, f"{field} must be a list")
                continue
            allowed = option_labels.get(field)
            if allowed is not None:
                unknown = sorted(set(value) - set(allowed))
                if unknown:
                    report.error(where, f"{field} values not present in captured Notion options: {unknown}")
        for field in ("公司立場", "報告書認證"):
            value = notion_fields.get(field)
            allowed = option_labels.get(field)
            if allowed is not None and value not in allowed:
                report.error(where, f"{field} value {value!r} is not present in captured Notion options")

        if is_v2:
            classifications = profile.get("analyst_classifications")
            if not isinstance(classifications, dict):
                report.error(where, "analyst_classifications must be an object")
                classifications = {}
            classification_contract = {
                "company_stance": notion_fields.get("公司立場"),
                "welfare_categories": notion_fields.get("福利類別"),
                "fit_tags": notion_fields.get("符合什麼條件？"),
            }
            for key, expected_value in classification_contract.items():
                claim = classifications.get(key)
                c_where = f"{where}.analyst_classifications.{key}"
                if not isinstance(claim, dict):
                    report.error(c_where, "classification object is required")
                    continue
                if claim.get("value") != expected_value:
                    report.error(c_where, "value must equal the corresponding Notion field")
                if not claim.get("rationale"):
                    report.error(c_where, "rationale is required")
                refs = claim.get("evidence_ids", [])
                if not isinstance(refs, list) or not refs:
                    report.error(c_where, "evidence_ids must be a non-empty list")
                elif set(refs) - evidence_ids:
                    report.error(c_where, f"cites unknown evidence IDs: {sorted(set(refs)-evidence_ids)}")

            esg_data = profile.get("esg", {})
            report_count = esg_data.get("report_count") if isinstance(esg_data, dict) else None
            if not isinstance(report_count, int) or isinstance(report_count, bool) or report_count < 0:
                report.error(where, "esg.report_count must be a non-negative integer")
            elif notion_fields.get("出版次數") != report_count:
                report.error(where, "Notion 出版次數 must equal esg.report_count")
            count_refs = esg_data.get("report_count_evidence_ids", []) if isinstance(esg_data, dict) else []
            if not isinstance(count_refs, list) or not count_refs:
                report.error(where, "esg.report_count_evidence_ids must be a non-empty list")
            elif set(count_refs) - evidence_ids:
                report.error(where, f"ESG report count cites unknown IDs: {sorted(set(count_refs)-evidence_ids)}")
            assurance = esg_data.get("report_assurance") if isinstance(esg_data, dict) else None
            if not isinstance(assurance, dict):
                report.error(where, "esg.report_assurance must be an object")
            else:
                assurance_status = assurance.get("status")
                if assurance_status not in {"VERIFIED", "NONE_FOUND", "UNKNOWN", "CONFLICT"}:
                    report.error(where, "report assurance status is invalid")
                if assurance.get("notion_value") != notion_fields.get("報告書認證"):
                    report.error(where, "report assurance notion_value must equal Notion 報告書認證")
                assurance_refs = assurance.get("evidence_ids", [])
                if assurance_status in {"VERIFIED", "NONE_FOUND", "CONFLICT"} and (
                    not isinstance(assurance_refs, list) or not assurance_refs
                ):
                    report.error(where, "report assurance conclusion requires evidence IDs")
                elif isinstance(assurance_refs, list) and set(assurance_refs) - evidence_ids:
                    report.error(where, f"report assurance cites unknown IDs: {sorted(set(assurance_refs)-evidence_ids)}")
                if assurance_status == "VERIFIED" and report_count == 0:
                    report.error(where, "report assurance cannot be VERIFIED when the company has zero reports")

            company_data = profile.get("company", {})
            revenue_claims = company_data.get("revenue_claims") if isinstance(company_data, dict) else None
            if not isinstance(revenue_claims, list):
                report.error(where, "company.revenue_claims must be a list; use [] when unavailable")
                revenue_claims = []
            for r_index, claim in enumerate(revenue_claims):
                r_where = f"{where}.company.revenue_claims[{r_index}]"
                if not isinstance(claim, dict):
                    report.error(r_where, "revenue claim must be an object")
                    continue
                for key in ("metric", "value", "denominator", "period", "scope", "evidence_ids"):
                    if claim.get(key) in (None, "", []):
                        report.error(r_where, f"{key} is required; never omit the denominator")
                refs = claim.get("evidence_ids", [])
                if isinstance(refs, list) and set(refs) - evidence_ids:
                    report.error(r_where, f"cites unknown evidence IDs: {sorted(set(refs)-evidence_ids)}")

        workforce = profile.get("workforce")
        if not isinstance(workforce, dict):
            report.error(where, "workforce must be an object")
            workforce = {}
        status, female_pct = _validate_female_metric(
            workforce.get("female_employees"), "female_employees", evidence_ids, where, report
        )
        _validate_female_metric(
            workforce.get("female_managers"), "female_managers", evidence_ids, where, report
        )
        tags = notion_fields.get("符合什麼條件？", [])
        tags = tags if isinstance(tags, list) else []
        female_tag = "員工女性為主" in tags
        if female_tag and (status != "VERIFIED" or female_pct is None or female_pct <= 50):
            report.error(where, "員工女性為主 requires verified female employee share above 50%")
        if status == "VERIFIED" and female_pct is not None and female_pct > 50 and not female_tag:
            report.warn(where, "verified female employee share exceeds 50% but 員工女性為主 is not selected")

        contacts = profile.get("contacts")
        if not isinstance(contacts, list) or not contacts:
            report.warn(where, "no public contact records supplied")
            contacts = []
        for c_index, contact in enumerate(contacts):
            c_where = f"{where}.contacts[{c_index}]"
            if not isinstance(contact, dict):
                report.error(c_where, "contact must be an object")
                continue
            if is_v2:
                for key in ("name", "role", "purpose", "outreach_allowed", "evidence_ids"):
                    if key not in contact:
                        report.error(c_where, f"v2 contact requires key {key}")
            contact_text = " ".join(
                str(contact.get(key, "")) for key in ("name", "role", "email", "website", "purpose")
            ).lower()
            if contact.get("outreach_allowed") is True and any(
                term in contact_text for term in PROHIBITED_CONTACT_PURPOSES
            ):
                report.error(c_where, "complaint/whistleblowing/privacy contact cannot be outreach-eligible")
            refs = contact.get("evidence_ids", [])
            if not isinstance(refs, list):
                report.error(c_where, "evidence_ids must be a list")
            elif set(refs) - evidence_ids:
                report.error(c_where, f"cites unknown evidence IDs: {sorted(set(refs)-evidence_ids)}")

        if is_v2:
            is_authorized = code in authorized_codes and writeback_authorized
            if is_authorized and decision not in allowed_decisions:
                report.error(where, f"authorized decision {decision} is outside allowed_decisions")
            if is_authorized and action == "SKIP":
                report.error(where, "authorized profile cannot use writeback_action SKIP")
            if not is_authorized and action != "SKIP" and mode == "writeback":
                report.error(where, "profile outside exact authorization scope must use SKIP")
            if action in {"CREATE", "UPDATE"} and action not in allowed_actions:
                report.error(where, f"{action} is outside the current authorization's allowed_actions")
            if action in {"CREATE", "UPDATE"} and dedup:
                name_hits = dedup.get("legal_name_hits")
                code_hits = dedup.get("stock_code_hits")
                if action == "CREATE" and (name_hits != 0 or code_hits != 0):
                    report.error(where, "CREATE requires zero legal-name and stock-code hits")
                if action == "CREATE" and dedup.get("resolution") != "CREATE":
                    report.error(where, "CREATE action requires dedup.resolution CREATE")
                if action == "UPDATE" and dedup.get("resolution") != "UPDATE_REQUIRES_AUTH":
                    report.error(where, "UPDATE action requires dedup.resolution UPDATE_REQUIRES_AUTH")

    unknown_authorized = sorted(set(authorized_codes) - set(profile_by_code))
    if unknown_authorized:
        report.error("package.authorization", f"authorized codes not present in profiles: {unknown_authorized}")

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path, help="Candidate package JSON")
    parser.add_argument(
        "--mode",
        choices=("research", "writeback"),
        default="research",
        help="Use writeback mode immediately before any live Notion mutation",
    )
    parser.add_argument(
        "--expected-sha256",
        help="Required in writeback mode; copy source_package_sha256 from the reviewed preview manifest",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable result")
    args = parser.parse_args()

    try:
        package_bytes = args.package.read_bytes()
        data = json.loads(package_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read package: {exc}", file=sys.stderr)
        return 2

    report = validate_package(data, mode=args.mode)
    actual_sha256 = hashlib.sha256(package_bytes).hexdigest()
    if args.mode == "writeback" and not args.expected_sha256:
        report.error("package", "writeback mode requires --expected-sha256 from the reviewed preview manifest")
    elif args.expected_sha256 and args.expected_sha256 != actual_sha256:
        report.error("package", "package SHA-256 differs from the reviewed preview manifest")
    result = {"valid": not report.errors, "errors": report.errors, "warnings": report.warnings}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for item in report.errors:
            print(f"ERROR {item}")
        for item in report.warnings:
            print(f"WARNING {item}")
        print(
            f"Result: {'VALID' if not report.errors else 'INVALID'}; "
            f"{len(report.errors)} error(s), {len(report.warnings)} warning(s)"
        )
    return 0 if not report.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
