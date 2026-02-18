import os
import requests
from datetime import datetime, timedelta

OURA_ACCESS_TOKEN = os.getenv("OURA_ACCESS_TOKEN")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

def get_oura_data(endpoint, start_date, end_date):
    url = f"https://api.ouraring.com/v2/usercollection/{endpoint}"
    headers = {"Authorization": f"Bearer {OURA_ACCESS_TOKEN}"}
    params = {"start_date": start_date, "end_date": end_date}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        print(response.text)
        return []

def update_notion(date_str, readiness, sleep, activity):
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    query_url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"

    query_payload = {
        "filter": {
            "property": "Date",
            "date": {"equals": date_str}
        }
    }

    query_res = requests.post(query_url, headers=headers, json=query_payload)

    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Name": {"title": [{"text": {"content": f"Oura Score {date_str}"}}]},
            "Date": {"date": {"start": date_str}},
            "Readiness": {"number": readiness},
            "Sleep": {"number": sleep},
            "Activity": {"number": activity}
        }
    }

    if query_res.status_code == 200 and query_res.json().get("results"):
        page_id = query_res.json()["results"][0]["id"]
        update_url = f"https://api.notion.com/v1/pages/{page_id}"
        del payload["parent"]
        requests.patch(update_url, headers=headers, json=payload)
    else:
        create_url = "https://api.notion.com/v1/pages"
        requests.post(create_url, headers=headers, json=payload)

def main():
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    readiness = get_oura_data("daily_readiness", yesterday, yesterday)
    sleep = get_oura_data("daily_sleep", yesterday, yesterday)
    activity = get_oura_data("daily_activity", yesterday, yesterday)

    readiness_score = readiness[0].get("score") if readiness else None
    sleep_score = sleep[0].get("score") if sleep else None
    activity_score = activity[0].get("score") if activity else None

    if readiness_score or sleep_score or activity_score:
        update_notion(yesterday, readiness_score, sleep_score, activity_score)

if __name__ == "__main__":
    main()
