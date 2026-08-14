#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import html as html_lib
import http.cookiejar
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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OUT = Path("out")
DEBUG = OUT / "debug"
OUT.mkdir(parents=True, exist_ok=True)
DEBUG.mkdir(parents=True, exist_ok=True)

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
)
SECURITY_TEXT = "安全性考量"


def decode_body(raw: bytes, headers: Any = None) -> str:
    charset = None
    try:
        charset = headers.get_content_charset() if headers is not None else None
    except Exception:
        charset = None
    for enc in [charset, "utf-8", "big5", "cp950"]:
        if not enc:
            continue
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            pass
    return raw.decode("utf-8", "ignore")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, obj: Any, *, indent: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, ensure_ascii=False, indent=indent),
        encoding="utf-8",
    )


def safe_preview(text: str, limit: int = 400) -> str:
    return re.sub(r"\s+", " ", text[:limit]).strip()


def classify_response(status: int | None, text: str) -> str:
    if SECURITY_TEXT in text:
        return "被擋"
    if status is not None and 200 <= status < 300:
        return "正常"
    if status in {401, 403, 407, 429}:
        return "被擋"
    return "錯誤"


def exact_probe(name: str, url: str, body: bytes | None = None) -> tuple[dict[str, Any], str]:
    headers = {
        "User-Agent": UA,
        "Content-Type": "application/json",
    }
    result: dict[str, Any] = {
        "name": name,
        "url": url,
        "method": "POST" if body is not None else "GET",
    }
    text = ""
    try:
        req = urllib.request.Request(url, data=body, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read()
            text = decode_body(raw, response.headers)
            status = getattr(response, "status", None)
            result.update(
                http_status=status,
                length=len(text),
                content_type=response.headers.get("Content-Type", ""),
                contains_security_text=SECURITY_TEXT in text,
                classification=classify_response(status, text),
                preview=safe_preview(text),
            )
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        text = decode_body(raw, exc.headers)
        result.update(
            http_status=exc.code,
            length=len(text),
            content_type=exc.headers.get("Content-Type", "") if exc.headers else "",
            contains_security_text=SECURITY_TEXT in text,
            classification=classify_response(exc.code, text),
            error=f"HTTPError {exc.code}: {exc.reason}",
            preview=safe_preview(text),
        )
    except Exception as exc:
        result.update(
            classification="錯誤",
            error=f"{type(exc).__name__}: {exc}",
        )
    debug_name = "probe_" + ("listed" if "openapi" in url else "esg") + ".txt"
    write_text(DEBUG / debug_name, text)
    print(f"{name}: {result['classification']}  長度={result.get('length', 0)}")
    print("PROBE_JSON", json.dumps(result, ensure_ascii=False))
    return result, text


def make_request(
    url: str,
    *,
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    opener: urllib.request.OpenerDirector | None = None,
    timeout: int = 90,
) -> tuple[int, Any, bytes, str]:
    request = urllib.request.Request(url, data=data, headers=headers or {})
    target = opener.open if opener is not None else urllib.request.urlopen
    try:
        with target(request, timeout=timeout) as response:
            raw = response.read()
            return (
                int(getattr(response, "status", 200)),
                response.headers,
                raw,
                decode_body(raw, response.headers),
            )
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        return exc.code, exc.headers, raw, decode_body(raw, exc.headers)


def fetch_listed(probe: dict[str, Any], probe_text: str, results: dict[str, Any]) -> None:
    name = "twse_listed.json"
    try:
        if probe.get("classification") != "正常":
            raise RuntimeError("上市基本資料探測不是正常回應")
        data = json.loads(probe_text)
        if not isinstance(data, list) or not data:
            raise ValueError("回應不是非空 JSON 陣列")
        write_json(OUT / name, data)
        results[name] = {
            "ok": True,
            "records": len(data),
            "bytes": (OUT / name).stat().st_size,
        }
    except Exception as exc:
        results[name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        traceback.print_exc()


def clean_cell(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", "", fragment)
    text = html_lib.unescape(text).replace("\xa0", "").replace("&nbsp;", "")
    return re.sub(r"\s+", " ", text).strip()


def parse_employee_html(text: str) -> tuple[dict[str, int], dict[str, Any]]:
    employees: dict[str, int] = {}
    data_rows = 0
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", text, re.S | re.I):
        cells = [
            clean_cell(cell)
            for cell in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S | re.I)
        ]
        if len(cells) >= 7 and re.fullmatch(r"\d{4}", cells[1] or ""):
            data_rows += 1
            try:
                employees[cells[1]] = int(float(cells[6].replace(",", "")))
            except ValueError:
                pass
    return employees, {"data_rows": data_rows, "parsed": len(employees)}


def fetch_employees(results: dict[str, Any]) -> None:
    name = "twse_employees.json"
    attempts: list[dict[str, Any]] = []
    employees: dict[str, int] = {}
    endpoints = [
        "https://mops.twse.com.tw/mops/web/ajax_t100sb14",
        "https://mopsov.twse.com.tw/mops/web/ajax_t100sb14",
    ]
    try:
        for market in ("sii", "otc"):
            market_data: dict[str, int] = {}
            form = urllib.parse.urlencode(
                {
                    "encodeURIComponent": 1,
                    "step": 1,
                    "firstin": 1,
                    "off": 1,
                    "TYPEK": market,
                    "RYEAR": "114",
                }
            ).encode()
            for url in endpoints:
                origin = f"https://{urllib.parse.urlsplit(url).netloc}"
                headers = {
                    "User-Agent": UA,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Origin": origin,
                    "Referer": origin + "/mops/web/t100sb14",
                }
                status, response_headers, raw, text = make_request(
                    url, data=form, headers=headers, timeout=90
                )
                parsed, stats = parse_employee_html(text)
                attempt = {
                    "market": market,
                    "url": url,
                    "http_status": status,
                    "length": len(text),
                    "content_type": response_headers.get("Content-Type", "") if response_headers else "",
                    "contains_security_text": SECURITY_TEXT in text,
                    "classification": classify_response(status, text),
                    **stats,
                    "preview": safe_preview(text),
                }
                attempts.append(attempt)
                write_text(DEBUG / f"employees_{market}_{urllib.parse.urlsplit(url).netloc}.html", text)
                print("EMPLOYEE_ATTEMPT", json.dumps(attempt, ensure_ascii=False))
                if parsed:
                    market_data = parsed
                    break
            employees.update(market_data)
            print(f"{market} 取得 {len(market_data)} 筆")

        if not employees:
            raise RuntimeError("上市與上櫃皆解析為 0 筆")
        write_json(OUT / name, employees)
        results[name] = {
            "ok": True,
            "records": len(employees),
            "bytes": (OUT / name).stat().st_size,
            "attempts": attempts,
        }
    except Exception as exc:
        results[name] = {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "attempts": attempts,
        }
        traceback.print_exc()


def parse_esg_json(text: str) -> tuple[dict[str, Any], list[Any]]:
    obj = json.loads(text)
    if not isinstance(obj, dict):
        raise ValueError("ESG API 回應不是 JSON 物件")
    data = obj.get("data", [])
    if data is None:
        data = []
    if not isinstance(data, list):
        raise ValueError("ESG API 的 data 不是陣列")
    return obj, data


def bare_esg_request(market_type: int, year: int = 2024) -> tuple[dict[str, Any], list[Any]]:
    url = "https://esggenplus.twse.com.tw/api/api/MopsSustainReport/data"
    payload = {
        "marketType": market_type,
        "industryNameList": [],
        "companyCodeList": [],
        "year": year,
    }
    body = json.dumps(payload).encode()
    headers = {
        "User-Agent": UA,
        "Content-Type": "application/json",
    }
    status, response_headers, raw, text = make_request(
        url, data=body, headers=headers, timeout=90
    )
    write_text(DEBUG / f"esg_bare_mt{market_type}.txt", text)
    meta: dict[str, Any] = {
        "mode": "bare",
        "marketType": market_type,
        "http_status": status,
        "length": len(text),
        "content_type": response_headers.get("Content-Type", "") if response_headers else "",
        "contains_security_text": SECURITY_TEXT in text,
        "classification": classify_response(status, text),
        "preview": safe_preview(text),
    }
    data: list[Any] = []
    try:
        _, data = parse_esg_json(text)
        meta["json_valid"] = True
        meta["records"] = len(data)
    except Exception as exc:
        meta["json_valid"] = False
        meta["json_error"] = f"{type(exc).__name__}: {exc}"
    return meta, data


def token_from_obj(obj: Any) -> str | None:
    if isinstance(obj, str):
        return obj if len(obj) > 20 else None
    if isinstance(obj, dict):
        for key in ("data", "token", "requestVerificationToken", "antiforgeryToken"):
            if key in obj:
                found = token_from_obj(obj[key])
                if found:
                    return found
    return None


def authenticated_esg_requests(year: int = 2024) -> tuple[list[Any], list[dict[str, Any]], dict[str, Any]]:
    base = "https://esggenplus.twse.com.tw"
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    common_get_headers = {
        "User-Agent": UA,
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        "Referer": base + "/inquiry/report",
    }
    home_status, _, _, home_text = make_request(
        base + "/inquiry/report",
        headers=common_get_headers,
        opener=opener,
        timeout=60,
    )
    token_status, _, _, token_text = make_request(
        base + "/api/api/Antiforgery/token",
        headers={**common_get_headers, "Accept": "application/json, text/plain, */*"},
        opener=opener,
        timeout=60,
    )
    write_text(DEBUG / "esg_antiforgery_token.txt", token_text)
    token_obj = json.loads(token_text)
    token = token_from_obj(token_obj)
    handshake = {
        "home_status": home_status,
        "home_length": len(home_text),
        "token_status": token_status,
        "token_length": len(token_text),
        "token_found": bool(token),
        "cookie_names": [cookie.name for cookie in jar],
    }
    if not token:
        raise RuntimeError(f"找不到 Antiforgery token：{safe_preview(token_text)}")

    headers = {
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        "Content-Type": "application/json",
        "Origin": base,
        "Referer": base + "/inquiry/report",
        "RequestVerificationToken": token,
    }
    attempts: list[dict[str, Any]] = []
    all_reports: list[Any] = []
    for market_type in (0, 1, 2):
        payloads = [
            {
                "marketType": market_type,
                "industryNameList": [],
                "companyCodeList": [],
                "year": year,
            },
            {
                "marketType": market_type,
                "industryNameList": [],
                "companyCodeList": [],
                "year": year,
                "industryName": "all",
                "companyCode": "",
            },
        ]
        market_data: list[Any] = []
        for variant, payload in enumerate(payloads, start=1):
            status, response_headers, raw, text = make_request(
                base + "/api/api/MopsSustainReport/data",
                data=json.dumps(payload).encode(),
                headers=headers,
                opener=opener,
                timeout=90,
            )
            write_text(DEBUG / f"esg_token_mt{market_type}_v{variant}.txt", text)
            meta: dict[str, Any] = {
                "mode": "antiforgery",
                "variant": variant,
                "marketType": market_type,
                "http_status": status,
                "length": len(text),
                "content_type": response_headers.get("Content-Type", "") if response_headers else "",
                "contains_security_text": SECURITY_TEXT in text,
                "classification": classify_response(status, text),
                "preview": safe_preview(text),
            }
            try:
                _, market_data = parse_esg_json(text)
                meta["json_valid"] = True
                meta["records"] = len(market_data)
            except Exception as exc:
                meta["json_valid"] = False
                meta["json_error"] = f"{type(exc).__name__}: {exc}"
                market_data = []
            attempts.append(meta)
            print("ESG_TOKEN_ATTEMPT", json.dumps(meta, ensure_ascii=False))
            if market_data:
                break
        all_reports.extend(market_data)
    return all_reports, attempts, handshake


def fetch_esg(results: dict[str, Any]) -> None:
    name = "twse_esg_reports.json"
    attempts: list[dict[str, Any]] = []
    all_reports: list[Any] = []
    mode = None
    handshake: dict[str, Any] | None = None
    try:
        for market_type in (0, 1, 2):
            meta, data = bare_esg_request(market_type)
            attempts.append(meta)
            print("ESG_BARE_ATTEMPT", json.dumps(meta, ensure_ascii=False))
            all_reports.extend(data)
        if all_reports:
            mode = "bare"
        else:
            all_reports, token_attempts, handshake = authenticated_esg_requests()
            attempts.extend(token_attempts)
            if all_reports:
                mode = "antiforgery"

        if not all_reports:
            raise RuntimeError("ESG 裸請求與 Antiforgery 流程皆取得 0 筆")
        write_json(OUT / name, all_reports)
        results[name] = {
            "ok": True,
            "mode": mode,
            "records": len(all_reports),
            "bytes": (OUT / name).stat().st_size,
            "attempts": attempts,
            "handshake": handshake,
        }
    except Exception as exc:
        results[name] = {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "attempts": attempts,
            "handshake": handshake,
        }
        traceback.print_exc()


def fetch_network_info() -> dict[str, Any]:
    info: dict[str, Any] = {
        "network_type": "雲端主機（GitHub-hosted Ubuntu runner）",
        "github_actions": os.getenv("GITHUB_ACTIONS"),
        "runner_environment": os.getenv("RUNNER_ENVIRONMENT"),
        "runner_os": os.getenv("RUNNER_OS"),
        "runner_arch": os.getenv("RUNNER_ARCH"),
        "image_os": os.getenv("ImageOS"),
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python": sys.version,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    for label, url in (
        ("ipify", "https://api.ipify.org?format=json"),
        ("ipinfo", "https://ipinfo.io/json"),
    ):
        try:
            status, _, _, text = make_request(
                url,
                headers={"User-Agent": UA, "Accept": "application/json"},
                timeout=20,
            )
            info[label] = {"http_status": status, "data": json.loads(text)}
        except Exception as exc:
            info[label] = {"error": f"{type(exc).__name__}: {exc}"}
    return info


def add_checksums(results: dict[str, Any]) -> None:
    for path in sorted(OUT.glob("*.json")):
        if path.name == "probe_result.json":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        results.setdefault("checksums", {})[path.name] = {
            "sha256": digest,
            "bytes": path.stat().st_size,
        }
        print("FILE", path.name, path.stat().st_size, digest)


def main() -> int:
    probe_results: list[dict[str, Any]] = []
    listed_probe, listed_text = exact_probe(
        "上市基本資料",
        "https://openapi.twse.com.tw/v1/opendata/t187ap03_L",
    )
    probe_results.append(listed_probe)

    esg_body = json.dumps(
        {
            "marketType": 0,
            "industryNameList": [],
            "companyCodeList": [],
            "year": 2024,
        }
    ).encode()
    esg_probe, _ = exact_probe(
        "ESG報告書清單",
        "https://esggenplus.twse.com.tw/api/api/MopsSustainReport/data",
        esg_body,
    )
    probe_results.append(esg_probe)

    fetch_results: dict[str, Any] = {}
    fetch_listed(listed_probe, listed_text, fetch_results)
    fetch_employees(fetch_results)
    fetch_esg(fetch_results)
    network_info = fetch_network_info()
    write_json(OUT / "network_info.json", network_info, indent=2)

    meta: dict[str, Any] = {
        "probe_results": probe_results,
        "fetch_results": fetch_results,
        "network_info": network_info,
    }
    add_checksums(meta)
    write_json(OUT / "probe_result.json", meta, indent=2)
    print("FINAL_META", json.dumps(meta, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
