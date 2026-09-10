from datetime import datetime
from flask import Blueprint, request, jsonify
from models import db, Progress 
progress_bp = Blueprint('progress', __name__)

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
        milestones_db = Progress.query.filter_by(topic_id=id).all()
        
        topic_progress = []
        for m in milestones_db:
            topic_progress.append({
                "id": m.id,
                "title": getattr(m, 'title', 'Cập nhật tiến độ'),
                "percentage": m.percentage,
                "note": getattr(m, 'note', ''),
                "created_at": m.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(m, 'created_at') and m.created_at else None
            })
            
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
        current_time = datetime.now()

        new_milestone = Progress(
            topic_id=id,
            title=title,
            percentage=percentage,
            note=note
        )
        
        if hasattr(new_milestone, 'created_at'):
            new_milestone.created_at = current_time

        db.session.add(new_milestone)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Cập nhật tiến độ thành công",
            "data": {
                "id": new_milestone.id,
                "title": title,
                "percentage": percentage,
                "note": note,
                "created_at": current_time.strftime("%Y-%m-%d %H:%M:%S")
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Lỗi server: {str(e)}"}), 500