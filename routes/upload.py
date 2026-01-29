# routes/upload.py
from flask import Blueprint, request, jsonify, current_app
import os
import uuid
from werkzeug.utils import secure_filename
import pandas as pd

upload_bp = Blueprint('upload', __name__)

@upload_bp.route("/api/upload", methods=["POST"])
def api_upload():
    if 'file' not in request.files:
        return jsonify({"error": "Không có file"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Tên file rỗng"}), 400

    try:
        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1].lower()
        
        # Tạo tên file ngẫu nhiên để tránh trùng
        new_name = f"{uuid.uuid4().hex}{ext}"
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], new_name)
        
        file.save(save_path)
        
        # Đọc thử để lấy danh sách cột gửi về cho Frontend
        cols = []
        if ext == '.csv':
            df = pd.read_csv(save_path, nrows=0) # Chỉ đọc header cho nhanh
        else:
            df = pd.read_excel(save_path, engine='openpyxl', nrows=0)
        
        cols = df.columns.tolist()

        return jsonify({
            "message": "Upload thành công",
            "dataset_id": new_name,
            "original_filename": filename,
            "columns": cols
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500