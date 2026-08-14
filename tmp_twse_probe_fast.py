#!/usr/bin/env python3
"""Bounded one-off TWSE probe; JSON metadata only, no PDF downloads."""

from __future__ import annotations

import concurrent.futures
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
import urllib.request
from pathlib import Path
from typing import Any

import requests

OUT = Path("twse_probe_output_fast")
OUT.mkdir(exist_ok=True)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
SECURITY_TEXT = "安全性考量"
LISTED_URL = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
ESG_URL = "https://esggenplus.twse.com.tw/api/api/MopsSustainReport/data"
TIMEOUT = 20


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save_json(name: str, data: Any) -> dict[str, Any]:
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    path = OUT / name
    path.write_bytes(raw)
    return {"ok": True, "records": len(data), "bytes": len(raw), "sha256": digest(raw)}


def probe(name: str, url: str, body: bytes | None = None) -> tuple[dict[str, Any], bytes | None]:
    headers = {"User-Agent": UA, "Content-Type": "application/json"}
    result: dict[str, Any] = {"name": name, "method": "POST" if body else "GET", "url": url}
    raw: bytes | None = None
    try:
        request = urllib.request.Request(url, data=body, headers=headers)
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            raw = response.read()
            text = raw.decode("utf-8", "ignore")
            result.update(
                classification="被擋" if SECURITY_TEXT in text else "正常",
                http_status=response.status,
                length=len(text),
                bytes=len(raw),
                contains_security_text=SECURITY_TEXT in text,
                content_type=response.headers.get("Content-Type", ""),
                sha256=digest(raw),
                preview=re.sub(r"\s+", " ", text[:300]),
            )
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        text = raw.decode("utf-8", "ignore")
        classification = "被擋" if SECURITY_TEXT in text or exc.code in (403, 429) else "錯誤"
        result.update(
            classification=classification,
            http_status=exc.code,
            length=len(text),
            bytes=len(raw),
            contains_security_text=SECURITY_TEXT in text,
            error=f"HTTPError {exc.code}: {exc.reason}",
            preview=re.sub(r"\s+", " ", text[:500]),
        )
    except Exception as exc:
        result.update(classification="錯誤", error=f"{type(exc).__name__}: {exc}")
    print("PROBE", json.dumps(result, ensure_ascii=False), flush=True)
    return result, raw


def clean_cell(fragment: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        html_module.unescape(re.sub(r"<[^>]+>", "", fragment)).replace("\xa0", "").strip(),
    )


def parse_employees(text: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", text, re.S | re.I):
        cells = [clean_cell(x) for x in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S | re.I)]
        if len(cells) >= 7 and re.fullmatch(r"\d{4}", cells[1] or ""):
            try:
                result[cells[1]] = int(float(cells[6].replace(",", "")))
            except ValueError:
                pass
    return result


def employee_market(market: str) -> tuple[dict[str, int], list[dict[str, Any]]]:
    attempts: list[dict[str, Any]] = []
    payload = {
        "encodeURIComponent": "1",
        "step": "1",
        "firstin": "1",
        "off": "1",
        "TYPEK": market,
        "RYEAR": "114",
        "code": "",
    }
    for host in ("mopsov.twse.com.tw", "mops.twse.com.tw"):
        url = f"https://{host}/mops/web/ajax_t100sb14"
        try:
            response = requests.post(
                url,
                data=payload,
                headers={
                    "User-Agent": UA,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Origin": f"https://{host}",
                    "Referer": f"https://{host}/mops/web/t100sb14",
                },
                timeout=(8, TIMEOUT),
            )
            response.encoding = "utf-8"
            text = response.text
            rows = parse_employees(text)
            attempt = {
                "market": market,
                "url": url,
                "http_status": response.status_code,
                "length": len(text),
                "contains_security_text": SECURITY_TEXT in text,
                "parsed_records": len(rows),
                "preview": re.sub(r"\s+", " ", text[:240]),
            }
            attempts.append(attempt)
            print("EMP", json.dumps(attempt, ensure_ascii=False), flush=True)
            if rows:
                return rows, attempts
        except Exception as exc:
            attempt = {"market": market, "url": url, "error": f"{type(exc).__name__}: {exc}"}
            attempts.append(attempt)
            print("EMP", json.dumps(attempt, ensure_ascii=False), flush=True)
    return {}, attempts


def fetch_employees() -> dict[str, Any]:
    combined: dict[str, int] = {}
    attempts: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(employee_market, market): market for market in ("sii", "otc")}
        for future in concurrent.futures.as_completed(futures):
            rows, logs = future.result()
            combined.update(rows)
            attempts.extend(logs)
    if not combined:
        return {"ok": False, "error": "No employee rows parsed", "attempts": attempts}
    meta = save_json("twse_employees.json", combined)
    meta["attempts"] = attempts
    return meta


def records_from(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    data = payload.get("data", [])
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ("data", "items", "rows", "result"):
            value = data.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
    return []


def fetch_esg() -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Accept-Language": "zh-TW,zh;q=0.9"})
    token = ""
    handshake: dict[str, Any] | None = None

    try:
        home = session.get("https://esggenplus.twse.com.tw/", timeout=(8, TIMEOUT))
        token_response = session.get(
            "https://esggenplus.twse.com.tw/api/api/Antiforgery/token",
            headers={"Referer": "https://esggenplus.twse.com.tw/inquiry/report"},
            timeout=(8, TIMEOUT),
        )
        token_payload = token_response.json()
        token = token_payload.get("data", "") if isinstance(token_payload, dict) else ""
        handshake = {
            "home_status": home.status_code,
            "token_status": token_response.status_code,
            "token_length": len(token) if isinstance(token, str) else 0,
            "cookie_names": sorted(session.cookies.keys()),
        }
        print("ESG_HANDSHAKE", json.dumps(handshake, ensure_ascii=False), flush=True)
    except Exception as exc:
        handshake = {"error": f"{type(exc).__name__}: {exc}"}
        print("ESG_HANDSHAKE", json.dumps(handshake, ensure_ascii=False), flush=True)

    for market_type in (0, 1, 2):
        payload = {
            "marketType": market_type,
            "industryNameList": [],
            "companyCodeList": [],
            "year": 2024,
        }
        headers = {
            "User-Agent": UA,
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://esggenplus.twse.com.tw",
            "Referer": "https://esggenplus.twse.com.tw/inquiry/report",
        }
        if isinstance(token, str) and token:
            headers["RequestVerificationToken"] = token
        try:
            response = session.post(ESG_URL, json=payload, headers=headers, timeout=(8, TIMEOUT))
            text = response.text
            data = response.json()
            rows = records_from(data)
            attempt = {
                "marketType": market_type,
                "http_status": response.status_code,
                "length": len(text),
                "contains_security_text": SECURITY_TEXT in text,
                "records": len(rows),
                "used_antiforgery": bool(token),
                "preview": re.sub(r"\s+", " ", text[:240]),
            }
            attempts.append(attempt)
            print("ESG", json.dumps(attempt, ensure_ascii=False), flush=True)
            all_rows.extend(rows)
        except Exception as exc:
            attempt = {"marketType": market_type, "error": f"{type(exc).__name__}: {exc}", "used_antiforgery": bool(token)}
            attempts.append(attempt)
            print("ESG", json.dumps(attempt, ensure_ascii=False), flush=True)

    if not all_rows:
        return {"ok": False, "error": "No ESG rows returned", "attempts": attempts, "handshake": handshake}
    meta = save_json("twse_esg_reports.json", all_rows)
    meta.update({"attempts": attempts, "handshake": handshake})
    return meta


def main() -> None:
    esg_body = json.dumps({"marketType": 0, "industryNameList": [], "companyCodeList": [], "year": 2024}).encode()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        listed_future = executor.submit(probe, "上市基本資料", LISTED_URL, None)
        esg_future = executor.submit(probe, "ESG報告書清單", ESG_URL, esg_body)
        listed_probe, listed_raw = listed_future.result()
        esg_probe, _ = esg_future.result()

    fetches: dict[str, Any] = {}
    try:
        if listed_raw:
            listed = json.loads(listed_raw.decode("utf-8-sig"))
            fetches["twse_listed.json"] = save_json("twse_listed.json", listed)
        else:
            fetches["twse_listed.json"] = {"ok": False, "error": "Probe did not return a JSON body"}
    except Exception as exc:
        traceback.print_exc()
        fetches["twse_listed.json"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        employee_future = executor.submit(fetch_employees)
        esg_fetch_future = executor.submit(fetch_esg)
        fetches["twse_employees.json"] = employee_future.result()
        fetches["twse_esg_reports.json"] = esg_fetch_future.result()

    network = {
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
        network["public_ip"] = requests.get("https://api.ipify.org", timeout=(5, 10)).text.strip()
    except Exception as exc:
        network["public_ip_error"] = f"{type(exc).__name__}: {exc}"

    result = {
        "network": network,
        "probe_results": [listed_probe, esg_probe],
        "fetch_results": fetches,
        "pdf_downloads_attempted": False,
    }
    save_json("probe_result.json", result)
    print("FINAL", json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
