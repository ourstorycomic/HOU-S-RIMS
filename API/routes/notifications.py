from flask import Blueprint, jsonify, session
from models import db, Notification

notifications_bp = Blueprint('notifications_api', __name__, url_prefix='/api/notifications')

@notifications_bp.route('', methods=['GET'])
def get_notifications():
    """
    Get all notifications for the current logged-in user
    ---
    tags:
      - Notifications
    responses:
      200:
        description: List of notifications
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    notifs = Notification.query.filter_by(user_id=user_id).order_by(Notification.is_read.asc(), Notification.created_at.desc()).all()
    result = [
        {
            'id': n.id,
            'content': n.content,
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S') if n.created_at else ''
        }
        for n in notifs
    ]
    return jsonify(result), 200

@notifications_bp.route('/<int:notif_id>/read', methods=['PATCH'])
def mark_read(notif_id):
    """Mark a notification as read"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    notif = Notification.query.filter_by(id=notif_id, user_id=user_id).first()
    if not notif:
        return jsonify({'error': 'Not found'}), 404

    notif.is_read = True
    db.session.commit()
    return jsonify({'message': 'Marked as read'}), 200

@notifications_bp.route('/read', methods=['DELETE'])
def delete_read_notifications():
    """Delete all read notifications for the current user"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    Notification.query.filter_by(user_id=user_id, is_read=True).delete()
    db.session.commit()
    return jsonify({'message': 'Deleted read notifications'}), 200

@notifications_bp.route('/sync', methods=['GET'])
def sync_notifications():
    """
    Real-time synchronization endpoint for notifications, invitations, topic status, and role counters
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    from models import Notification, GroupMember, Topic, Group, User
    
    current_u = User.query.get(user_id)
    user_role = (current_u.role if current_u else '').lower()
    
    # 1. Notifications
    notifs = Notification.query.filter_by(user_id=user_id).order_by(
        Notification.is_read.asc(), Notification.created_at.desc()
    ).limit(30).all()
    
    unread_notifs_count = sum(1 for n in notifs if not n.is_read)
    
    # 2. Received Invitations (memberships where current user is NOT leader)
    received_invitations = []
    memberships = GroupMember.query.filter_by(student_id=user_id).all()
    for m in memberships:
        if m.group and m.group.leader_id != user_id:
            topic = m.group.topics[0] if (m.group.topics and len(m.group.topics) > 0) else None
            received_invitations.append({
                'id': m.id,
                'group_id': m.group_id,
                'group_name': m.group.name,
                'leader_name': m.group.leader.full_name if m.group.leader else '',
                'topic_title': topic.title if topic else 'NCKH',
                'status': m.status
            })
            
    pending_inv_count = sum(1 for inv in received_invitations if inv['status'] in ['pending', 'invited'])
    total_badge_count = unread_notifs_count + pending_inv_count
    
    # 3. Group and topic status (for live member acceptance & topic progress updates)
    group_data = None
    sent_pending_invitations = []
    led_group = Group.query.filter_by(leader_id=user_id).order_by(Group.id.desc()).first()
    if not led_group and memberships:
        # Check any group user is member of (khi đã chính thức đồng ý tham gia)
        accepted_m = [m for m in memberships if m.status in ['accepted', 'joined']]
        if accepted_m:
            first_m = accepted_m[0]
            if first_m.group:
                led_group = first_m.group

    if led_group:
        g_topic = led_group.topics[0] if (led_group.topics and len(led_group.topics) > 0) else None
        
        status_map = {'waiting_for_members': 0, 'pending': 1, 'faculty_pending': 2, 'approved': 3, 'rejected': 0}
        step = status_map.get(g_topic.status if g_topic else '', 1)
        pct = 100 if (g_topic and g_topic.status == 'approved') else (50 if (g_topic and g_topic.status == 'faculty_pending') else 0)
        
        status_labels = {
            'approved': 'ĐÃ PHÊ DUYỆT CHÍNH THỨC',
            'faculty_pending': 'GV ĐÃ DUYỆT • CHỜ KHOA DUYỆT',
            'waiting_for_members': 'CHỜ THÀNH VIÊN XÁC NHẬN',
            'rejected': 'TỪ CHỐI PHÊ DUYỆT',
            'pending': 'ĐANG CHỜ GV DUYỆT'
        }
        
        # Check rejected members in group
        rejected_members = [gm for gm in led_group.members if gm.status in ['rejected', 'declined']]
        has_rejected = len(rejected_members) > 0
        rejected_names = [gm.student.full_name if gm.student else f"SV {gm.student_id}" for gm in rejected_members]

        # Check pending invitations sent by leader
        if led_group.leader_id == user_id:
            for gm in led_group.members:
                if gm.student_id != user_id and gm.status in ['pending', 'invited']:
                    sent_pending_invitations.append({
                        'student_id': gm.student_id,
                        'full_name': gm.student.full_name if gm.student else '',
                        'student_code': gm.student.student_id or (gm.student.username if gm.student else '')
                    })

        group_data = {
            'group_id': led_group.id,
            'group_name': led_group.name,
            'is_leader': bool(led_group.leader_id == user_id),
            'topic': {
                'id': g_topic.id if g_topic else None,
                'title': g_topic.title if g_topic else '',
                'status': g_topic.status if g_topic else '',
                'status_label': status_labels.get(g_topic.status, 'ĐANG CHỜ GV DUYỆT') if g_topic else '',
                'step': step,
                'pct': pct,
                'mentor_id': g_topic.mentor_id if g_topic else None,
                'mentor_name': g_topic.mentor.full_name if (g_topic and g_topic.mentor) else 'Chưa có',
                'group_id': led_group.id,
                'group_name': led_group.name,
                'description': g_topic.description or '' if g_topic else '',
                'has_rejected_members': has_rejected,
                'rejected_names': rejected_names,
                'members': [
                    {
                        'student_id': gm.student_id,
                        'full_name': gm.student.full_name if gm.student else '',
                        'student_code': gm.student.student_id or (gm.student.username if gm.student else ''),
                        'faculty': gm.student.faculty if gm.student else '',
                        'status': gm.status,
                        'is_leader': bool(gm.student_id == led_group.leader_id)
                    }
                    for gm in led_group.members
                ]
            } if g_topic else None,
            'members': [
                {
                    'student_id': gm.student_id,
                    'name': gm.student.full_name if gm.student else '',
                    'code': gm.student.student_id or (gm.student.username if gm.student else ''),
                    'faculty': gm.student.faculty if gm.student else '',
                    'status': gm.status
                }
                for gm in led_group.members
            ]
        }

    # 4. Role-specific counts and system state hash (Lecturer, Faculty & Admin)
    lecturer_pending_count = 0
    faculty_pending_count = 0
    if user_role == 'lecturer':
        lecturer_pending_count = Topic.query.filter_by(mentor_id=user_id, status='pending').count()
    elif user_role in ['faculty', 'admin']:
        faculty_pending_count = Topic.query.filter_by(status='faculty_pending').count()

    # Tính toán dấu vết dữ liệu hệ thống (data fingerprint) để đồng bộ tự động thời gian thực cho Khoa và Admin
    system_state_hash = ""
    try:
        from models import Submission, Batch
        latest_sub = Submission.query.order_by(Submission.id.desc()).first()
        latest_sub_id = latest_sub.id if latest_sub else 0
        latest_sub_status = latest_sub.status if latest_sub else ''
        latest_sub_fac = latest_sub.faculty_status if latest_sub else ''
        
        latest_topic = Topic.query.order_by(Topic.id.desc()).first()
        latest_topic_id = latest_topic.id if latest_topic else 0
        latest_topic_status = latest_topic.status if latest_topic else ''
        
        sub_count = Submission.query.count()
        topic_count = Topic.query.count()
        batch_count = Batch.query.count()
        approved_sub_count = Submission.query.filter_by(status='approved').count()
        
        system_state_hash = f"{faculty_pending_count}_{topic_count}_{sub_count}_{approved_sub_count}_{latest_sub_id}_{latest_sub_status}_{latest_sub_fac}_{latest_topic_id}_{latest_topic_status}_{batch_count}"
    except Exception:
        system_state_hash = f"{faculty_pending_count}_{lecturer_pending_count}"

    return jsonify({
        'total_badge_count': total_badge_count,
        'unread_notifs_count': unread_notifs_count,
        'pending_invitations_count': pending_inv_count,
        'invitations': received_invitations,
        'sent_pending_invitations': sent_pending_invitations,
        'notifications': [
            {
                'id': n.id,
                'content': n.content,
                'is_read': n.is_read,
                'created_at': n.created_at.strftime('%d/%m/%Y %H:%M') if n.created_at else ''
            }
            for n in notifs
        ],
        'group_data': group_data,
        'user_role': user_role,
        'lecturer_pending_count': lecturer_pending_count,
        'faculty_pending_count': faculty_pending_count,
        'system_state_hash': system_state_hash
    }), 200
