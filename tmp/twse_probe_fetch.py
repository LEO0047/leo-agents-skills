import html as htmlmod
import json
import os
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path("out")
OUT.mkdir(parents=True, exist_ok=True)

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
SECURITY_TEXT = "安全性考量"
JSON_HEADERS = {"User-Agent": UA, "Content-Type": "application/json"}


def preview(text, n=360):
    return re.sub(r"\s+", " ", text[:n]).strip()


def write_json(path, obj, *, indent=None):
    Path(path).write_text(
        json.dumps(obj, ensure_ascii=False, indent=indent), encoding="utf-8"
    )


def exact_probe(name, url, body=None):
    result = {"name": name, "url": url}
    try:
        req = urllib.request.Request(url, data=body, headers=JSON_HEADERS)
        with urllib.request.urlopen(req, timeout=90) as response:
            text = response.read().decode("utf-8", "ignore")
            blocked = SECURITY_TEXT in text
            result.update(
                classification="被擋" if blocked else "正常",
                http_status=getattr(response, "status", None),
                length=len(text),
                contains_security_text=blocked,
                content_type=response.headers.get("Content-Type", ""),
                preview=preview(text),
            )
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", "ignore")
        result.update(
            classification="被擋" if SECURITY_TEXT in text else "錯誤",
            http_status=exc.code,
            length=len(text),
            contains_security_text=SECURITY_TEXT in text,
            error=f"HTTPError {exc.code}: {exc.reason}",
            preview=preview(text),
        )
    except Exception as exc:
        result.update(classification="錯誤", error=f"{type(exc).__name__}: {exc}")
    print("PROBE", json.dumps(result, ensure_ascii=False))
    return result


def request_text(url, data=None, content_type=None, origin=None, referer=None):
    headers = {"User-Agent": UA}
    if content_type:
        headers["Content-Type"] = content_type
    if origin:
        headers["Origin"] = origin
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as response:
        return (
            response.read().decode("utf-8", "ignore"),
            getattr(response, "status", None),
            response.geturl(),
        )


def clean_cell(value):
    value = re.sub(r"<[^>]+>", "", value)
    value = htmlmod.unescape(value).replace("\xa0", "").strip()
    return re.sub(r"\s+", " ", value)


def parse_employees(text):
    employees = {}
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


def main():
    payload0 = json.dumps(
        {
            "marketType": 0,
            "industryNameList": [],
            "companyCodeList": [],
            "year": 2024,
        }
    ).encode()
    probes = [
        exact_probe(
            "上市基本資料",
            "https://openapi.twse.com.tw/v1/opendata/t187ap03_L",
        ),
        exact_probe(
            "ESG報告書清單",
            "https://esggenplus.twse.com.tw/api/api/MopsSustainReport/data",
            payload0,
        ),
    ]

    fetch_results = {}
    all_normal = all(item.get("classification") == "正常" for item in probes)

    if all_normal:
        # 1) 上市公司基本資料
        try:
            text, status, final_url = request_text(
                "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
            )
            listed = json.loads(text)
            write_json(OUT / "twse_listed.json", listed)
            fetch_results["twse_listed.json"] = {
                "ok": True,
                "records": len(listed),
                "bytes": (OUT / "twse_listed.json").stat().st_size,
                "http_status": status,
                "final_url": final_url,
            }
        except Exception as exc:
            fetch_results["twse_listed.json"] = {
                "ok": False,
                "error": f"{type(exc).__name__}: {exc}",
            }

        # 2) 員工人數。先測使用者原網址；被安全頁擋時改用現行 mopsov 主機。
        employees = {}
        employee_attempts = []
        market_counts = {}
        for market in ("sii", "otc"):
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
            market_data = {}
            for base in (
                "https://mops.twse.com.tw",
                "https://mopsov.twse.com.tw",
            ):
                url = f"{base}/mops/web/ajax_t100sb14"
                try:
                    text, status, final_url = request_text(
                        url,
                        form,
                        "application/x-www-form-urlencoded",
                        base,
                        f"{base}/mops/web/t100sb14",
                    )
                    parsed = parse_employees(text)
                    attempt = {
                        "market": market,
                        "url": url,
                        "final_url": final_url,
                        "http_status": status,
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

        if employees:
            write_json(OUT / "twse_employees.json", employees)
            fetch_results["twse_employees.json"] = {
                "ok": True,
                "records": len(employees),
                "market_counts": market_counts,
                "bytes": (OUT / "twse_employees.json").stat().st_size,
                "attempts": employee_attempts,
            }
        else:
            fetch_results["twse_employees.json"] = {
                "ok": False,
                "error": "上市與上櫃合計解析為 0 筆",
                "attempts": employee_attempts,
            }

        # 3) 2024 永續報告書清單，只取清單，不下載 PDF。
        reports = []
        esg_counts = {}
        esg_attempts = []
        for market_type in (0, 1, 2):
            payload = json.dumps(
                {
                    "marketType": market_type,
                    "industryNameList": [],
                    "companyCodeList": [],
                    "year": 2024,
                }
            ).encode()
            try:
                text, status, final_url = request_text(
                    "https://esggenplus.twse.com.tw/api/api/MopsSustainReport/data",
                    payload,
                    "application/json",
                    "https://esggenplus.twse.com.tw",
                    "https://esggenplus.twse.com.tw/inquiry/report",
                )
                result = json.loads(text)
                data = result.get("data", [])
                esg_counts[str(market_type)] = len(data)
                reports.extend(data)
                attempt = {
                    "marketType": market_type,
                    "http_status": status,
                    "final_url": final_url,
                    "length": len(text),
                    "records": len(data),
                    "contains_security_text": SECURITY_TEXT in text,
                    "success": result.get("success"),
                    "message": result.get("message"),
                }
                esg_attempts.append(attempt)
                print("ESG", json.dumps(attempt, ensure_ascii=False))
            except Exception as exc:
                attempt = {
                    "marketType": market_type,
                    "error": f"{type(exc).__name__}: {exc}",
                }
                esg_attempts.append(attempt)
                print("ESG", json.dumps(attempt, ensure_ascii=False))

        if reports:
            write_json(OUT / "twse_esg_reports.json", reports)
            fetch_results["twse_esg_reports.json"] = {
                "ok": True,
                "records": len(reports),
                "market_counts": esg_counts,
                "bytes": (OUT / "twse_esg_reports.json").stat().st_size,
                "attempts": esg_attempts,
            }
        else:
            fetch_results["twse_esg_reports.json"] = {
                "ok": False,
                "error": "三個 marketType 合計 0 筆",
                "attempts": esg_attempts,
            }
    else:
        fetch_results = {
            "skipped": True,
            "reason": "第一步並非兩個端點都正常，依使用者條件不執行第二步。",
        }

    result = {
        "network": {
            "type": "GitHub-hosted cloud runner",
            "github_actions": os.getenv("GITHUB_ACTIONS"),
            "runner_environment": os.getenv("RUNNER_ENVIRONMENT"),
            "runner_os": os.getenv("RUNNER_OS"),
            "runner_arch": os.getenv("RUNNER_ARCH"),
            "image_os": os.getenv("ImageOS"),
            "hostname": socket.gethostname(),
        },
        "probe_results": probes,
        "all_normal": all_normal,
        "fetch_results": fetch_results,
        "pdf_downloaded": False,
    }
    write_json(OUT / "probe_result.json", result, indent=2)
    print("FINAL_RESULT", json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
