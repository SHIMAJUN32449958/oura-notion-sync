import os
import requests
from datetime import datetime, timedelta

OURA_ACCESS_TOKEN = os.getenv("OURA_ACCESS_TOKEN")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

def get_oura_data(endpoint, date):
    url = f"https://api.ouraring.com/v2/usercollection/{endpoint}"
    headers = {"Authorization": f"Bearer {OURA_ACCESS_TOKEN}"}
    params = {"start_date": date, "end_date": date}

    res = requests.get(url, headers=headers, params=params)
    if res.status_code == 200:
        return res.json().get("data", [])
    else:
        print(res.text)
        return []

def update_notion(date, readiness, sleep, activity):
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    query_url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"

    query = {
        "filter": {
            "property": "Date",
            "date": {"equals": date}
        }
    }

    q = requests.post(query_url, headers=headers, json=query)

    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Name": {"title": [{"text": {"content": f"Oura Score {date}"}}]},
            "Date": {"date": {"start": date}},
            "Readiness": {"number": readiness},
            "Sleep": {"number": sleep},
            "Activity": {"number": activity}
        }
    }

    if q.status_code == 200 and q.json()["results"]:
        page_id = q.json()["results"][0]["id"]
        del payload["parent"]
        requests.patch(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=headers,
            json=payload,
        )
        print(f"Updated {date}")
    else:
        requests.post(
            "https://api.notion.com/v1/pages",
            headers=headers,
            json=payload,
        )
        print(f"Created {date}")

def main():
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"Fetching data for {yesterday}")

    readiness = get_oura_data("daily_readiness", yesterday)
    sleep = get_oura_data("daily_sleep", yesterday)
    activity = get_oura_data("daily_activity", yesterday)

    readiness_score = readiness[0]["score"] if readiness else None
    sleep_score = sleep[0]["score"] if sleep else None
    activity_score = activity[0]["score"] if activity else None

    if readiness_score or sleep_score or activity_score:
        update_notion(yesterday, readiness_score, sleep_score, activity_score)
    else:
        print("No data found")

if __name__ == "__main__":
    main()
