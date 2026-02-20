import os
import sys
import requests
from datetime import datetime, timedelta

OURA_ACCESS_TOKEN = os.getenv("OURA_ACCESS_TOKEN")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")


def die(msg: str) -> None:
    print(msg)
    sys.exit(1)


def must(value, msg: str) -> None:
    if not value:
        die(msg)


def get_oura_data(endpoint: str, date_str: str):
    url = f"https://api.ouraring.com/v2/usercollection/{endpoint}"
    headers = {"Authorization": f"Bearer {OURA_ACCESS_TOKEN}"}
    params = {"start_date": date_str, "end_date": date_str}

    r = requests.get(url, headers=headers, params=params)
    if r.status_code != 200:
        die(f"[OURA] {endpoint} failed: {r.status_code} {r.text}")

    return r.json().get("data", [])


def notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }


def upsert_notion(date_str: str, readiness, sleep, activity) -> None:
    headers = notion_headers()

    # 既存検索（Date が同じ行があれば更新）
    query_url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    query_payload = {"filter": {"property": "Date", "date": {"equals": date_str}}}

    q = requests.post(query_url, headers=headers, json=query_payload)
    if q.status_code != 200:
        die(f"[NOTION] query failed: {q.status_code} {q.text}")

    props = {
        "Name": {"title": [{"text": {"content": f"Oura Score {date_str}"}}]},
        "Date": {"date": {"start": date_str}},
        "Readiness": {"number": readiness},
        "Sleep": {"number": sleep},
        "Activity": {"number": activity},
    }

    results = q.json().get("results", [])

    if results:
        # 更新
        page_id = results[0]["id"]
        update_url = f"https://api.notion.com/v1/pages/{page_id}"
        r = requests.patch(update_url, headers=headers, json={"properties": props})
        if r.status_code != 200:
            die(f"[NOTION] update failed: {r.status_code} {r.text}")
        print(f"Updated {date_str} page_id={page_id}")
    else:
        # 新規作成
        create_url = "https://api.notion.com/v1/pages"
        payload = {"parent": {"database_id": NOTION_DATABASE_ID}, "properties": props}
        r = requests.post(create_url, headers=headers, json=payload)
        if r.status_code not in (200, 201):
            die(f"[NOTION] create failed: {r.status_code} {r.text}")
        page_id = r.json().get("id")
        print(f"Created {date_str} page_id={page_id}")


def main() -> None:
    must(OURA_ACCESS_TOKEN, "Missing OURA_ACCESS_TOKEN")
    must(NOTION_TOKEN, "Missing NOTION_TOKEN")
    must(NOTION_DATABASE_ID, "Missing NOTION_DATABASE_ID")

    print(f"Using Notion DB: {NOTION_DATABASE_ID}")

    # 直近7日ぶんを毎回同期（歯抜け回収＆取りこぼし耐性）
    for i in range(1, 8):
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        print(f"Fetching data for {day}...")

        readiness = get_oura_data("daily_readiness", day)
        sleep = get_oura_data("daily_sleep", day)
        activity = get_oura_data("daily_activity", day)

        readiness_score = readiness[0].get("score") if readiness else None
        sleep_score = sleep[0].get("score") if sleep else None
        activity_score = activity[0].get("score") if activity else None

        if readiness_score is None and sleep_score is None and activity_score is None:
            print(f"No data for {day}")
            continue

        upsert_notion(day, readiness_score, sleep_score, activity_score)

    print("Done")


if __name__ == "__main__":
    main()
