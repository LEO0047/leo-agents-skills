#!/usr/bin/env python3
"""Regression tests for the Taiwan ESG skill package."""

from __future__ import annotations

from copy import deepcopy
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from validate_candidate_package import EXPECTED_NOTION_FIELDS, validate_package


AS_OF = "2026-08-05"


def evidence(
    evidence_id: str,
    gate: str,
    *,
    beneficiary: str = "NOT_APPLICABLE",
    claim_codes: list[str] | None = None,
) -> dict:
    return {
        "id": evidence_id,
        "fields": [gate],
        "source_type": "official test fixture",
        "source_title": f"fixture {gate}",
        "source_url": f"https://example.com/{evidence_id}",
        "subject_stock_code": "0000",
        "reference_period": AS_OF,
        "pdf_page": None,
        "printed_page": None,
        "excerpt": f"direct evidence for {gate}",
        "verified_at": AS_OF,
        "source_updated_at": None,
        "local_path": None,
        "confidence": "HIGH",
        "scope_note": "Taiwan applicant legal entity",
        "strength": "DIRECT",
        "source_tier": 1,
        "entity_scope_code": "APPLICANT_ENTITY",
        "beneficiary_scope": beneficiary,
        "supports": [gate],
        "claim_codes": claim_codes or [],
    }


def valid_package(*, approved: bool = False) -> dict:
    gate_specs = {
        "market_status": {},
        "employee_count": {},
        "capital": {},
        "festival_gift_box": {
            "beneficiary": "EMPLOYEES",
            "claim_codes": ["THREE_FESTIVAL_GIFT_BOXES_EXPLICIT"],
        },
        "festival_cash_bonus": {
            "beneficiary": "EMPLOYEES",
            "claim_codes": ["THREE_FESTIVAL_CASH_EXPLICIT"],
        },
        "funeral_support": {"beneficiary": "EMPLOYEES"},
        "parental_leave": {"beneficiary": "EMPLOYEES"},
        "labor_health_insurance": {"beneficiary": "EMPLOYEES"},
    }
    evidence_items = [
        evidence(f"0000-{index:02d}", gate, **kwargs)
        for index, (gate, kwargs) in enumerate(gate_specs.items(), start=1)
    ]
    evidence_by_gate = {
        item["supports"][0]: item["id"] for item in evidence_items
    }
    market_evidence = evidence_by_gate["market_status"]
    gates = [
        {
            "gate": gate,
            "status": "PASS",
            "result": "verified",
            "evidence_ids": [evidence_by_gate[gate]],
        }
        for gate in gate_specs
    ]
    fields = {key: "測試" for key in EXPECTED_NOTION_FIELDS}
    fields.update(
        {
            "公司名稱": "測試股份有限公司",
            "公司立場": "社會友善",
            "資本額": 100_000_000,
            "人數": 165,
            "出版次數": 0,
            "報告書認證": "無",
            "福利類別": ["水準之上"],
            "符合什麼條件？": [],
            "什麼時候追進度": None,
        }
    )
    unknown_female = {
        "status": "NOT_DISCLOSED",
        "count": None,
        "denominator": None,
        "reported_pct": None,
        "computed_pct": None,
        "scope": None,
        "reference_period": "2025",
        "evidence_ids": [],
        "note": "未揭露",
    }
    property_types = {key: "rich_text" for key in EXPECTED_NOTION_FIELDS}
    property_types["公司名稱"] = "title"
    property_types["資本額"] = "number"
    property_types["人數"] = "number"
    property_types["出版次數"] = "number"
    return {
        "version": 2,
        "run_id": "test-run-2026-08-05",
        "run_scope": "USER_SEEDED_CANDIDATES",
        "as_of": AS_OF,
        "rule_version": "notion-first-2026-08-05",
        "lifecycle_status": "APPROVED_FOR_WRITEBACK" if approved else "PILOT_REVIEW",
        "authorization": {
            "pilot_method_approved": approved,
            "batch_expansion_approved": False,
            "writeback_approved": approved,
            "approval_source": "current task user message" if approved else None,
            "approved_at": "2026-08-05T18:00:00+08:00" if approved else None,
            "approved_rule_version": "notion-first-2026-08-05" if approved else None,
            "approved_as_of": AS_OF if approved else None,
            "authorized_stock_codes": ["0000"] if approved else [],
            "allowed_decisions": ["PASS"],
            "allowed_actions": ["CREATE"],
        },
        "notion_option_labels": {
            "公司立場": ["中立", "社會友善", "低下"],
            "福利類別": ["水準之上", "基礎之下"],
            "符合什麼條件？": ["員工女性為主"],
            "報告書認證": ["有", "無"],
        },
        "notion_targets": {
            key: {
                "title": title,
                "data_source_id": f"test-{key}",
                "schema_fetched_at": AS_OF,
                "schema_hash": f"hash-{key}",
                "properties": deepcopy(property_types),
            }
            for key, title in (
                ("listed_otc", "尋找 ESG 目標公司"),
                ("emerging", "尋找興櫃目標公司"),
            )
        },
        "profiles": [
            {
                "stock_code": "0000",
                "legal_name": "測試股份有限公司",
                "short_name": "測試",
                "market": "興櫃",
                "target_database_key": "emerging",
                "decision": "PASS",
                "decision_code": "PASS",
                "decision_reason": "fixture",
                "writeback_action": "CREATE" if approved else "SKIP",
                "dedup": {
                    "checked_database_keys": ["listed_otc", "emerging"],
                    "checked_at": AS_OF,
                    "legal_name_query": "測試股份有限公司",
                    "stock_code_query": "0000",
                    "legal_name_hits": 0,
                    "stock_code_hits": 0,
                    "match_page_ids": [],
                    "resolution": "CREATE",
                },
                "metrics": {
                    "capital_twd": 100_000_000,
                    "employee_count": 165,
                    "employee_scope": "台灣申請法人",
                    "employee_scope_code": "APPLICANT_ENTITY",
                    "employee_measure": "當下",
                    "employee_measure_code": "CURRENT",
                    "employee_resolution_status": "RESOLVED",
                    "employee_reference_date": AS_OF,
                    "employee_evidence_ids": [evidence_by_gate["employee_count"]],
                    "employee_current_corrob_evidence_ids": [],
                    "selected_employee_observation_id": "emp-current",
                    "employee_selection_reason": "latest applicant-entity current count",
                    "employee_observations": [
                        {
                            "id": "emp-current",
                            "value": 165,
                            "scope": "台灣申請法人",
                            "scope_code": "APPLICANT_ENTITY",
                            "measure": "當下",
                            "measure_code": "CURRENT",
                            "reference_date": AS_OF,
                            "verified_at": AS_OF,
                            "evidence_ids": [evidence_by_gate["employee_count"]],
                            "eligible_for_gate": True,
                            "derivation": None,
                        }
                    ],
                },
                "gates": gates,
                "gate_followups": {},
                "notion_fields": fields,
                "analyst_classifications": {
                    "company_stance": {
                        "value": "社會友善",
                        "rationale": "fixture",
                        "evidence_ids": [market_evidence],
                    },
                    "welfare_categories": {
                        "value": ["水準之上"],
                        "rationale": "fixture",
                        "evidence_ids": [evidence_by_gate["festival_gift_box"]],
                    },
                    "fit_tags": {
                        "value": [],
                        "rationale": "no tags selected",
                        "evidence_ids": [market_evidence],
                    },
                },
                "company": {"revenue_claims": []},
                "workforce": {
                    "female_employees": deepcopy(unknown_female),
                    "female_managers": deepcopy(unknown_female),
                },
                "welfare": {},
                "esg": {
                    "report_count": 0,
                    "report_count_evidence_ids": [market_evidence],
                    "report_assurance": {
                        "status": "NONE_FOUND",
                        "notion_value": "無",
                        "evidence_ids": [market_evidence],
                        "note": "no company report assurance",
                    },
                },
                "organization": {},
                "contacts": [
                    {
                        "name": "公司總機",
                        "role": "總機",
                        "phone": "02-0000-0000",
                        "extension": None,
                        "email": None,
                        "website": "https://example.com",
                        "purpose": "general business",
                        "outreach_allowed": True,
                        "evidence_ids": [market_evidence],
                    }
                ],
                "outreach": {},
                "open_questions": [],
                "evidence": evidence_items,
            }
        ],
    }


def error_text(package: dict, *, mode: str = "research") -> str:
    return "\n".join(validate_package(package, mode=mode).errors)


class ValidatorTests(unittest.TestCase):
    def test_valid_emerging_package_has_no_upper_employee_limit(self) -> None:
        result = validate_package(valid_package())
        self.assertEqual(result.errors, [])

    def test_research_can_defer_notion_snapshots_without_fabrication(self) -> None:
        package = valid_package()
        package["notion_targets"] = None
        package["notion_option_labels"] = None
        package["profiles"][0]["dedup"] = None
        result = validate_package(package, mode="research")
        self.assertEqual(result.errors, [])
        self.assertTrue(any("required before writeback" in item for item in result.warnings))
        self.assertTrue(any("dedup not recorded" in item for item in result.warnings))

    def test_writeback_requires_live_notion_snapshots(self) -> None:
        package = valid_package(approved=True)
        package["notion_targets"] = None
        package["notion_option_labels"] = None
        text = error_text(package, mode="writeback")
        self.assertIn("live target data-source snapshots", text)
        self.assertIn("option labels copied from the live Notion schema", text)

    def test_preview_blocks_approved_package_with_unverified_schema(self) -> None:
        package = valid_package(approved=True)
        package["notion_targets"] = None
        package["notion_option_labels"] = None
        with tempfile.TemporaryDirectory(prefix="esg-schema-preview-") as temp_dir:
            temp_path = Path(temp_dir)
            package_path = temp_path / "package.json"
            output_path = temp_path / "preview"
            package_path.write_text(json.dumps(package, ensure_ascii=False), encoding="utf-8")
            preview_script = Path(__file__).with_name("build_writeback_preview.py")
            result = subprocess.run(
                [sys.executable, str(preview_script), str(package_path), "--output-dir", str(output_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            csv_path = output_path / f"{package['run_id']}-notion-writeback-preview.csv"
            with csv_path.open(encoding="utf-8-sig", newline="") as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(row["可否回填"], "否")
            self.assertIn("schema", row["阻擋／說明"])

    def test_unknown_female_status_stays_distinct_from_not_disclosed(self) -> None:
        package = valid_package()
        metric = package["profiles"][0]["workforce"]["female_employees"]
        metric.update({"status": "UNKNOWN", "note": "not researched yet"})
        self.assertEqual(error_text(package), "")
        metric["reported_pct"] = 51
        self.assertIn("must keep count, denominator, and percentages null", error_text(package))

    def test_listed_same_count_fails_40_99_and_requires_esg_gate(self) -> None:
        package = valid_package()
        profile = package["profiles"][0]
        profile["market"] = "上市"
        profile["target_database_key"] = "listed_otc"
        text = error_text(package)
        self.assertIn("official_esg", text)
        self.assertIn("employee gate must be REJECT", text)

    def test_group_scope_cannot_pass_applicant_gate(self) -> None:
        package = valid_package()
        metrics = package["profiles"][0]["metrics"]
        metrics["employee_scope_code"] = "GROUP"
        metrics["employee_observations"][0]["scope_code"] = "GROUP"
        metrics["employee_observations"][0]["eligible_for_gate"] = True
        text = error_text(package)
        self.assertIn("group observation cannot be eligible", text)
        self.assertIn("scoped to the applicant", text)

    def test_generic_festival_box_cannot_pass(self) -> None:
        package = valid_package()
        item = next(
            item for item in package["profiles"][0]["evidence"]
            if "festival_gift_box" in item["supports"]
        )
        item["claim_codes"] = ["GENERIC_FESTIVAL_BOX"]
        self.assertIn("gift-box PASS requires", error_text(package))

    def test_ambiguous_cash_or_gift_cannot_pass_cash(self) -> None:
        package = valid_package()
        item = next(
            item for item in package["profiles"][0]["evidence"]
            if "festival_cash_bonus" in item["supports"]
        )
        item["claim_codes"] = ["AMBIGUOUS_CASH_OR_GIFT"]
        self.assertIn("cash PASS requires", error_text(package))

    def test_wrong_subject_and_customer_box_fail_direct_gate(self) -> None:
        package = valid_package()
        item = next(
            item for item in package["profiles"][0]["evidence"]
            if "festival_gift_box" in item["supports"]
        )
        item["subject_stock_code"] = "9999"
        item["beneficiary_scope"] = "CUSTOMERS"
        self.assertIn("applicant-scoped DIRECT evidence", error_text(package))

    def test_low_tier_anonymous_evidence_cannot_be_direct(self) -> None:
        package = valid_package()
        package["profiles"][0]["evidence"][0]["source_tier"] = 4
        text = error_text(package)
        self.assertIn("tiers 4-5 cannot be DIRECT", text)

    def test_review_cannot_hide_failed_capital_gate(self) -> None:
        package = valid_package()
        profile = package["profiles"][0]
        profile["decision"] = "REVIEW"
        profile["decision_code"] = "REVIEW_BOX_SCOPE"
        profile["metrics"]["capital_twd"] = 1_200_000_000
        profile["notion_fields"]["資本額"] = 1_200_000_000
        box_gate = next(g for g in profile["gates"] if g["gate"] == "festival_gift_box")
        box_gate["status"] = "REVIEW"
        box_gate["evidence_ids"] = []
        profile["gate_followups"] = {"festival_gift_box": "Ask for three distribution records"}
        self.assertIn("capital gate must be REJECT", error_text(package))

    def test_emerging_over_99_cannot_be_rejected_for_employee_count(self) -> None:
        package = valid_package()
        profile = package["profiles"][0]
        profile["decision"] = "REJECT"
        profile["decision_code"] = "REJECT_EMPLOYEE_COUNT"
        employee_gate = next(g for g in profile["gates"] if g["gate"] == "employee_count")
        employee_gate["status"] = "REJECT"
        self.assertIn("emerging has no upper limit", error_text(package))

    def test_notion_values_must_match_canonical_metrics(self) -> None:
        package = valid_package()
        fields = package["profiles"][0]["notion_fields"]
        fields["公司名稱"] = "另一家公司"
        fields["人數"] = 1
        fields["資本額"] = 9_900_000_000
        text = error_text(package)
        self.assertIn("must equal legal_name", text)
        self.assertIn("must equal metrics.employee_count", text)
        self.assertIn("must equal metrics.capital_twd", text)

    def test_future_date_is_invalid(self) -> None:
        package = valid_package()
        package["profiles"][0]["evidence"][0]["verified_at"] = "2026-08-06"
        self.assertIn("cannot be later", error_text(package))

    def test_female_percentage_and_evidence_are_validated(self) -> None:
        package = valid_package()
        metric = package["profiles"][0]["workforce"]["female_employees"]
        metric.update(
            {
                "status": "VERIFIED",
                "count": 200,
                "denominator": 100,
                "reported_pct": 200,
                "evidence_ids": [],
            }
        )
        text = error_text(package)
        self.assertIn("has no evidence IDs", text)
        self.assertIn("between 0 and 100", text)
        self.assertIn("cannot exceed denominator", text)

    def test_disguised_whistleblowing_contact_is_blocked(self) -> None:
        package = valid_package()
        package["profiles"][0]["contacts"][0]["email"] = "whistleblowing@example.com"
        self.assertIn("cannot be outreach-eligible", error_text(package))

    def test_revenue_claim_requires_explicit_denominator(self) -> None:
        package = valid_package()
        package["profiles"][0]["company"]["revenue_claims"] = [
            {
                "metric": "customer share",
                "value": "100%",
                "denominator": None,
                "period": "2025",
                "scope": "applicant entity",
                "evidence_ids": ["0000-01"],
            }
        ]
        self.assertIn("never omit the denominator", error_text(package))

    def test_report_assurance_cannot_exist_without_company_report(self) -> None:
        package = valid_package()
        assurance = package["profiles"][0]["esg"]["report_assurance"]
        assurance["status"] = "VERIFIED"
        assurance["notion_value"] = "有"
        package["profiles"][0]["notion_fields"]["報告書認證"] = "有"
        self.assertIn("zero reports", error_text(package))

    def test_review_gate_requires_actionable_followup(self) -> None:
        package = valid_package()
        profile = package["profiles"][0]
        profile["decision"] = "REVIEW"
        profile["decision_code"] = "REVIEW_BOX_SCOPE"
        box_gate = next(g for g in profile["gates"] if g["gate"] == "festival_gift_box")
        box_gate["status"] = "REVIEW"
        box_gate["evidence_ids"] = []
        self.assertIn("missing actionable follow-up", error_text(package))

    def test_writeback_authorization_is_exact_and_provenanced(self) -> None:
        package = valid_package(approved=True)
        self.assertEqual(validate_package(package, mode="writeback").errors, [])
        package["authorization"]["authorized_stock_codes"] = ["9999"]
        text = error_text(package, mode="writeback")
        self.assertIn("outside exact authorization scope", text)
        self.assertIn("authorized codes not present", text)

    def test_superseded_package_cannot_authorize_writeback(self) -> None:
        package = valid_package(approved=True)
        package["lifecycle_status"] = "SUPERSEDED_DO_NOT_WRITE"
        self.assertIn("superseded package", error_text(package, mode="writeback"))

    def test_preview_is_run_scoped_hashed_and_refuses_silent_overwrite(self) -> None:
        package = valid_package()
        with tempfile.TemporaryDirectory(prefix="esg-skill-test-") as temp_dir:
            temp_path = Path(temp_dir)
            package_path = temp_path / "package.json"
            output_path = temp_path / "preview"
            package_bytes = json.dumps(package, ensure_ascii=False).encode("utf-8")
            package_path.write_bytes(package_bytes)
            preview_script = Path(__file__).with_name("build_writeback_preview.py")
            first = subprocess.run(
                [sys.executable, str(preview_script), str(package_path), "--output-dir", str(output_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            run_id = package["run_id"]
            md_path = output_path / f"{run_id}-candidate-review.md"
            csv_path = output_path / f"{run_id}-notion-writeback-preview.csv"
            manifest_path = output_path / f"{run_id}-preview-manifest.json"
            self.assertTrue(md_path.is_file())
            self.assertTrue(csv_path.is_file())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["source_package_sha256"], hashlib.sha256(package_bytes).hexdigest())
            with csv_path.open(encoding="utf-8-sig", newline="") as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(row["可否回填"], "否")
            second = subprocess.run(
                [sys.executable, str(preview_script), str(package_path), "--output-dir", str(output_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(second.returncode, 0)

    def test_cli_writeback_requires_reviewed_package_hash(self) -> None:
        package = valid_package(approved=True)
        with tempfile.TemporaryDirectory(prefix="esg-skill-hash-") as temp_dir:
            package_path = Path(temp_dir) / "package.json"
            package_bytes = json.dumps(package, ensure_ascii=False).encode("utf-8")
            package_path.write_bytes(package_bytes)
            validator = Path(__file__).with_name("validate_candidate_package.py")
            without_hash = subprocess.run(
                [sys.executable, str(validator), str(package_path), "--mode", "writeback"],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(without_hash.returncode, 0)
            with_hash = subprocess.run(
                [
                    sys.executable,
                    str(validator),
                    str(package_path),
                    "--mode",
                    "writeback",
                    "--expected-sha256",
                    hashlib.sha256(package_bytes).hexdigest(),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(with_hash.returncode, 0, with_hash.stdout + with_hash.stderr)


if __name__ == "__main__":
    unittest.main()
