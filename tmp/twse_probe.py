import html as htmlmod
import json
import os
import platform
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT = Path("out")
OUT.mkdir(parents=True, exist_ok=True)

SECURITY_TEXT = "因為安全性考量，您所執行的頁面無法呈現"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
)
JSON_HEADERS = {"User-Agent": UA, "Content-Type": "application/json"}


def write_json(path: Path, data, *, indent=None):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=indent),
        encoding="utf-8",
    )


def preview(text: str, limit: int = 320) -> str:
    return re.sub(r"\s+", " ", text[:limit]).strip()


def exact_probe(name: str, url: str, body=None):
    result = {"name": name, "url": url}
    try:
        request = urllib.request.Request(url, data=body, headers=JSON_HEADERS)
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read()
            text = raw.decode("utf-8", "ignore")
            blocked = SECURITY_TEXT in text
            result.update(
                classification="被擋" if blocked else "正常",
                http_status=getattr(response, "status", None),
                length=len(text),
                content_type=response.headers.get("Content-Type", ""),
                contains_security_text=blocked,
                preview=preview(text),
            )
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        text = raw.decode("utf-8", "ignore")
        blocked = SECURITY_TEXT in text
        result.update(
            classification="被擋" if blocked else "錯誤",
            http_status=exc.code,
            length=len(text),
            contains_security_text=blocked,
            error=f"HTTPError {exc.code}: {exc.reason}",
            preview=preview(text),
        )
    except Exception as exc:
        result.update(classification="錯誤", error=f"{type(exc).__name__}: {exc}")

    print(
        f"{name}: {result['classification']}"
        + (
            f"  HTTP={result.get('http_status')} 長度={result.get('length')}"
            if "length" in result
            else ""
        )
        + (f"  {result.get('error')}" if result.get("error") else "")
    )
    return result


def get_text(url: str, data=None, content_type: str | None = None) -> str:
    headers = {"User-Agent": UA}
    if content_type:
        headers["Content-Type"] = content_type
    request = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read().decode("utf-8", "ignore")


def clean_cell(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = htmlmod.unescape(value).replace("\xa0", "").strip()
    return re.sub(r"\s+", " ", value)


def parse_employees(text: str) -> dict[str, int]:
    employees: dict[str, int] = {}
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", text, re.S | re.I):
        cells = [
            clean_cell(cell)
            for cell in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S | re.I)
        ]
        if len(cells) >= 7 and re.fullmatch(r"\d{4}", cells[1] or ""):
            try:
                employees[cells[1]] = int(float(cells[6].replace(",", "")))
            except ValueError:
                pass
    return employees


def fetch_requested_files():
    results = {}

    # 1) 上市公司基本資料
    try:
        text = get_text("https://openapi.twse.com.tw/v1/opendata/t187ap03_L")
        listed = json.loads(text)
        path = OUT / "twse_listed.json"
        path.write_text(text, encoding="utf-8")
        results[path.name] = {
            "ok": True,
            "records": len(listed) if isinstance(listed, list) else None,
            "bytes": path.stat().st_size,
            "source": "https://openapi.twse.com.tw/v1/opendata/t187ap03_L",
        }
        print(path.name, results[path.name])
    except Exception as exc:
        results["twse_listed.json"] = {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
        print("twse_listed.json 失敗:", results["twse_listed.json"]["error"])

    # 2) 員工人數：先測使用者原網址；若該舊主機回安全頁，改用現行 mopsov 主機。
    employees: dict[str, int] = {}
    employee_attempts = []
    market_counts = {}
    try:
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
            market_data: dict[str, int] = {}
            for base in (
                "https://mops.twse.com.tw",
                "https://mopsov.twse.com.tw",
            ):
                url = f"{base}/mops/web/ajax_t100sb14"
                try:
                    text = get_text(
                        url,
                        body,
                        "application/x-www-form-urlencoded",
                    )
                    parsed = parse_employees(text)
                    attempt = {
                        "market": market,
                        "url": url,
                        "length": len(text),
                        "contains_security_text": SECURITY_TEXT in text,
                        "records": len(parsed),
                        "preview": preview(text),
                    }
                    employee_attempts.append(attempt)
                    print("EMPLOYEE", json.dumps(attempt, ensure_ascii=False))
                    if parsed:
                        market_data = parsed
                        break
                except Exception as exc:
                    attempt = {
                        "market": market,
                        "url": url,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                    employee_attempts.append(attempt)
                    print("EMPLOYEE", json.dumps(attempt, ensure_ascii=False))

            market_counts[market] = len(market_data)
            employees.update(market_data)

        if not employees:
            raise RuntimeError("上市與上櫃合計解析為 0 筆")

        path = OUT / "twse_employees.json"
        write_json(path, employees)
        results[path.name] = {
            "ok": True,
            "records": len(employees),
            "market_counts": market_counts,
            "bytes": path.stat().st_size,
            "attempts": employee_attempts,
        }
        print(path.name, results[path.name])
    except Exception as exc:
        results["twse_employees.json"] = {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "attempts": employee_attempts,
        }
        print("twse_employees.json 失敗:", results["twse_employees.json"]["error"])

    # 3) 2024 永續報告書清單（只抓清單，不下載 PDF）
    reports = []
    esg_market_counts = {}
    try:
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
            esg_market_counts[str(market_type)] = len(data)
            reports.extend(data)
            print("marketType", market_type, "筆數", len(data))

        if not reports:
            raise RuntimeError("三個 marketType 合計為 0 筆")

        path = OUT / "twse_esg_reports.json"
        write_json(path, reports)
        results[path.name] = {
            "ok": True,
            "records": len(reports),
            "market_counts": esg_market_counts,
            "bytes": path.stat().st_size,
        }
        print(path.name, results[path.name])
    except Exception as exc:
        results["twse_esg_reports.json"] = {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
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

    fetch_results = (
        fetch_requested_files()
        if all_normal
        else {
            "skipped": True,
            "reason": "第一步並非兩個端點都顯示正常，依使用者條件不執行第二步。",
        }
    )

    result = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "probe_results": probe_results,
        "all_normal": all_normal,
        "fetch_results": fetch_results,
        "network_info": network_info,
        "pdf_downloaded": False,
    }
    write_json(OUT / "probe_result.json", result, indent=2)
    print("FINAL_RESULT", json.dumps(result, ensure_ascii=False))
    print("完成；未下載任何 PDF。")


if __name__ == "__main__":
    main()
