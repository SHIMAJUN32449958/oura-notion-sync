# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

A single-script Python tool that pulls daily health scores (Readiness, Sleep, Activity) from the Oura Ring API v2 and upserts them into a Notion database. It runs via GitHub Actions on a daily cron schedule.

## Running the script

```bash
pip install requests
OURA_ACCESS_TOKEN=... NOTION_TOKEN=... NOTION_DATABASE_ID=... python oura_to_notion.py
```

There are no tests, no linter configuration, and no `requirements.txt` — `requests` is the only dependency.

## Required environment variables

| Variable | Description |
|---|---|
| `OURA_ACCESS_TOKEN` | Personal access token from the Oura developer portal |
| `NOTION_TOKEN` | Notion integration token |
| `NOTION_DATABASE_ID` | ID of the target Notion database |

In production these are set as GitHub Actions secrets.

## Architecture

Everything lives in `oura_to_notion.py`. The data flow is:

1. **Oura API v2** (`/v2/usercollection/{endpoint}`) — fetched for `daily_readiness`, `daily_sleep`, `daily_activity` endpoints. `start_date == end_date` targets a single day.
2. **8-day lookback** — the script iterates today through 7 days ago (JST timezone, `UTC+9`) to catch scores that Oura posts with a delay.
3. **Notion upsert** — for each day, queries the database by `Date` property; patches the existing page if found, creates a new one otherwise. Skips a day entirely if all three scores are `None`.

### Notion database schema

The script writes these five properties (must exist in the Notion DB):

| Property | Notion type |
|---|---|
| `Name` | title |
| `Date` | date |
| `Readiness` | number |
| `Sleep` | number |
| `Activity` | number |

## GitHub Actions workflow

`.github/workflows/sync.yml` triggers on:
- **Cron**: `0 21 * * *` UTC = 06:00 JST (morning after overnight sleep data is available)
- **Manual**: `workflow_dispatch`

The workflow checks out the repo, installs Python + `requests`, and runs the script with the three secrets injected as environment variables.
