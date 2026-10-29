from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Blueprint, request, jsonify, session
from models import db, Meeting

calendar_bp = Blueprint('calendar_api', __name__, url_prefix='/api/calendar')

LOCAL_TZ = ZoneInfo('Asia/Ho_Chi_Minh')


def _now_local():
    """Giờ hiện tại theo giờ Việt Nam (naive) để so với giá trị lưu trong DB."""
    return datetime.now(LOCAL_TZ).replace(tzinfo=None)


def _parse_dt(value):
    """Nhận 'YYYY-MM-DDTHH:MM', 'YYYY-MM-DD HH:MM' (có thể kèm giây). Không có giờ -> None."""
    if not value or not isinstance(value, str):
        return None
    for fmt in ('%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


@calendar_bp.route('/events', methods=['GET'])
def get_events():
    """
    Get all calendar events/meetings
    ---
    tags:
      - Calendar
    parameters:
      - in: query
        name: user_id
        type: integer
        description: Filter events by user ID
    responses:
      200:
        description: List of events
    """
    from models import Milestone
    meetings = Meeting.query.filter(Meeting.status.in_(['approved', 'pending'])).all()
    result = []
    for m in meetings:
        result.append({
            'id': m.id,
            'title': m.title,
            'description': m.description,
            'start': m.start_time.strftime('%Y-%m-%d %H:%M:%S') if m.start_time else None,
            'end': m.end_time.strftime('%Y-%m-%d %H:%M:%S') if m.end_time else None,
            'organizer_id': m.organizer_id,
            'topic_id': m.topic_id,
            'status': m.status
        })

    milestones = Milestone.query.all()
    for ms in milestones:
        result.append({
            'id': f'ms_{ms.id}',
            'title': f'🚩 Deadline: {ms.name}',
            'start': ms.deadline.strftime('%Y-%m-%d %H:%M:%S') if ms.deadline else None,
            'end': ms.deadline.strftime('%Y-%m-%d %H:%M:%S') if ms.deadline else None,
            'status': 'milestone',
            'milestone_id': ms.id,
            'topic_id': ms.topic_id,
            'name': ms.name
        })

    return jsonify(result), 200


@calendar_bp.route('/events', methods=['POST'])
def create_event():
    """
    Create a new event/meeting
    """
    data = request.get_json(silent=True)
    if not data or 'title' not in data or 'start_time' not in data:
        return jsonify({'error': 'Missing required fields (title, start_time)'}), 400

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    start = _parse_dt(data['start_time'])
    if not start:
        return jsonify({'error': 'Thời gian không hợp lệ hoặc thiếu giờ (định dạng YYYY-MM-DDTHH:MM)'}), 400
    end = _parse_dt(data.get('end_time')) if data.get('end_time') else start
    if not end:
        return jsonify({'error': 'Thời gian kết thúc không hợp lệ'}), 400

    # Không cho đặt lịch hẹn trong quá khứ (tính cả giờ)
    if start <= _now_local():
        return jsonify({'error': 'Không thể đặt lịch hẹn trong quá khứ (tính cả giờ)'}), 400
    if end < start:
        return jsonify({'error': 'Thời gian kết thúc phải sau thời gian bắt đầu'}), 400

    try:
        new_meeting = Meeting(
            title=data['title'],
            description=data.get('description', ''),
            start_time=start,
            end_time=end,
            organizer_id=user_id,
            topic_id=data.get('topic_id'),
            status='pending'
        )
        db.session.add(new_meeting)
        db.session.commit()
        return jsonify({'message': 'Meeting created successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@calendar_bp.route('/events/<int:meeting_id>', methods=['DELETE'])
def delete_event(meeting_id):
    """
    Delete (revoke) an event/meeting
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401

        meeting = Meeting.query.get(meeting_id)
        if not meeting:
            return jsonify({'error': 'Meeting not found'}), 404

        # Optional: check if user is organizer
        if meeting.organizer_id != user_id:
            return jsonify({'error': 'Permission denied'}), 403

        db.session.delete(meeting)
        db.session.commit()
        return jsonify({'message': 'Meeting deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@calendar_bp.route('/events/<int:id>/status', methods=['PUT'])
def update_event_status(id):
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401
    if (session.get('role') or '').lower() not in ('lecturer', 'faculty', 'admin'):
        return jsonify({'error': 'Permission denied'}), 403

    meeting = Meeting.query.get(id)
    if not meeting:
        return jsonify({'error': 'Meeting not found'}), 404

    data = request.get_json(silent=True) or {}
    new_status = data.get('status')
    if new_status not in ['approved', 'rejected', 'pending']:
        return jsonify({'error': 'Invalid status'}), 400

    meeting.status = new_status
    db.session.commit()

    # Notify student
    from models import User, Notification

    student = User.query.get(meeting.organizer_id)
    if student:
        lecturer_name = session.get('full_name', 'Giảng viên')
        status_text = "phê duyệt" if new_status == 'approved' else "từ chối"
        notif_content = f"Giảng viên {lecturer_name} đã {status_text} yêu cầu lịch hẹn '{meeting.title}' của bạn."

        db.session.add(Notification(user_id=student.id, content=notif_content))
        db.session.commit()

        try:
            from email_utils import send_notification_email
            send_notification_email(
                to_email=student.email,
                subject=f"[HOU S-RIMS] Lịch hẹn đã được {status_text}",
                content=f"""Xin chào {student.full_name},

Giảng viên {lecturer_name} đã {status_text} yêu cầu lịch hẹn của bạn:
- Tiêu đề: {meeting.title}
- Trạng thái: {status_text.upper()}

Trân trọng,
HOU S-RIMS"""
            )
        except Exception as e:
            print(f"Email error (meeting status): {e}")

    return jsonify({'message': 'Status updated successfully'})
