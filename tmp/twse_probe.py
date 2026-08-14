import json
import os
import platform
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SECURITY_TEXT = "因為安全性考量，您所執行的頁面無法呈現"
H = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    "Content-Type": "application/json",
}


def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def exact_probe(name, url, body=None):
    result = {"name": name, "url": url}
    try:
        req = urllib.request.Request(url, data=body, headers=H)
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read()
            text = raw.decode("utf-8", "ignore")
            result.update(
                classification="被擋" if SECURITY_TEXT in text else "正常",
                http_status=getattr(response, "status", None),
                length=len(text),
                content_type=response.headers.get("Content-Type", ""),
                contains_security_text=SECURITY_TEXT in text,
                preview=text[:300],
            )
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        text = raw.decode("utf-8", "ignore")
        result.update(
            classification="被擋" if SECURITY_TEXT in text else "錯誤",
            http_status=exc.code,
            length=len(text),
            contains_security_text=SECURITY_TEXT in text,
            error=f"HTTPError {exc.code}: {exc.reason}",
            preview=text[:500],
        )
    except Exception as exc:
        result.update(classification="錯誤", error=f"{type(exc).__name__}: {exc}")

    print(
        f"{name}: {result['classification']}"
        + (f"  HTTP={result.get('http_status')} 長度={result.get('length')}" if "length" in result else "")
        + (f"  {result.get('error')}" if result.get("error") else "")
    )
    return result


def get_text(url, data=None, content_type=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
    }
    if content_type:
        headers["Content-Type"] = content_type
    request = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read().decode("utf-8", "ignore")


def clean_cell(value):
    return re.sub(r"<[^>]+>", "", value).replace("&nbsp;", "").strip()


def fetch_requested_files():
    results = {}

    # 1) 上市公司基本資料
    try:
        text = get_text("https://openapi.twse.com.tw/v1/opendata/t187ap03_L")
        parsed = json.loads(text)
        Path("twse_listed.json").write_text(text, encoding="utf-8")
        results["twse_listed.json"] = {
            "ok": True,
            "records": len(parsed) if isinstance(parsed, list) else None,
            "bytes": Path("twse_listed.json").stat().st_size,
        }
        print("twse_listed.json:", results["twse_listed.json"])
    except Exception as exc:
        results["twse_listed.json"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        print("twse_listed.json 失敗:", results["twse_listed.json"]["error"])

    # 2) 員工人數（完全沿用使用者提供的網址、欄位與年度）
    try:
        employees = {}
        market_counts = {}
        for market in ("sii", "otc"):
            body = urllib.parse.urlencode(
                {
                    "encodeURIComponent": 1,
                    "step": 1,
                    "firstin": 1,
                    "off": 1,
                    "TYPEK": market,
                    "RYEAR": "114",
                }
            ).encode()
            html = get_text(
                "https://mops.twse.com.tw/mops/web/ajax_t100sb14",
                body,
                "application/x-www-form-urlencoded",
            )
            count = 0
            for row in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S):
                cells = [clean_cell(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
                if len(cells) >= 7 and re.fullmatch(r"\d{4}", cells[1]):
                    try:
                        employees[cells[1]] = int(float(cells[6].replace(",", "")))
                        count += 1
                    except ValueError:
                        pass
            market_counts[market] = count
            print(market, "取得", count, "筆")
        if not employees:
            raise RuntimeError("上市與上櫃合計解析為 0 筆")
        Path("twse_employees.json").write_text(
            json.dumps(employees, ensure_ascii=False), encoding="utf-8"
        )
        results["twse_employees.json"] = {
            "ok": True,
            "records": len(employees),
            "market_counts": market_counts,
            "bytes": Path("twse_employees.json").stat().st_size,
        }
    except Exception as exc:
        results["twse_employees.json"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        print("twse_employees.json 失敗:", results["twse_employees.json"]["error"])

    # 3) 2024 永續報告書清單（不下載 PDF）
    try:
        reports = []
        market_counts = {}
        for market_type in (0, 1, 2):
            payload = json.dumps(
                {
                    "marketType": market_type,
                    "industryNameList": [],
                    "companyCodeList": [],
                    "year": 2024,
                }
            ).encode()
            response = json.loads(
                get_text(
                    "https://esggenplus.twse.com.tw/api/api/MopsSustainReport/data",
                    payload,
                    "application/json",
                )
            )
            data = response.get("data", [])
            market_counts[str(market_type)] = len(data)
            reports.extend(data)
            print("marketType", market_type, "筆數", len(data))
        if not reports:
            raise RuntimeError("三個 marketType 合計為 0 筆")
        Path("twse_esg_reports.json").write_text(
            json.dumps(reports, ensure_ascii=False), encoding="utf-8"
        )
        results["twse_esg_reports.json"] = {
            "ok": True,
            "records": len(reports),
            "market_counts": market_counts,
            "bytes": Path("twse_esg_reports.json").stat().st_size,
        }
    except Exception as exc:
        results["twse_esg_reports.json"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        print("twse_esg_reports.json 失敗:", results["twse_esg_reports.json"]["error"])

    return results


def main():
    tests = [
        (
            "上市基本資料",
            "https://openapi.twse.com.tw/v1/opendata/t187ap03_L",
            None,
        ),
        (
            "ESG報告書清單",
            "https://esggenplus.twse.com.tw/api/api/MopsSustainReport/data",
            json.dumps(
                {
                    "marketType": 0,
                    "industryNameList": [],
                    "companyCodeList": [],
                    "year": 2024,
                }
            ).encode(),
        ),
    ]

    probe_results = [exact_probe(name, url, body) for name, url, body in tests]
    all_normal = all(item.get("classification") == "正常" for item in probe_results)

    network_info = {
        "type": "cloud_host",
        "provider": "GitHub Actions hosted runner",
        "github_actions": os.getenv("GITHUB_ACTIONS"),
        "runner_environment": os.getenv("RUNNER_ENVIRONMENT"),
        "runner_os": os.getenv("RUNNER_OS"),
        "runner_arch": os.getenv("RUNNER_ARCH"),
        "image_os": os.getenv("ImageOS"),
        "image_version": os.getenv("ImageVersion"),
        "hostname": socket.gethostname(),
        "python": platform.python_version(),
    }

    fetch_results = fetch_requested_files() if all_normal else {
        "skipped": True,
        "reason": "第一步並非兩個端點都顯示正常，依使用者條件不執行第二步。",
    }

    write_json(
        "probe_result.json",
        {
            "probe_results": probe_results,
            "all_normal": all_normal,
            "fetch_results": fetch_results,
            "network_info": network_info,
            "pdf_downloaded": False,
        },
    )
    print("完成；未下載任何 PDF。")


if __name__ == "__main__":
    main()
