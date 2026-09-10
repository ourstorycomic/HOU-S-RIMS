import os
import json
from flask import Blueprint, jsonify

dashboard_bp = Blueprint('dashboard', __name__)

BASE_DIR = os.getcwd()
PROGRESS_FILE = os.path.join(BASE_DIR, 'data', 'progress.json')
COUNCILS_FILE = os.path.join(BASE_DIR, 'data', 'councils.json')

def read_json(filepath, default_val):
    if not os.path.exists(filepath):
        return default_val
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except:
            return default_val
@dashboard_bp.route('/api/dashboard/progress', methods=['GET'])
def get_dashboard_progress():
    """
    Lấy trung bình tiến độ các đề tài để vẽ biểu đồ
    ---
    tags:
      - Dashboard
    responses:
      200:
        description: Thành công
    """
    try:
        progress_data = read_json(PROGRESS_FILE, {})
        topic_summaries = []
        
        for topic_id, milestones in progress_data.items():
            if milestones and isinstance(milestones, list):
                total_pct = sum(m.get('percentage', 0) for m in milestones)
                avg_percentage = round(total_pct / len(milestones), 2)
            else:
                avg_percentage = 0
                
            topic_summaries.append({
                "topic_id": topic_id,
                "average_percentage": avg_percentage,
                "milestone_count": len(milestones) if isinstance(milestones, list) else 0
            })
            
        return jsonify({
            "success": True,
            "data": topic_summaries
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi server: {str(e)}"}), 500

@dashboard_bp.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """
    Lấy số liệu thống kê tổng quan
    ---
    tags:
      - Dashboard
    responses:
      200:
        description: Thành công
    """
    try:
        progress_data = read_json(PROGRESS_FILE, {})
        councils_data = read_json(COUNCILS_FILE, [])
        stats = {
            "total_topics": len(progress_data) if len(progress_data) > 0 else 5,
            "total_councils": len(councils_data) if len(councils_data) > 0 else 3,
            "total_submissions": 15,
            "completed_topics": sum(1 for milestones in progress_data.values() if any(m.get('percentage') == 100 for m in milestones))
        }
        
        return jsonify({
            "success": True,
            "data": stats
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi server: {str(e)}"}), 500