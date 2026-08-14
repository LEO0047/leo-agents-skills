#!/usr/bin/env python3
"""One-off TWSE endpoint probe. Downloads JSON metadata only; never downloads PDFs."""

from __future__ import annotations

import hashlib
import html as html_module
import json
import os
import platform
import re
import socket
import sys
import traceback
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import requests

OUT = Path("twse_probe_output")
OUT.mkdir(exist_ok=True)
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
)
SECURITY_TEXT = "安全性考量"
LISTED_URL = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
ESG_URL = "https://esggenplus.twse.com.tw/api/api/MopsSustainReport/data"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(name: str, obj: Any) -> dict[str, Any]:
    path = OUT / name
    raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    path.write_bytes(raw)
    return {
        "ok": True,
        "path": str(path),
        "bytes": len(raw),
        "sha256": sha256_bytes(raw),
        "records": len(obj) if isinstance(obj, (list, dict)) else None,
    }


def exact_probe(name: str, url: str, body: bytes | None = None) -> dict[str, Any]:
    """Run the user's urllib probe as closely as possible."""
    headers = {
        "User-Agent": UA,
        "Content-Type": "application/json",
    }
    result: dict[str, Any] = {"name": name, "url": url, "method": "POST" if body else "GET"}
    try:
        req = urllib.request.Request(url, data=body, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read()
            text = raw.decode("utf-8", "ignore")
            result.update(
                classification="被擋" if SECURITY_TEXT in text else "正常",
                http_status=getattr(response, "status", None),
                length=len(text),
                bytes=len(raw),
                content_type=response.headers.get("Content-Type", ""),
                contains_security_text=SECURITY_TEXT in text,
                sha256=sha256_bytes(raw),
                preview=re.sub(r"\s+", " ", text[:300]),
            )
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        text = raw.decode("utf-8", "ignore")
        result.update(
            classification="被擋" if SECURITY_TEXT in text else "錯誤",
            http_status=exc.code,
            length=len(text),
            bytes=len(raw),
            contains_security_text=SECURITY_TEXT in text,
            error=f"HTTPError {exc.code}: {exc.reason}",
            preview=re.sub(r"\s+", " ", text[:500]),
        )
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        result.update(classification="錯誤", error=f"{type(exc).__name__}: {exc}")
    print("PROBE", json.dumps(result, ensure_ascii=False))
    return result


def fetch_listed() -> dict[str, Any]:
    try:
        req = urllib.request.Request(LISTED_URL, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=90) as response:
            raw = response.read()
        data = json.loads(raw.decode("utf-8-sig"))
        if not isinstance(data, list) or not data:
            raise ValueError(f"Unexpected listed-company payload: {type(data).__name__}")
        meta = write_json("twse_listed.json", data)
        meta["source"] = LISTED_URL
        return meta
    except Exception as exc:  # noqa: BLE001
        traceback.print_exc()
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def clean_cell(fragment: str) -> str:
    fragment = re.sub(r"<[^>]+>", "", fragment)
    fragment = html_module.unescape(fragment).replace("\xa0", "").strip()
    return re.sub(r"\s+", " ", fragment)


def parse_employee_html(text: str) -> dict[str, int]:
    records: dict[str, int] = {}
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", text, re.S | re.I):
        cells = [
            clean_cell(cell)
            for cell in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S | re.I)
        ]
        if len(cells) >= 7 and re.fullmatch(r"\d{4}", cells[1] or ""):
            try:
                records[cells[1]] = int(float(cells[6].replace(",", "")))
            except ValueError:
                continue
    return records


def decode_response(response: requests.Response) -> str:
    # MOPS currently emits UTF-8; preserve a fallback for legacy pages.
    raw = response.content
    for encoding in ("utf-8", "utf-8-sig", response.apparent_encoding, "big5", "cp950"):
        if not encoding:
            continue
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", "ignore")


def fetch_employees() -> dict[str, Any]:
    combined: dict[str, int] = {}
    attempts: list[dict[str, Any]] = []
    base_payload = {
        "encodeURIComponent": "1",
        "step": "1",
        "firstin": "1",
        "off": "1",
        "RYEAR": "114",
    }
    hosts = ("mops.twse.com.tw", "mopsov.twse.com.tw")

    for market in ("sii", "otc"):
        market_records: dict[str, int] = {}
        for host in hosts:
            for include_code in (False, True):
                payload = dict(base_payload, TYPEK=market)
                if include_code:
                    payload["code"] = ""
                url = f"https://{host}/mops/web/ajax_t100sb14"
                headers = {
                    "User-Agent": UA,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Origin": f"https://{host}",
                    "Referer": f"https://{host}/mops/web/t100sb14",
                }
                try:
                    response = requests.post(
                        url,
                        data=payload,
                        headers=headers,
                        timeout=90,
                        allow_redirects=True,
                    )
                    text = decode_response(response)
                    parsed = parse_employee_html(text)
                    attempt = {
                        "market": market,
                        "url": url,
                        "include_code": include_code,
                        "http_status": response.status_code,
                        "length": len(text),
                        "contains_security_text": SECURITY_TEXT in text,
                        "parsed_records": len(parsed),
                        "preview": re.sub(r"\s+", " ", text[:240]),
                    }
                    attempts.append(attempt)
                    print("EMP_ATTEMPT", json.dumps(attempt, ensure_ascii=False))
                    if parsed:
                        market_records = parsed
                        break
                except Exception as exc:  # noqa: BLE001
                    attempt = {
                        "market": market,
                        "url": url,
                        "include_code": include_code,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                    attempts.append(attempt)
                    print("EMP_ATTEMPT", json.dumps(attempt, ensure_ascii=False))
            if market_records:
                break
        combined.update(market_records)

    if not combined:
        return {"ok": False, "error": "No employee rows parsed", "attempts": attempts}
    meta = write_json("twse_employees.json", combined)
    meta["attempts"] = attempts
    meta["markets_requested"] = ["sii", "otc"]
    return meta


def extract_esg_records(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    data = payload.get("data", [])
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("data", "items", "rows", "result"):
            nested = data.get(key)
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]
    return []


def get_antiforgery_session() -> tuple[requests.Session, str, dict[str, Any]]:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": UA,
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        }
    )
    home = session.get("https://esggenplus.twse.com.tw/", timeout=60)
    token_response = session.get(
        "https://esggenplus.twse.com.tw/api/api/Antiforgery/token",
        headers={
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://esggenplus.twse.com.tw/inquiry/report",
        },
        timeout=60,
    )
    token_response.raise_for_status()
    token_payload = token_response.json()
    token = token_payload.get("data", "") if isinstance(token_payload, dict) else ""
    if not isinstance(token, str) or len(token) < 20:
        raise ValueError(f"Unexpected antiforgery response: {str(token_payload)[:300]}")
    handshake = {
        "home_status": home.status_code,
        "home_length": len(home.text),
        "token_status": token_response.status_code,
        "token_length": len(token),
        "cookie_names": sorted(session.cookies.keys()),
    }
    return session, token, handshake


def fetch_esg() -> dict[str, Any]:
    all_records: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    session: requests.Session | None = None
    token = ""
    handshake: dict[str, Any] | None = None

    for market_type in (0, 1, 2):
        basic_payload = {
            "marketType": market_type,
            "industryNameList": [],
            "companyCodeList": [],
            "year": 2024,
        }
        variants = [
            ("bare", basic_payload),
            (
                "bare-expanded-payload",
                dict(basic_payload, industryName="all", companyCode=""),
            ),
        ]
        market_records: list[dict[str, Any]] = []

        for mode, payload in variants:
            headers = {
                "User-Agent": UA,
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://esggenplus.twse.com.tw",
                "Referer": "https://esggenplus.twse.com.tw/inquiry/report",
            }
            try:
                response = requests.post(ESG_URL, json=payload, headers=headers, timeout=90)
                text = response.text
                parsed_json = response.json()
                records = extract_esg_records(parsed_json)
                attempt = {
                    "marketType": market_type,
                    "mode": mode,
                    "http_status": response.status_code,
                    "length": len(text),
                    "contains_security_text": SECURITY_TEXT in text,
                    "records": len(records),
                    "preview": re.sub(r"\s+", " ", text[:240]),
                }
                attempts.append(attempt)
                print("ESG_ATTEMPT", json.dumps(attempt, ensure_ascii=False))
                if response.ok and records:
                    market_records = records
                    break
            except Exception as exc:  # noqa: BLE001
                attempt = {
                    "marketType": market_type,
                    "mode": mode,
                    "error": f"{type(exc).__name__}: {exc}",
                }
                attempts.append(attempt)
                print("ESG_ATTEMPT", json.dumps(attempt, ensure_ascii=False))

        if not market_records:
            try:
                if session is None:
                    session, token, handshake = get_antiforgery_session()
                    print("ESG_HANDSHAKE", json.dumps(handshake, ensure_ascii=False))
                auth_headers = {
                    "User-Agent": UA,
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/plain, */*",
                    "Origin": "https://esggenplus.twse.com.tw",
                    "Referer": "https://esggenplus.twse.com.tw/inquiry/report",
                    "RequestVerificationToken": token,
                }
                for payload_variant in (
                    basic_payload,
                    dict(basic_payload, industryName="all", companyCode=""),
                ):
                    response = session.post(
                        ESG_URL,
                        json=payload_variant,
                        headers=auth_headers,
                        timeout=90,
                    )
                    text = response.text
                    parsed_json = response.json()
                    records = extract_esg_records(parsed_json)
                    attempt = {
                        "marketType": market_type,
                        "mode": "antiforgery",
                        "expanded_payload": "industryName" in payload_variant,
                        "http_status": response.status_code,
                        "length": len(text),
                        "contains_security_text": SECURITY_TEXT in text,
                        "records": len(records),
                        "preview": re.sub(r"\s+", " ", text[:240]),
                    }
                    attempts.append(attempt)
                    print("ESG_ATTEMPT", json.dumps(attempt, ensure_ascii=False))
                    if response.ok and records:
                        market_records = records
                        break
            except Exception as exc:  # noqa: BLE001
                attempt = {
                    "marketType": market_type,
                    "mode": "antiforgery",
                    "error": f"{type(exc).__name__}: {exc}",
                }
                attempts.append(attempt)
                print("ESG_ATTEMPT", json.dumps(attempt, ensure_ascii=False))

        all_records.extend(market_records)

    if not all_records:
        return {
            "ok": False,
            "error": "No ESG report rows returned",
            "attempts": attempts,
            "handshake": handshake,
        }
    meta = write_json("twse_esg_reports.json", all_records)
    meta["attempts"] = attempts
    meta["handshake"] = handshake
    meta["market_types_requested"] = [0, 1, 2]
    return meta


def network_info() -> dict[str, Any]:
    info: dict[str, Any] = {
        "type": "雲端主機（GitHub-hosted Actions runner）",
        "github_actions": os.getenv("GITHUB_ACTIONS"),
        "runner_environment": os.getenv("RUNNER_ENVIRONMENT"),
        "runner_os": os.getenv("RUNNER_OS"),
        "runner_arch": os.getenv("RUNNER_ARCH"),
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python": sys.version,
    }
    try:
        with urllib.request.urlopen("https://api.ipify.org?format=json", timeout=20) as response:
            info["public_ip"] = json.loads(response.read().decode("utf-8")).get("ip")
    except Exception as exc:  # noqa: BLE001
        info["public_ip_error"] = f"{type(exc).__name__}: {exc}"
    return info


def main() -> None:
    esg_probe_body = json.dumps(
        {
            "marketType": 0,
            "industryNameList": [],
            "companyCodeList": [],
            "year": 2024,
        }
    ).encode()
    probes = [
        exact_probe("上市基本資料", LISTED_URL),
        exact_probe("ESG報告書清單", ESG_URL, esg_probe_body),
    ]
    fetches = {
        "twse_listed.json": fetch_listed(),
        "twse_employees.json": fetch_employees(),
        "twse_esg_reports.json": fetch_esg(),
    }
    result = {
        "generated_at_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "network": network_info(),
        "probe_results": probes,
        "fetch_results": fetches,
        "pdf_downloads_attempted": False,
    }
    write_json("probe_result.json", result)
    print("FINAL_RESULT", json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
