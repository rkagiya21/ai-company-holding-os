import os, json, logging
from flask import Flask, request, jsonify
from functools import wraps
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from github import Github, GithubException
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GITHUB_TOKEN   = os.environ.get('GITHUB_TOKEN', '')
GITHUB_REPO    = os.environ.get('GITHUB_REPO', 'rkagiya21/ai-company-holding-os')
SUPABASE_URL   = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY   = os.environ.get('SUPABASE_SERVICE_KEY', '')
AGENT_API_KEY  = os.environ.get('AGENT_API_KEY', 'secret-key-change-me')

gh   = Github(GITHUB_TOKEN) if GITHUB_TOKEN else None
try:
        supa = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
except Exception as _e:
        logger.warning(f"Supabase init: {_e}")
        supa = None

@tool
def github_read_file(file_path: str) -> str:
    """GitHubリポジトリのファイルを読み込む。"""
    try:
        repo = gh.get_repo(GITHUB_REPO)
        c = repo.get_contents(file_path)
        return c.decoded_content.decode('utf-8')
    except GithubException as e:
        return f'[Error] {e}'

@tool
def github_write_file(file_path: str, new_content: str, commit_message: str) -> str:
    """GitHubリポジトリのファイルを更新してCommit&Pushする。"""
    try:
        repo = gh.get_repo(GITHUB_REPO)
        try:
            ex = repo.get_contents(file_path)
            repo.update_file(file_path, commit_message, new_content, ex.sha, branch='main')
            return f'[OK] Updated {file_path}'
        except GithubException:
            repo.create_file(file_path, commit_message, new_content, branch='main')
            return f'[OK] Created {file_path}'
    except GithubException as e:
        return f'[Error] {e}'

@tool
def github_list_files(directory: str = '') -> str:
    """GitHubリポジトリのディレクトリ一覧を取得する。"""
    try:
        repo = gh.get_repo(GITHUB_REPO)
        items = [f"{'[DIR]' if c.type=='dir' else '[FILE]'} {c.path}" for c in repo.get_contents(directory)]
        return '\n'.join(items)
    except GithubException as e:
        return f'[Error] {e}'

@tool
def supabase_query(table: str, filters: str = '', limit: int = 20) -> str:
    """Supabaseのテーブルからデータを取得する。"""
    try:
        q = supa.table(table).select('*').limit(limit)
        if filters:
            for k, v in json.loads(filters).items():
                q = q.eq(k, v)
        return json.dumps(q.execute().data, ensure_ascii=False, indent=2)
    except Exception as e:
        return f'[Error] {e}'

@tool
def supabase_execute_sql(sql: str) -> str:
    """SupabaseでSQLを直接実行する。"""
    try:
        return json.dumps(supa.rpc('execute_sql', {'query': sql}).execute().data, ensure_ascii=False, indent=2)
    except Exception as e:
        return f'[Error] {e}'

@tool
def supabase_update_record(table: str, record_id: str, updates: str) -> str:
    """Supabaseのレコードを更新する。"""
    try:
        return json.dumps(supa.table(table).update(json.loads(updates)).eq('id', record_id).execute().data, ensure_ascii=False, indent=2)
    except Exception as e:
        return f'[Error] {e}'

def build_agent():
    llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash', google_api_key=GEMINI_API_KEY, temperature=0.1)
    tools = [github_read_file, github_write_file, github_list_files, supabase_query, supabase_execute_sql, supabase_update_record]
    prompt = ChatPromptTemplate.from_messages([
        ('system', 'あなたはAI Company OSの自律エージェントです。GitHub(rkagiya21/ai-company-holding-os)とSupabaseを操作できます。KAMUI(backup-2026-03-12-gacha-working)は絶対に触れない。日時:{current_time}'),
        MessagesPlaceholder(variable_name='chat_history', optional=True),
        ('human', '{input}'),
        MessagesPlaceholder(variable_name='agent_scratchpad'),
    ])
    return AgentExecutor(agent=create_tool_calling_agent(llm, tools, prompt), tools=tools, verbose=True, max_iterations=10, handle_parsing_errors=True)

app = Flask(__name__)
agent_executor = build_agent()

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('X-API-Key') or request.args.get('api_key')
        if key != AGENT_API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'github': bool(gh), 'supabase': bool(supa)})

@app.route('/agent', methods=['POST'])
@require_api_key
def run_agent():
    data = request.get_json()
    instruction = data.get('instruction', '')
    if not instruction:
        return jsonify({'error': 'instruction required'}), 400
    try:
        result = agent_executor.invoke({'input': instruction, 'current_time': datetime.now().strftime('%Y-%m-%d %H:%M JST')})
        return jsonify({'status': 'success', 'output': result.get('output', '')})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/webhook/line', methods=['POST'])
def line_webhook():
    for event in request.get_json().get('events', []):
        if event.get('type') != 'message':
            continue
        text = event.get('message', {}).get('text', '')
        if not text.startswith('AI:'):
            continue
        try:
            agent_executor.invoke({'input': text[3:].strip(), 'current_time': datetime.now().strftime('%Y-%m-%d %H:%M JST')})
        except Exception as e:
            logger.error(f'[Agent] {e}')
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
