import hashlib
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, json, base64
from datetime import datetime
from uuid import uuid4

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
DATA_FILE = 'data.json'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 初始化空資料檔案
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)

@app.route('/api/save', methods=['POST'])
def save_data():
    data = request.json
    for task in data:
        for entry in task.get("timeline", []):
            new_images = []
            for image in entry.get("images", []):
                if image["src"].startswith("data:image"):
                    base64_data = image["src"].split(",")[1]

                    # ✅ 建立圖片唯一的雜湊值
                    image_hash = hashlib.md5(base64_data.encode()).hexdigest()
                    filename = f"{image_hash}.png"
                    filepath = os.path.join(UPLOAD_FOLDER, filename)

                    # ✅ 如果圖片不存在才寫入
                    if not os.path.exists(filepath):
                        with open(filepath, "wb") as f:
                            f.write(base64.b64decode(base64_data))

                    full_url = request.host_url.rstrip('/') + f'/uploads/{filename}'
                    new_images.append({"id": image["id"], "src": full_url})
                else:
                    new_images.append(image)
            entry["images"] = new_images

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return jsonify({"status": "saved"})

@app.route('/api/load', methods=['GET'])
def load_data():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return jsonify(data)

@app.route('/api/delete', methods=['POST'])
def delete_data():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)
    return jsonify({"status": "cleared"})

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
