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
    from models import Milestone, User
    meetings = Meeting.query.filter(Meeting.status.in_(['approved', 'pending'])).all()
    result = []
    for m in meetings:
        topic_title = m.topic.title if m.topic else None
        mentor_name = m.topic.mentor.full_name if (m.topic and m.topic.mentor) else None
        organizer = User.query.get(m.organizer_id) if m.organizer_id else None
        organizer_name = organizer.full_name if organizer else None
        organizer_role = (organizer.role if organizer else '').lower()
        result.append({
            'id': m.id,
            'title': m.title,
            'description': m.description,
            'start': m.start_time.strftime('%Y-%m-%d %H:%M:%S') if m.start_time else None,
            'end': m.end_time.strftime('%Y-%m-%d %H:%M:%S') if m.end_time else None,
            'organizer_id': m.organizer_id,
            'organizer_name': organizer_name,
            'organizer_role': organizer_role,
            'topic_id': m.topic_id,
            'topic_title': topic_title,
            'mentor_name': mentor_name,
            'status': m.status
        })

    milestones = Milestone.query.all()
    for ms in milestones:
        result.append({
            'id': f'ms_{ms.id}',
            'title': f'🚩 Deadline: {ms.name}',
            'description': f'Cột mốc NCKH: {ms.name}',
            'start': ms.deadline.strftime('%Y-%m-%d %H:%M:%S') if ms.deadline else None,
            'end': ms.deadline.strftime('%Y-%m-%d %H:%M:%S') if ms.deadline else None,
            'status': 'milestone'
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
    if end <= start:
        return jsonify({'error': 'Giờ kết thúc phải sau giờ bắt đầu!'}), 400

    # Task 3.7: Bắt lỗi khung giờ hành chính (07:30 - 17:30)
    from datetime import time as time_cls
    office_start = time_cls(7, 30)
    office_end = time_cls(17, 30)
    if start.time() < office_start or end.time() > office_end:
        return jsonify({'error': 'Lịch hẹn phải nằm trong khung giờ hành chính (từ 07:30 đến 17:30)!'}), 400

    # Tự động phát hiện topic_id nếu không truyền hoặc rỗng
    topic_id = data.get('topic_id')
    try:
        topic_id = int(topic_id) if topic_id else None
    except (ValueError, TypeError):
        topic_id = None

    from models import Topic, Group, GroupMember, Notification, User
    if not topic_id:
        lead_topic = Topic.query.join(Group).filter(Group.leader_id == user_id).order_by(Topic.id.desc()).first()
        if lead_topic:
            topic_id = lead_topic.id
        else:
            member_gm = GroupMember.query.filter_by(student_id=user_id, status='accepted').order_by(GroupMember.id.desc()).first()
            if member_gm:
                mem_topic = Topic.query.filter_by(group_id=member_gm.group_id).order_by(Topic.id.desc()).first()
                if mem_topic:
                    topic_id = mem_topic.id

    # Chống spam / trùng lặp (nếu sinh viên nhấp đúp hoặc gửi cùng 1 lịch hẹn)
    existing_dup = Meeting.query.filter_by(
        organizer_id=user_id,
        start_time=start,
        end_time=end,
        status='pending'
    ).first()
    if existing_dup:
        return jsonify({'message': 'Yêu cầu lịch hẹn này đã được gửi trước đó.', 'meeting_id': existing_dup.id}), 200

    try:
        new_meeting = Meeting(
            title=data['title'].strip(),
            description=data.get('description', '').strip(),
            start_time=start,
            end_time=end,
            organizer_id=user_id,
            topic_id=topic_id,
            status='pending'
        )
        db.session.add(new_meeting)
        db.session.commit()

        # Gửi thông báo đến người nhận tương ứng
        if topic_id:
            topic = Topic.query.get(topic_id)
            actor = User.query.get(user_id)
            actor_name = actor.full_name if actor else session.get('full_name', 'Người dùng')
            start_str = start.strftime('%H:%M %d/%m/%Y')
            end_str = end.strftime('%H:%M %d/%m/%Y')

            # Nếu Giảng viên / Khoa tạo lịch -> Gửi thông báo đến toàn bộ sinh viên trong nhóm đề tài
            if (session.get('role') or '').lower() in ('lecturer', 'faculty') or (topic and user_id == topic.mentor_id):
                if topic and topic.group:
                    notif_content = (
                        f"Giảng viên {actor_name} đã đề xuất lịch họp: '{data['title'].strip()}' "
                        f"({start_str} - {end_str}) cho đề tài '{topic.title}'. "
                        f"Vui lòng vào mục Lịch & Thông báo để xác nhận hoặc phản hồi."
                    )
                    notified_users = set()
                    if topic.group.leader_id and topic.group.leader_id != user_id:
                        db.session.add(Notification(user_id=topic.group.leader_id, content=notif_content))
                        notified_users.add(topic.group.leader_id)
                    from models import GroupMember
                    members = GroupMember.query.filter_by(group_id=topic.group_id, status='accepted').all()
                    for m in members:
                        if m.student_id != user_id and m.student_id not in notified_users:
                            db.session.add(Notification(user_id=m.student_id, content=notif_content))
                            notified_users.add(m.student_id)
                    db.session.commit()

            # Nếu Sinh viên tạo lịch -> Gửi thông báo đến GVHD
            elif topic and topic.mentor_id:
                notif_content = (
                    f"Sinh viên {actor_name} đã gửi yêu cầu lịch hẹn: '{data['title'].strip()}' "
                    f"({start_str} - {end_str}) cho đề tài '{topic.title}'. "
                    f"Vui lòng vào mục Lịch & Sự kiện để phê duyệt."
                )
                db.session.add(Notification(
                    user_id=topic.mentor_id,
                    content=notif_content
                ))
                db.session.commit()

        return jsonify({'message': 'Meeting created successfully', 'meeting_id': new_meeting.id}), 201
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
        if meeting.organizer_id != user_id and (session.get('role') or '').lower() not in ('admin', 'faculty', 'lecturer'):
            return jsonify({'error': 'Permission denied'}), 403

        db.session.delete(meeting)
        db.session.commit()
        return jsonify({'message': 'Meeting deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@calendar_bp.route('/events/<int:id>/status', methods=['PUT'])
def update_event_status(id):
    user_id = session.get('user_id')
    user_role = (session.get('role') or '').lower()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    meeting = Meeting.query.get(id)
    if not meeting:
        return jsonify({'error': 'Meeting not found'}), 404

    # Kiểm tra quyền duyệt/phản hồi
    can_update = False
    if user_role in ('lecturer', 'faculty', 'admin'):
        can_update = True
    elif user_role == 'student':
        # Sinh viên có quyền chấp nhận / từ chối lịch do Giảng viên đề xuất cho đề tài của nhóm
        from models import GroupMember
        if meeting.topic and meeting.topic.group:
            g = meeting.topic.group
            if g.leader_id == user_id:
                can_update = True
            else:
                is_mem = GroupMember.query.filter_by(group_id=g.id, student_id=user_id, status='accepted').first()
                if is_mem:
                    can_update = True
        # Người tạo không thể tự duyệt lịch của chính mình
        if meeting.organizer_id == user_id:
            can_update = False

    if not can_update:
        return jsonify({'error': 'Bạn không có quyền phản hồi lịch hẹn này'}), 403

    data = request.get_json(silent=True) or {}
    new_status = data.get('status')
    if new_status not in ['approved', 'rejected', 'pending']:
        return jsonify({'error': 'Invalid status'}), 400

    meeting.status = new_status
    db.session.commit()

    from models import User, Notification
    actor_name = session.get('full_name', 'Người dùng')

    # Nếu người duyệt là sinh viên -> gửi thông báo và email cho GVHD (người tổ chức)
    if user_role == 'student':
        status_text = "đồng ý tham gia" if new_status == 'approved' else "từ chối"
        target_id = meeting.organizer_id or (meeting.topic.mentor_id if meeting.topic else None)
        if target_id:
            lecturer = User.query.get(target_id)
            notif_content = f"Sinh viên {actor_name} đã {status_text} lịch hẹn '{meeting.title}' ({meeting.start_time.strftime('%H:%M %d/%m/%Y') if meeting.start_time else ''})."
            db.session.add(Notification(user_id=target_id, content=notif_content))
            db.session.commit()
            if lecturer and lecturer.email:
                try:
                    from email_utils import send_notification_email
                    send_notification_email(
                        to_email=lecturer.email,
                        subject=f"[HOU S-RIMS] Sinh viên đã {status_text} lịch hẹn",
                        content=f"""Xin chào {lecturer.full_name},

Sinh viên {actor_name} đã {status_text} lịch hẹn do Thầy/Cô đề xuất:
- Tiêu đề: {meeting.title}
- Thời gian: {meeting.start_time.strftime('%H:%M %d/%m/%Y') if meeting.start_time else ''}
- Trạng thái: {status_text.upper()}

Trân trọng,
HOU S-RIMS"""
                    )
                except Exception as e:
                    print(f"Email error: {e}")

    # Nếu người duyệt là Giảng viên / Khoa -> gửi thông báo và email cho Sinh viên (người tạo meeting hoặc nhóm)
    else:
        status_text = "phê duyệt" if new_status == 'approved' else "từ chối"
        student = User.query.get(meeting.organizer_id)
        if student:
            notif_content = f"Giảng viên {actor_name} đã {status_text} yêu cầu lịch hẹn '{meeting.title}' của bạn."
            db.session.add(Notification(user_id=student.id, content=notif_content))
            db.session.commit()
            if student.email:
                try:
                    from email_utils import send_notification_email
                    send_notification_email(
                        to_email=student.email,
                        subject=f"[HOU S-RIMS] Lịch hẹn đã được {status_text}",
                        content=f"""Xin chào {student.full_name},

Giảng viên {actor_name} đã {status_text} yêu cầu lịch hẹn của bạn:
- Tiêu đề: {meeting.title}
- Thời gian: {meeting.start_time.strftime('%H:%M %d/%m/%Y') if meeting.start_time else ''}
- Trạng thái: {status_text.upper()}

Trân trọng,
HOU S-RIMS"""
                    )
                except Exception as e:
                    print(f"Email error: {e}")

    return jsonify({'message': 'Status updated successfully', 'status': new_status})
