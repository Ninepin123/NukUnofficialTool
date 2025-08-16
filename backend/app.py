# app.py - 高雄大學學分分析與排課系統
import os
import sys
import time
import json
import logging
import webbrowser
import threading
from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def get_resource_path(relative_path):
    """獲取資源檔案的正確路徑，支援PyInstaller打包後的環境"""
    try:
        # PyInstaller 打包後的路徑
        base_path = sys._MEIPASS
    except Exception:
        # 開發環境的路徑
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# 導入課程系統模組
from modules.course_system.fetcher import fetch_course_update_from_nuk

# 導入學分系統模組
from modules.credit_system.scraper import run_selenium_process

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATA_FILE = get_resource_path('data/courses_final.json')
CACHE_TTL = 600  # Cache duration in seconds (10 minutes)
LOCK_TTL = 30    # Lock duration in seconds

app = Flask(__name__, 
            static_folder=get_resource_path('frontend'), 
            template_folder=get_resource_path('frontend'))
CORS(app)

# Rate limiter
limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["200 per hour"])

# --- In-Memory Cache and Lock Implementation ---
MEMORY_CACHE = {}
MEMORY_LOCKS = {}

def cache_get(key):
    """Gets a value from the in-memory cache if it's not expired."""
    if key in MEMORY_CACHE and (time.time() - MEMORY_CACHE[key]['timestamp']) < CACHE_TTL:
        return MEMORY_CACHE[key]['data']
    return None

def cache_set(key, value, ttl=CACHE_TTL):
    """Sets a value in the in-memory cache with a timestamp."""
    MEMORY_CACHE[key] = {'data': value, 'timestamp': time.time()}

def acquire_lock(lock_key, ttl=LOCK_TTL):
    """Acquires a simple in-memory lock."""
    if lock_key in MEMORY_LOCKS and (time.time() - MEMORY_LOCKS[lock_key]) < ttl:
        return False  # Lock is active
    MEMORY_LOCKS[lock_key] = time.time()
    return True

def release_lock(lock_key):
    """Releases an in-memory lock."""
    if lock_key in MEMORY_LOCKS:
        del MEMORY_LOCKS[lock_key]

# --- 課程系統 API Endpoints ---
@app.route('/api/courses', methods=['GET'])
def api_courses():
    """獲取課程列表"""
    if not os.path.exists(DATA_FILE):
        return jsonify({"error": f"Data file '{DATA_FILE}' not found."}), 404
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))

@app.route('/api/course-update', methods=['GET'])
@limiter.limit("10 per minute")
def api_course_update():
    """更新課程資訊"""
    year, semester, sclass, cono = request.args.get('year'), request.args.get('helf'), request.args.get('sclass'), request.args.get('cono')
    if not all([year, semester, sclass, cono]):
        return jsonify({"error": "Missing required query parameters."}), 400

    cache_key = f"course:{year}:{semester}:{sclass}:{cono}"
    lock_key = f"lock:{cache_key}"

    cached = cache_get(cache_key)
    if cached:
        logger.info(f"[CACHE HIT] Serving from memory for {cache_key}")
        return jsonify(cached)

    if not acquire_lock(lock_key):
        logger.info(f"[WAIT] Another process is fetching {cache_key}. Waiting briefly.")
        time.sleep(1)
        cached = cache_get(cache_key)
        if cached:
            logger.info(f"[WAIT HIT] {cache_key}")
            return jsonify(cached)
        return jsonify({"error": "Data not available after waiting, please try again."}), 503

    try:
        logger.info(f"[FETCH] Fetching {cache_key} from NUK site")
        result = fetch_course_update_from_nuk(year=year, semester=semester, sclass=sclass, cono=cono)
        if result is None:
            return jsonify({"error": f"Course {cono} not found or fetch failed."}), 404
        
        cache_set(cache_key, result, ttl=CACHE_TTL)
        return jsonify(result)
    except Exception:
        logger.exception("Error while fetching course update")
        return jsonify({"error": "Internal server error during fetch."}), 500
    finally:
        release_lock(lock_key)

# --- 學分系統 API Endpoints ---
@app.route('/api/start-credit-analysis', methods=['POST'])
def api_start_credit_analysis():
    """啟動學分分析流程"""
    print("收到前端請求，準備開始學分分析流程...")
    result = run_selenium_process()
    return jsonify(result)

# --- 主頁面路由 ---
@app.route('/')
def index():
    """主頁面"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    """靜態檔案代理"""
    return send_from_directory(app.static_folder, path)

def open_browser(port):
    """延遲開啟瀏覽器"""
    time.sleep(1.5)  # 等待Flask伺服器完全啟動
    webbrowser.open(f'http://localhost:{port}')

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() in ('1', 'true')
    
    # 在背景執行緒中開啟瀏覽器
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    
    app.run(host='0.0.0.0', port=port, debug=debug)