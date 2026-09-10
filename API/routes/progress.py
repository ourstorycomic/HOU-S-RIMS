import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify

progress_bp = Blueprint('progress', __name__)

BASE_DIR = os.getcwd()
PROGRESS_FILE = os.path.join(BASE_DIR, 'data', 'progress.json')

def read_progress():
    if not os.path.exists(PROGRESS_FILE):
        return {}
    with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except:
            return {}

def write_progress(data):
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@progress_bp.route('/api/topics/<id>/progress', methods=['GET'])
def get_topic_progress(id):
    """
    Lấy danh sách tiến độ đề tài
    ---
    tags:
      - Progress
    parameters:
      - in: path
        name: id
        type: string
        required: true
        description: ID của đề tài (VD: 1)
    responses:
      200:
        description: Thành công
    """
    try:
        all_data = read_progress()
        topic_progress = all_data.get(str(id), [])
        
        return jsonify({
            "success": True,
            "topic_id": id,
            "milestones": topic_progress
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi server: {str(e)}"}), 500

@progress_bp.route('/api/topics/<id>/progress', methods=['POST'])
def add_topic_progress(id):
    """
    Thêm mốc tiến độ mới
    ---
    tags:
      - Progress
    parameters:
      - in: path
        name: id
        type: string
        required: true
        description: ID của đề tài (VD: 1)
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
              example: "Nộp báo cáo giữa kỳ"
            percentage:
              type: integer
              example: 50
            note:
              type: string
              example: "Đã hoàn thành code backend"
    responses:
      201:
        description: Thêm thành công
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Không có dữ liệu gửi lên"}), 400
            
        title = data.get("title", "Cập nhật tiến độ")
        percentage = data.get("percentage", 0)  
        note = data.get("note", "")

        all_data = read_progress()
        topic_key = str(id)
        
        if topic_key not in all_data:
            all_data[topic_key] = []

        new_milestone = {
            "id": len(all_data[topic_key]) + 1,
            "title": title,
            "percentage": percentage,
            "note": note,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        all_data[topic_key].append(new_milestone)
        write_progress(all_data)

        return jsonify({
            "success": True,
            "message": "Cập nhật tiến độ thành công",
            "data": new_milestone
        }), 201
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi server: {str(e)}"}), 500