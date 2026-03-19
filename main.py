# AI Company OS v5.0 - Autonomous Agent System

# Gemini脳 + GitHub/Supabase/Drive手足による自律型AIエージェント

import os
import json
import logging
from datetime import datetime
from functools import wraps
from typing import Dict, Any, List

from flask import Flask, request, jsonify

# Google Generative AI

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# GitHub操作

from github import Github, GithubException

# Supabase操作

from supabase import create_client, Client

# Google Drive操作

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# ===== 設定とロギング =====

logging.basicConfig(level=logging.INFO, format=”%(asctime)s [%(levelname)s] %(message)s”)
logger = logging.getLogger(**name**)

# ===== 環境変数読み込み =====

GOOGLE_API_KEY = os.environ.get(“GOOGLE_API_KEY”, “”)
GITHUB_TOKEN = os.environ.get(“GITHUB_TOKEN”, “”)
GITHUB_REPO = os.environ.get(“GITHUB_REPO”, “rkagiya21/ai-company-holding-os”)
SUPABASE_URL = os.environ.get(“SUPABASE_URL”, “”)
SUPABASE_KEY = os.environ.get(“SUPABASE_KEY”, “”)
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get(“LINE_CHANNEL_ACCESS_TOKEN”, “”)
GOOGLE_DRIVE_SERVICE_ACCOUNT = os.environ.get(“GOOGLE_DRIVE_SERVICE_ACCOUNT”, “”)
AGENT_API_KEY = os.environ.get(“AGENT_API_KEY”, “ai-company-os-secret-key”)

# ===== クライアント初期化 =====

gh = Github(GITHUB_TOKEN) if GITHUB_TOKEN else None

supa: Client = None
if SUPABASE_URL and SUPABASE_KEY:
try:
supa = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
logger.error(f”Supabase initialization failed: {e}”)

drive_service = None
if GOOGLE_DRIVE_SERVICE_ACCOUNT:
try:
service_account_info = json.loads(GOOGLE_DRIVE_SERVICE_ACCOUNT)
credentials = Credentials.from_service_account_info(
service_account_info, scopes=[‘https://www.googleapis.com/auth/drive’]
)
drive_service = build(‘drive’, ‘v3’, credentials=credentials)
logger.info(“Google Drive initialized”)
except Exception as e:
logger.error(f”Google Drive initialization failed: {e}”)

# ═══════════════════════════════════════════════════════════

# 🔧 GitHub ツール群

# ═══════════════════════════════════════════════════════════

@tool
def github_read_file(file_path: str) -> str:
“””
GitHubリポジトリの指定ファイルを読み込む。
Args:
file_path: リポジトリ内のファイルパス（例: “AI/bot.py”）
Returns:
ファイルの内容（文字列）
“””
if not gh:
return “[Error] GitHub client not initialized”
try:
repo = gh.get_repo(GITHUB_REPO)
content = repo.get_contents(file_path)
return content.decoded_content.decode(“utf-8”)
except GithubException as e:
return f”[Error] GitHub read failed: {e}”

@tool
def github_write_file(file_path: str, new_content: str, commit_message: str) -> str:
“””
GitHubリポジトリの指定ファイルを更新してCommit & Pushする。
Args:
file_path: リポジトリ内のファイルパス（例: “AI/bot.py”）
new_content: 書き込む新しいファイル内容（全文）
commit_message: コミットメッセージ
Returns:
成功 or エラーメッセージ
“””
if not gh:
return “[Error] GitHub client not initialized”
try:
repo = gh.get_repo(GITHUB_REPO)
try:
existing = repo.get_contents(file_path)
repo.update_file(
path=file_path,
message=commit_message,
content=new_content,
sha=existing.sha,
branch=“main”
)
return f”[OK] Updated {file_path}: {commit_message}”
except GithubException:
repo.create_file(
path=file_path,
message=commit_message,
content=new_content,
branch=“main”
)
return f”[OK] Created {file_path}: {commit_message}”
except GithubException as e:
return f”[Error] GitHub write failed: {e}”

@tool
def github_list_files(directory: str = “”) -> str:
“””
GitHubリポジトリの指定ディレクトリのファイル一覧を取得する。
Args:
directory: ディレクトリパス（空文字でルート）
Returns:
ファイル/ディレクトリ名の一覧
“””
if not gh:
return “[Error] GitHub client not initialized”
try:
repo = gh.get_repo(GITHUB_REPO)
contents = repo.get_contents(directory)
items = [f”{’[DIR]’ if c.type == ‘dir’ else ‘[FILE]’} {c.path}” for c in contents]
return “\n”.join(items)
except GithubException as e:
return f”[Error] GitHub list failed: {e}”

# ═══════════════════════════════════════════════════════════

# 🗄️ Supabase ツール群

# ═══════════════════════════════════════════════════════════

@tool
def supabase_query(table: str, filters: str = “”, limit: int = 20) -> str:
“””
Supabaseの指定テーブルからデータを取得する。
Args:
table: テーブル名（例: “user_items”, “gacha_history”）
filters: フィルタ条件（JSON形式、例: ‘{“status”: “pending”}’）
limit: 取得件数の上限（デフォルト20）
Returns:
取得したレコードのJSON文字列
“””
if not supa:
return “[Error] Supabase client not initialized”
try:
query = supa.table(table).select(”*”).limit(limit)
if filters:
f = json.loads(filters)
for k, v in f.items():
query = query.eq(k, v)
result = query.execute()
return json.dumps(result.data, ensure_ascii=False, indent=2)
except Exception as e:
return f”[Error] Supabase query failed: {e}”

@tool
def supabase_execute_sql(sql: str) -> str:
“””
SupabaseでSQLを直接実行してデータを修正・参照する。
Args:
sql: 実行するSQL文（SELECT / UPDATE / INSERT / DELETE）
Returns:
実行結果のJSON文字列
“””
if not supa:
return “[Error] Supabase client not initialized”
try:
result = supa.rpc(“execute_sql”, {“query”: sql}).execute()
return json.dumps(result.data, ensure_ascii=False, indent=2)
except Exception as e:
return f”[Error] SQL execution failed: {e}”

@tool
def supabase_update_record(table: str, record_id: str, updates: str) -> str:
“””
Supabaseの指定テーブルの1レコードを更新する。
Args:
table: テーブル名
record_id: 更新対象レコードのID
updates: 更新するカラムとその値のJSON文字列（例: ‘{“status”: “fixed”}’）
Returns:
更新結果のJSON文字列
“””
if not supa:
return “[Error] Supabase client not initialized”
try:
data = json.loads(updates)
result = supa.table(table).update(data).eq(“id”, record_id).execute()
return json.dumps(result.data, ensure_ascii=False, indent=2)
except Exception as e:
return f”[Error] Supabase update failed: {e}”

# ═══════════════════════════════════════════════════════════

# 🧠 Geminiエージェント構築

# ═══════════════════════════════════════════════════════════

def build_agent() -> AgentExecutor:
“”“Gemini + ツール群でエージェントを構築して返す”””

```
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.1,
)

tools = [
    github_read_file,
    github_write_file,
    github_list_files,
    supabase_query,
    supabase_execute_sql,
    supabase_update_record,
]

prompt = ChatPromptTemplate.from_messages([
    ("system", """あなたはAI Company OSの自律エージェントです。
```

GitHub（rkagiya21/ai-company-holding-os）とSupabaseを操作する「手足」を持っています。

【担当業務】

- Kindle自動出版パイプラインの保守・改善
- KAMUI オリパサイトのバグ修正・DB整合性確保
- コードの読み込み・修正・コミット

【行動原則】

- まず現状を確認してから変更を加える
- Supabaseの変更はSELECTで確認後に実行する
- コミットメッセージは日本語で簡潔に書く
- KAMUI（backup-2026-03-12-gacha-working）は絶対に触れない

現在の日時: {current_time}
“””),
MessagesPlaceholder(variable_name=“chat_history”, optional=True),
(“human”, “{input}”),
MessagesPlaceholder(variable_name=“agent_scratchpad”),
])

```
agent = create_tool_calling_agent(llm, tools, prompt)

return AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=10,
    handle_parsing_errors=True,
)
```

# ═══════════════════════════════════════════════════════════

# 🌐 Flask APIサーバー

# ═══════════════════════════════════════════════════════════

app = Flask(**name**)
agent_executor = None

def require_api_key(f):
“”“APIキー認証デコレーター”””
@wraps(f)
def decorated(*args, **kwargs):
key = request.headers.get(“X-API-Key”) or request.args.get(“api_key”)
if key != AGENT_API_KEY:
return jsonify({“error”: “Unauthorized”}), 401
return f(*args, **kwargs)
return decorated

@app.route(”/health”, methods=[“GET”])
def health():
“”“ヘルスチェック”””
return jsonify({
“status”: “ok”,
“github”: “connected” if gh else “not configured”,
“supabase”: “connected” if supa else “not configured”,
“drive”: “connected” if drive_service else “not configured”,
})

@app.route(”/agent”, methods=[“POST”])
@require_api_key
def run_agent():
“””
エージェントへの指示エンドポイント
Body: {“instruction”: “AI/bot.pyを読んで、kindleコマンドの処理を確認して”}
“””
data = request.get_json()
instruction = data.get(“instruction”, “”)
if not instruction:
return jsonify({“error”: “instruction is required”}), 400

```
logger.info(f"[Agent] Instruction: {instruction}")

try:
    result = agent_executor.invoke({
        "input": instruction,
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M JST"),
    })
    return jsonify({
        "status": "success",
        "output": result.get("output", ""),
    })
except Exception as e:
    logger.error(f"[Agent] Error: {e}")
    return jsonify({"status": "error", "message": str(e)}), 500
```

@app.route(”/webhook/line”, methods=[“POST”])
def line_webhook():
“””
LINEからのWebhook経由でエージェントに指示を出す
メッセージ先頭が「AI:」の場合のみエージェントに転送
例: 「AI: bot.pyのkindleコマンドを修正して」
“””
body = request.get_json()
events = body.get(“events”, [])

```
for event in events:
    if event.get("type") != "message":
        continue
    text = event.get("message", {}).get("text", "")
    if not text.startswith("AI:"):
        continue

    instruction = text[3:].strip()
    logger.info(f"[LINE→Agent] {instruction}")

    try:
        result = agent_executor.invoke({
            "input": instruction,
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M JST"),
        })
        logger.info(f"[Agent Result] {result.get('output', '')[:200]}")
    except Exception as e:
        logger.error(f"[Agent] LINE webhook error: {e}")

return jsonify({"status": "ok"})
```

# ═══════════════════════════════════════════════════════════

# 🚀 起動

# ═══════════════════════════════════════════════════════════

def initialize():
global agent_executor
logger.info(“🚀 AI Company OS Agent起動中…”)
agent_executor = build_agent()
logger.info(“✅ Geminiエージェント初期化完了”)

if **name** == “**main**”:
initialize()
app.run(host=“0.0.0.0”, port=int(os.environ.get(“PORT”, 5000)))
else:
# Gunicorn起動時（Render）
initialize()
