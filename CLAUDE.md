# CLAUDE.md

このファイルは、Claude Code (claude.ai/code) がこのリポジトリで作業する際のガイダンスを提供します。

## プロジェクト概要

Oura Ring API v2 から毎日の健康スコア（Readiness・Sleep・Activity）を取得し、Notion データベースへ upsert する単一ファイルの Python スクリプト。GitHub Actions で毎日自動実行される。

## スクリプトの実行方法

```bash
pip install requests
OURA_ACCESS_TOKEN=... NOTION_TOKEN=... NOTION_DATABASE_ID=... python oura_to_notion.py
```

テスト・リンター設定・`requirements.txt` はなく、依存パッケージは `requests` のみ。

## 必要な環境変数

| 変数名 | 説明 |
|---|---|
| `OURA_ACCESS_TOKEN` | Oura 開発者ポータルで発行した個人アクセストークン |
| `NOTION_TOKEN` | Notion インテグレーショントークン |
| `NOTION_DATABASE_ID` | 同期先 Notion データベースの ID |

本番環境では GitHub Actions の Secrets として設定する。

## アーキテクチャ

すべてのロジックは `oura_to_notion.py` 1 ファイルに集約されている。データの流れは以下の通り：

1. **Oura API v2** (`/v2/usercollection/{endpoint}`) — `daily_readiness`・`daily_sleep`・`daily_activity` の 3 エンドポイントを呼び出す。`start_date == end_date` で 1 日分を指定。
2. **8 日間の遡り取得** — Oura のスコアは遅延投稿されることがあるため、JST（UTC+9）の今日から 7 日前まで計 8 日分をループ処理する。
3. **Notion upsert** — 各日付について `Date` プロパティで DB を検索し、既存ページがあれば PATCH で更新、なければ新規作成。3 スコアすべて `None` の場合はスキップ。

### Notion データベーススキーマ

スクリプトが書き込む 5 つのプロパティ（Notion DB 側に事前に作成が必要）：

| プロパティ名 | Notion の型 |
|---|---|
| `Name` | title |
| `Date` | date |
| `Readiness` | number |
| `Sleep` | number |
| `Activity` | number |

## GitHub Actions ワークフロー

`.github/workflows/sync.yml` のトリガー：
- **スケジュール**: `0 21 * * *` UTC = JST 06:00（睡眠データが出揃う朝に実行）
- **手動**: `workflow_dispatch`

ワークフローはリポジトリをチェックアウトし、Python と `requests` をインストールしたうえで、3 つの Secrets を環境変数として注入してスクリプトを実行する。
