"""
HikVision HikCentral Connect API integration for attendance reports.
"""
import requests
import pandas as pd
from datetime import datetime, date
import os
import database as db

API_URL = "https://iind-team.hikcentralconnect.com/hcc/hccattendance/report/v1/list"

DEFAULT_HEADERS = {
    "accept": "application/json",
    "clientsource": "0",
    "content-type": "application/json",
    "origin": "https://www.hik-connect.com/",
    "referer": "https://www.hik-connect.com/",
}


def fetch_attendance(
    jsessionid: str,
    start_date: date,
    end_date: date,
    page: int = 1,
    page_size: int = 50,
    name_filter: str = "",
) -> dict:
    """Fetch attendance report from HikVision API. Returns raw JSON response."""
    headers = {
        **DEFAULT_HEADERS,
        "Cookie": f"JSESSIONID={jsessionid}",
    }

    start_str = f"{start_date.isoformat()}T00:00:00+05:30"
    end_str = f"{end_date.isoformat()}T23:59:59+05:30"

    body = {
        "page": page,
        "pageSize": page_size,
        "language": "en",
        "reportTypeId": 1,
        "columnIdList": [],
        "filterList": [
            {"columnName": "fullName", "operation": "LIKE", "value": name_filter},
            {"columnName": "personCode", "operation": "LIKE", "value": ""},
            {"columnName": "groupId", "operation": "IN", "value": ""},
            {"columnName": "clockStamp", "operation": "BETWEEN", "value": f"{start_str},{end_str}"},
            {"columnName": "deviceId", "operation": "IN", "value": ""},
        ],
        "order": {"columnName": "clockDate", "operation": "ASC"},
    }

    resp = requests.post(API_URL, json=body, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_all_pages(
    jsessionid: str,
    start_date: date,
    end_date: date,
    name_filter: str = "",
    page_size: int = 50,
    max_pages: int = 20,
) -> pd.DataFrame:
    """Fetch all pages and return a combined DataFrame."""
    all_rows = []
    page = 1

    while page <= max_pages:
        data = fetch_attendance(jsessionid, start_date, end_date, page, page_size, name_filter)

        rows = data.get("data", {}).get("list", [])
        if not rows:
            # Try alternate response shapes
            rows = data.get("list", [])
        if not rows:
            rows = data.get("data", []) if isinstance(data.get("data"), list) else []

        if not rows:
            break

        all_rows.extend(rows)

        total = data.get("data", {}).get("total", 0)
        if not total:
            total = data.get("total", len(all_rows))

        if len(all_rows) >= total:
            break

        page += 1

    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    return df


def get_jsessionid() -> str:
    """Get JSESSIONID from env var or return empty string."""
    return os.environ.get("HIKVISION_JSESSIONID", "")


def match_hikvision_to_employee(hik_name: str) -> str | None:
    """Try to match a HikVision full name to an existing employee.
    
    Matching strategy:
    1. Exact match (case-insensitive)
    2. HikVision name contains employee name or vice versa
    3. First+last name partial match
    """
    employees = db.get_all_employees()
    hik_lower = hik_name.strip().lower()

    # Exact match
    for emp in employees:
        if emp.lower() == hik_lower:
            return emp

    # Contains match
    for emp in employees:
        emp_lower = emp.lower()
        if emp_lower in hik_lower or hik_lower in emp_lower:
            return emp

    # Word overlap match (at least 2 words matching, or 1 word if single-word names)
    hik_words = set(hik_lower.split())
    for emp in employees:
        emp_words = set(emp.lower().split())
        overlap = hik_words & emp_words
        if len(overlap) >= min(2, len(emp_words), len(hik_words)):
            return emp

    return None


def import_to_local_db(df: pd.DataFrame, name_col: str, date_col: str, time_col: str | None = None) -> tuple[int, int, list[str]]:
    """Import HikVision data into the local attendance DB.
    
    Returns: (imported_count, skipped_count, unmatched_names)
    """
    imported = 0
    skipped = 0
    unmatched = []
    seen_unmatched = set()

    for _, row in df.iterrows():
        hik_name = str(row.get(name_col, "")).strip()
        if not hik_name:
            skipped += 1
            continue

        matched_emp = match_hikvision_to_employee(hik_name)
        if not matched_emp:
            if hik_name not in seen_unmatched:
                unmatched.append(hik_name)
                seen_unmatched.add(hik_name)
            skipped += 1
            continue

        # Parse date
        raw_date = str(row.get(date_col, "")).strip()
        try:
            if "T" in raw_date:
                att_date = raw_date.split("T")[0]
            else:
                att_date = raw_date[:10]
            # Validate
            datetime.strptime(att_date, "%Y-%m-%d")
        except Exception:
            skipped += 1
            continue

        # Parse time if available
        in_time = ""
        if time_col and time_col in row:
            raw_time = str(row[time_col]).strip()
            try:
                if "T" in raw_time:
                    in_time = raw_time.split("T")[1][:5]
                elif ":" in raw_time:
                    in_time = raw_time[:5]
            except Exception:
                pass

        ok, _ = db.add_attendance(
            matched_emp, att_date, in_time, "", "Present",
            "Imported from HikVision"
        )
        if ok:
            imported += 1
        else:
            skipped += 1

    return imported, skipped, unmatched
