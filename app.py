# from flask import Flask, request, jsonify, send_from_directory
# from flask_cors import CORS
# import os
# import json

# app = Flask(__name__)
# CORS(app)

# DATA_FOLDER = 'data'
# os.makedirs(DATA_FOLDER, exist_ok=True)

# def get_user_file(username):
#     safe_name = username.replace("/", "_").replace("\\", "_")
#     return os.path.join(DATA_FOLDER, f"user_{safe_name}.json")

# # 🔹 登入（只是回傳成功，前端自行記錄 username）
# @app.route('/api/login', methods=['POST'])
# def login():
#     data = request.get_json()
#     username = data.get('username')
#     if not username:
#         return jsonify({"success": False, "message": "缺少使用者名稱"}), 400
#     return jsonify({"success": True})

# # 🔹 讀取使用者留言資料
# @app.route('/api/load/<username>', methods=['GET'])
# def load_data(username):
#     file_path = get_user_file(username)
#     if os.path.exists(file_path):
#         with open(file_path, 'r', encoding='utf-8') as f:
#             return jsonify(json.load(f))
#     else:
#         return jsonify([])  # 回傳空列表

# # 🔹 儲存留言資料
# @app.route('/api/save/<username>', methods=['POST'])
# def save_data(username):
#     file_path = get_user_file(username)
#     data = request.get_json()
#     with open(file_path, 'w', encoding='utf-8') as f:
#         json.dump(data, f, ensure_ascii=False, indent=2)
#     return jsonify({"success": True})

# # 🔹 刪除該使用者留言資料
# @app.route('/api/delete/<username>', methods=['POST'])
# def delete_data(username):
#     file_path = get_user_file(username)
#     if os.path.exists(file_path):
#         os.remove(file_path)
#         return jsonify({"success": True, "message": "資料已刪除"})
#     return jsonify({"success": False, "message": "檔案不存在"}), 404

# # 🔹 前端 index.html 測試用途（可選）
# @app.route('/')
# def index():
#     return send_from_directory('static', 'index.html')

# if __name__ == '__main__':
#     app.run(debug=True)


from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sqlite3

app = Flask(__name__)
CORS(app)

DATA_FOLDER = 'data'
os.makedirs(DATA_FOLDER, exist_ok=True)

def get_user_db(username):
    safe_name = username.replace("/", "_").replace("\\", "_")
    return os.path.join(DATA_FOLDER, f"user_{safe_name}.db")

def init_user_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            title TEXT,
            sort_order INTEGER
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS timeline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            html TEXT,
            raw_html TEXT,
            timestamp TEXT,
            FOREIGN KEY(task_id) REFERENCES tasks(id)
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    if not username:
        return jsonify({"success": False, "message": "缺少使用者名稱"}), 400

    db_path = get_user_db(username)
    init_user_db(db_path)
    return jsonify({"success": True})

@app.route('/api/load/<username>', methods=['GET'])
def load_data(username):
    db_path = get_user_db(username)
    if not os.path.exists(db_path):
        return jsonify([])

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # c.execute('SELECT id, title FROM tasks')
    c.execute('SELECT id, title FROM tasks ORDER BY sort_order ASC')
    tasks = []
    for task_id, title in c.fetchall():
        c.execute('''
            SELECT html, raw_html, timestamp
            FROM timeline
            WHERE task_id = ?
            ORDER BY rowid DESC
        ''', (task_id,))
        timeline = [
            {
                "html": html,
                "rawHtml": raw_html,
                "timestamp": timestamp,
                "isEditing": False,
                "editRef": None
            }
            for html, raw_html, timestamp in c.fetchall()
        ]
        tasks.append({"id": task_id, "title": title, "timeline": timeline})
    conn.close()
    return jsonify(tasks)


@app.route('/api/save/<username>', methods=['POST'])
def save_data(username):
    db_path = get_user_db(username)
    data = request.get_json()
    init_user_db(db_path)

    conn = sqlite3.connect(db_path, timeout=5)
    c = conn.cursor()
    c.execute('DELETE FROM timeline')
    c.execute('DELETE FROM tasks')

    # for task in data:
    #     c.execute('INSERT INTO tasks (title) VALUES (?)', (task['title'],))
    #     task_id = c.lastrowid

    #     # 🔄 這邊反轉 timeline 儲存順序（讓最新的3先寫入）
    #     for entry in reversed(task.get('timeline', [])):
    #         c.execute('''
    #             INSERT INTO timeline (task_id, html, raw_html, timestamp)
    #             VALUES (?, ?, ?, ?)
    #         ''', (task_id, entry['html'], entry.get('rawHtml', entry['html']), entry['timestamp']))

    for idx, task in enumerate(data):  # 👈 多了 idx 代表順序
        c.execute('INSERT INTO tasks (title, sort_order) VALUES (?, ?)', (task['title'], idx))
        task_id = c.lastrowid
        for entry in reversed(task.get('timeline', [])):
            c.execute('''
                INSERT INTO timeline (task_id, html, raw_html, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (task_id, entry['html'], entry.get('rawHtml', entry['html']), entry['timestamp']))


    conn.commit()
    conn.close()
    return jsonify({"success": True})



@app.route('/api/delete/<username>', methods=['POST'])
def delete_data(username):
    db_path = get_user_db(username)
    if os.path.exists(db_path):
        os.remove(db_path)
        return jsonify({"success": True, "message": "資料庫已刪除"})
    return jsonify({"success": False, "message": "資料庫不存在"}), 404

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    app.run(debug=True)
