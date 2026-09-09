import os
import json
import uuid
from flask import Blueprint, request, jsonify

evaluation_bp = Blueprint('evaluation', __name__)

BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, 'data')

COUNCILS_FILE = os.path.join(DATA_DIR, 'councils.json')
RUBRICS_FILE = os.path.join(DATA_DIR, 'rubrics.json')

def read_json(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except:
            return []

def write_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@evaluation_bp.route('/api/councils', methods=['POST'])
def create_council():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Không có dữ liệu JSON được gửi lên"}), 400
            
        councils = read_json(COUNCILS_FILE)
        
        new_council = {
            "id": str(uuid.uuid4()),
            "name": data.get("name", "Hội đồng chưa đặt tên"),
            "members": data.get("members", [])
        }
        
        councils.append(new_council)
        write_json(COUNCILS_FILE, councils)
        
        return jsonify({
            "success": True, 
            "message": "Tạo hội đồng thành công", 
            "data": new_council
        }), 201
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi server: {str(e)}"}), 500

@evaluation_bp.route('/api/rubrics', methods=['PUT'])
def update_rubric():
    try:
        data = request.get_json()
        if not data or 'id' not in data:
            return jsonify({"success": False, "message": "Vui lòng cung cấp JSON có chứa trường 'id' của rubric"}), 400
            
        rubrics = read_json(RUBRICS_FILE)
        rubric_id = data['id']
        
        updated = False
        for i, rubric in enumerate(rubrics):
            if rubric.get('id') == rubric_id:
                rubrics[i].update(data) 
                updated = True
                break
        
        if not updated:
            rubrics.append(data)
            
        write_json(RUBRICS_FILE, rubrics)
        
        return jsonify({
            "success": True, 
            "message": "Cập nhật Rubric thành công", 
            "data": data
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi server: {str(e)}"}), 500