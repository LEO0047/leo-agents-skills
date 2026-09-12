#!/usr/bin/env python3
"""Build run-scoped Markdown/CSV previews from a validated candidate package."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import sys
from pathlib import Path

from validate_candidate_package import (
    EXPECTED_NOTION_FIELDS,
    NOTION_OPTION_FIELDS,
    validate_package,
)


FIELD_ORDER = [
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
]


def cell(value: object) -> str:
    if value is None:
        return "未揭露"
    if isinstance(value, list):
        return "、".join(str(item) for item in value)
    return str(value)


def authorization_view(data: dict) -> tuple[bool, set[str], set[str], set[str]]:
    if data.get("version") == 2:
        authorization = data.get("authorization", {})
        return (
            authorization.get("writeback_approved") is True,
            {str(item) for item in authorization.get("authorized_stock_codes", [])},
            set(authorization.get("allowed_decisions", ["PASS"])),
            set(authorization.get("allowed_actions", ["CREATE"])),
        )
    return (
        data.get("writeback_authorized") is True,
        {str(item) for item in data.get("authorized_stock_codes", [])},
        set(data.get("allowed_decisions", ["PASS"])),
        {"CREATE"},
    )


def notion_preflight_ready(data: dict) -> bool:
    if data.get("version") != 2:
        return False
    targets = data.get("notion_targets")
    options = data.get("notion_option_labels")
    if not isinstance(targets, dict) or not isinstance(options, dict):
        return False
    if not NOTION_OPTION_FIELDS.issubset(options):
        return False
    for field in NOTION_OPTION_FIELDS:
        if not isinstance(options.get(field), list):
            return False
    for key in ("listed_otc", "emerging"):
        target = targets.get(key)
        if not isinstance(target, dict):
            return False
        if any(
            not target.get(field)
            for field in ("title", "data_source_id", "schema_fetched_at", "schema_hash", "properties")
        ):
            return False
        if target.get("schema_fetched_at") != data.get("as_of"):
            return False
        properties = target.get("properties")
        if not isinstance(properties, dict) or not EXPECTED_NOTION_FIELDS.issubset(properties):
            return False
    return True


def writeback_ready(profile: dict, data: dict) -> tuple[bool, str]:
    approved, codes, decisions, actions = authorization_view(data)
    code = str(profile.get("stock_code", ""))
    lifecycle = data.get("lifecycle_status")
    action = profile.get("writeback_action", "SKIP")
    if lifecycle == "SUPERSEDED_DO_NOT_WRITE":
        return False, "歷史／已取代，禁止回填"
    if not approved:
        return False, "尚未取得本次明確寫入授權"
    if lifecycle != "APPROVED_FOR_WRITEBACK":
        return False, "生命週期尚未核准回填"
    if not notion_preflight_ready(data):
        return False, "Notion schema／選項尚未以本次 as-of 完整驗證"
    if code not in codes:
        return False, "不在本次核准股票代號範圍"
    if profile.get("decision") not in decisions:
        return False, "判定不在核准範圍"
    if action not in actions:
        return False, "動作不在核准範圍"
    dedup = profile.get("dedup") or {}
    if action == "CREATE" and (
        dedup.get("legal_name_hits") != 0 or dedup.get("stock_code_hits") != 0
    ):
        return False, "去重結果不允許 CREATE"
    if action == "CREATE" and dedup.get("resolution") != "CREATE":
        return False, "去重結論不是 CREATE"
    if action == "UPDATE" and dedup.get("resolution") != "UPDATE_REQUIRES_AUTH":
        return False, "去重結論不允許 UPDATE"
    return True, "已通過預覽層檢查；仍須執行 writeback mode 驗證"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace previews only within the same run after deliberate regeneration",
    )
    args = parser.parse_args()

    try:
        package_bytes = args.package.read_bytes()
        data = json.loads(package_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read package: {exc}", file=sys.stderr)
        return 2

    report = validate_package(data, mode="research")
    if report.errors:
        for item in report.errors:
            print(f"ERROR {item}", file=sys.stderr)
        print("Preview not created because validation failed.", file=sys.stderr)
        return 1

    run_id = str(data.get("run_id") or "legacy-v1")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / f"{run_id}-notion-writeback-preview.csv"
    md_path = args.output_dir / f"{run_id}-candidate-review.md"
    manifest_path = args.output_dir / f"{run_id}-preview-manifest.json"
    outputs = (csv_path, md_path, manifest_path)
    existing = [path for path in outputs if path.exists()]
    if existing and not args.overwrite:
        print(
            "ERROR: preview already exists; use a new run_id or --overwrite for deliberate same-run regeneration: "
            + ", ".join(str(path) for path in existing),
            file=sys.stderr,
        )
        return 1

    approved, authorized_codes, allowed_decisions, allowed_actions = authorization_view(data)
    lifecycle = data.get("lifecycle_status", "LEGACY_V1_PREVIEW_ONLY")
    schema_verified = notion_preflight_ready(data)

    csv_fields = [
        "執行批次",
        "生命週期",
        "股票代號",
        "市場",
        "目標資料庫",
        "判定",
        "預定動作",
        "本次核准",
        "可否回填",
        "阻擋／說明",
        *FIELD_ORDER,
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=csv_fields)
        writer.writeheader()
        for profile in data["profiles"]:
            ready, reason = writeback_ready(profile, data)
            code = str(profile["stock_code"])
            fields = profile["notion_fields"]
            writer.writerow(
                {
                    "執行批次": run_id,
                    "生命週期": lifecycle,
                    "股票代號": code,
                    "市場": profile["market"],
                    "目標資料庫": profile.get("target_database_key", "未指定"),
                    "判定": profile["decision"],
                    "預定動作": profile.get("writeback_action", "SKIP"),
                    "本次核准": "是" if approved and code in authorized_codes else "否",
                    "可否回填": "是" if ready else "否",
                    "阻擋／說明": reason,
                    **{key: cell(fields[key]) for key in FIELD_ORDER},
                }
            )

    superseded = lifecycle == "SUPERSEDED_DO_NOT_WRITE"
    lines = [
        f"# Taiwan ESG candidate review — {run_id}",
        "",
        f"> 狀態：{'歷史產物，禁止回填' if superseded else lifecycle}。這是預覽，不是 Notion 寫入結果。",
        "",
        f"- As of: {data['as_of']}",
        f"- Rule version: {data['rule_version']}",
        f"- Run scope: {data.get('run_scope', 'legacy-v1')}",
        f"- Writeback approved: {approved}",
        f"- Authorized stock codes: {', '.join(sorted(authorized_codes)) or 'none'}",
        f"- Allowed decisions: {', '.join(sorted(allowed_decisions)) or 'none'}",
        f"- Allowed actions: {', '.join(sorted(allowed_actions)) or 'none'}",
        f"- Notion schema/options verified for this as-of: {schema_verified}",
        f"- Profiles: {len(data['profiles'])}",
        "",
    ]
    for profile in data["profiles"]:
        ready, reason = writeback_ready(profile, data)
        metrics = profile.get("metrics", {})
        selected = metrics.get("selected_employee_observation_id", "legacy-single-value")
        lines.extend(
            [
                f"## {profile['legal_name']}（{profile['stock_code']}）",
                "",
                f"- 市場／判定：{profile['market']}／{profile['decision']}",
                f"- 目標／動作：{profile.get('target_database_key', '未指定')}／{profile.get('writeback_action', 'SKIP')}",
                f"- 可否回填：{'是' if ready else '否'} — {reason}",
                f"- 判定原因：{profile.get('decision_reason', '未填')}",
                f"- 員工口徑：{cell(metrics.get('employee_count'))} 人；{cell(metrics.get('employee_scope'))}；{cell(metrics.get('employee_measure'))}；{cell(metrics.get('employee_reference_date'))}",
                f"- 選用員工觀測：{selected}；{cell(metrics.get('employee_selection_reason'))}",
                f"- 女性員工：{cell(profile['workforce']['female_employees'].get('reported_pct'))}%（狀態：{profile['workforce']['female_employees'].get('status')}）",
                f"- 聯絡資料筆數：{len(profile.get('contacts', []))}",
                "",
                "### Gate check",
                "",
            ]
        )
        for gate in profile["gates"]:
            lines.append(f"- {gate['gate']}: {gate['status']} — {gate['result']}")
        lines.extend(["", "### Notion properties", ""])
        for key in FIELD_ORDER:
            lines.append(f"- {key}: {cell(profile['notion_fields'][key])}")
        lines.extend(["", "### Contacts", ""])
        for contact in profile.get("contacts", []):
            lines.append(
                f"- {cell(contact.get('name'))}／{cell(contact.get('role'))}／{cell(contact.get('phone'))}／{cell(contact.get('email'))}／可開發：{contact.get('outreach_allowed', False)}"
            )
        lines.extend(["", "### Open questions", ""])
        for question in profile.get("open_questions", []):
            lines.append(f"- {question}")
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    manifest = {
        "run_id": run_id,
        "lifecycle_status": lifecycle,
        "source_package": str(args.package.resolve()),
        "source_package_sha256": hashlib.sha256(package_bytes).hexdigest(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "writeback_approved": approved,
        "notion_schema_verified": schema_verified,
        "authorized_stock_codes": sorted(authorized_codes),
        "outputs": [str(path.resolve()) for path in (md_path, csv_path)],
        "validation_warnings": report.warnings,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Created {md_path}")
    print(f"Created {csv_path}")
    print(f"Created {manifest_path}")
    if report.warnings:
        print(f"Warnings carried into review: {len(report.warnings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
