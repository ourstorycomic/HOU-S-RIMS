from flask import Blueprint, request, jsonify
from models import db, Milestone, Progress

progress_bp = Blueprint('progress_api', __name__, url_prefix='/api/topics')

@progress_bp.route('/<int:topic_id>/progress', methods=['GET'])
def get_progress(topic_id):
    """
    Get progress of a topic
    ---
    tags:
      - Progress
    parameters:
      - in: path
        name: topic_id
        type: integer
        required: true
    responses:
      200:
        description: List of milestones and progress
    """
    milestones = Milestone.query.filter_by(topic_id=topic_id).all()
    result = []
    for m in milestones:
        progresses = Progress.query.filter_by(milestone_id=m.id).all()
        result.append({
            'milestone_id': m.id,
            'name': m.name,
            'deadline': m.deadline.strftime('%Y-%m-%d %H:%M:%S') if m.deadline else None,
            'status': m.status,
            'progress': [{'id': p.id, 'percentage': p.percentage, 'notes': p.notes} for p in progresses]
        })
    return jsonify(result), 200

@progress_bp.route('/<int:topic_id>/progress', methods=['POST'])
def update_progress(topic_id):
    """
    Update progress of a milestone for a topic
    ---
    tags:
      - Progress
    """
    from flask import session
    data = request.get_json()
    if not data or 'milestone_id' not in data or 'percentage' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
        
    try:
        new_progress = Progress(
            milestone_id=data['milestone_id'],
            percentage=int(data['percentage']),
            notes=data.get('notes', '')
        )
        db.session.add(new_progress)
        db.session.commit()

        # Send notifications to all topic members
        try:
            from models import Notification, User, Topic, Group, GroupMember
            from email_utils import send_notification_email

            milestone = Milestone.query.get(data['milestone_id'])
            topic = Topic.query.get(topic_id)
            updater = User.query.get(session.get('user_id'))
            updater_name = updater.full_name if updater else "Giảng viên"

            if milestone and topic:
                pct = int(data['percentage'])
                notif_msg = f"📊 {updater_name} đã cập nhật tiến độ cột mốc '{milestone.name}' lên {pct}% trong đề tài '{topic.title}'"

                recipients = []
                # Notify students in group
                if topic.group_id:
                    members = GroupMember.query.filter_by(group_id=topic.group_id).all()
                    for m in members:
                        recipients.append(User.query.get(m.student_id))
                # Notify topic mentor if updater is not the mentor
                if topic.mentor_id and topic.mentor_id != session.get('user_id'):
                    recipients.append(User.query.get(topic.mentor_id))

                for u in recipients:
                    if not u:
                        continue
                    notif = Notification(user_id=u.id, content=notif_msg)
                    db.session.add(notif)
                    try:
                        send_notification_email(
                            to_email=u.email,
                            subject=f"[HOU S-RIMS] Cập nhật tiến độ - {topic.title}",
                            body=f"""Xin chào {u.full_name},

{updater_name} vừa cập nhật tiến độ cột mốc trong đề tài "{topic.title}":

📌 Cột mốc: {milestone.name}
📊 Tiến độ mới: {pct}%

Xem chi tiết tại: http://127.0.0.1:5000/student/progress

Trân trọng,
HOU S-RIMS"""
                        )
                    except Exception:
                        pass
                db.session.commit()
        except Exception:
            pass

        return jsonify({'message': 'Progress updated'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@progress_bp.route('/<int:topic_id>/milestones', methods=['POST'])
def add_milestone(topic_id):
    from datetime import datetime
    data = request.get_json()
    if not data or 'name' not in data or 'deadline' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
        
    try:
        deadline_date = datetime.strptime(data['deadline'], '%Y-%m-%d')
        new_milestone = Milestone(
            topic_id=topic_id,
            name=data['name'],
            deadline=deadline_date,
            description=data.get('description', '')
        )
        db.session.add(new_milestone)
        db.session.commit()
        return jsonify({'message': 'Milestone created', 'id': new_milestone.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
