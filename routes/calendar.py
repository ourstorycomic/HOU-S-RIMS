from flask import Blueprint, request, jsonify
from models import db, Meeting

calendar_bp = Blueprint('calendar_bp', __name__, url_prefix='/api/calendar')

@calendar_bp.route('/meetings', methods=['POST'])
def create_meeting():
    data = request.get_json()
    if not data or 'date_time' not in data:
        return jsonify({"msg": "Thiếu thông tin ngày tháng (date_time)"}), 400
    
    new_meeting = Meeting(
        date_time=data['date_time'],
        notes=data.get('notes', '')
    )
    db.session.add(new_meeting)
    db.session.commit()
    
    return jsonify({
        "msg": "Tạo lịch họp thành công!",
        "meeting": new_meeting.to_dict()
    }), 201
