import uuid
import json
from flask import Blueprint, request, jsonify
from models import db, Council, Rubric

evaluation_bp = Blueprint('evaluation', __name__)

@evaluation_bp.route('/api/councils', methods=['POST'])
def create_council():
    """
    Tạo hội đồng đánh giá mới
    ---
    tags:
      - Evaluation
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              example: "Hội đồng 1"
            members:
              type: array
              items:
                type: string
              example: ["Thầy A", "Cô B"]
    responses:
      201:
        description: Tạo thành công
    """ 
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Không có dữ liệu JSON được gửi lên"}), 400
            
        council_id = str(uuid.uuid4())
        name = data.get("name", "Hội đồng chưa đặt tên")
        
        members = data.get("members", [])
        members_json = json.dumps(members, ensure_ascii=False)
        
        new_council = Council(
            id=council_id, 
            name=name,
            members=members_json
        )
        
        db.session.add(new_council)
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": "Tạo hội đồng thành công", 
            "data": {
                "id": council_id,
                "name": name,
                "members": members
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Lỗi server: {str(e)}"}), 500

@evaluation_bp.route('/api/rubrics', methods=['PUT'])
def update_rubric():
    """
    Cập nhật Rubric đánh giá
    ---
    tags:
      - Evaluation
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            id:
              type: string
              example: "rubric-001"
            criteria:
              type: array
              items:
                type: string
              example: ["Code: 7", "Trình bày: 3"]
    responses:
      200:
        description: Cập nhật thành công
    """
    try:
        data = request.get_json()
        if not data or 'id' not in data:
            return jsonify({"success": False, "message": "Vui lòng cung cấp JSON có chứa trường 'id' của rubric"}), 400
            
        rubric_id = data['id']
        criteria = data.get("criteria", [])
        criteria_json = json.dumps(criteria, ensure_ascii=False)
        
        rubric = Rubric.query.filter_by(id=rubric_id).first()
        
        if rubric:
            rubric.criteria = criteria_json
            for key, value in data.items():
                if hasattr(rubric, key) and key not in ['id', 'criteria']:
                    setattr(rubric, key, value)
        else:
            rubric = Rubric(id=rubric_id, criteria=criteria_json)
            for key, value in data.items():
                if hasattr(rubric, key) and key not in ['id', 'criteria']:
                    setattr(rubric, key, value)
            db.session.add(rubric)
            
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": "Cập nhật Rubric thành công", 
            "data": data
        }), 200
    except Exception as e:
        db.session.rollback() 
        return jsonify({"success": False, "message": f"Lỗi server: {str(e)}"}), 500