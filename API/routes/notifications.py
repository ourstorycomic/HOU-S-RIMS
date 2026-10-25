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
    Real-time synchronization endpoint for notifications, invitations, and group status
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    from models import Notification, GroupMember, Topic, Group, User
    
    # 1. Notifications
    notifs = Notification.query.filter_by(user_id=user_id).order_by(
        Notification.is_read.asc(), Notification.created_at.desc()
    ).limit(25).all()
    
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
    
    # 3. Group and topic status (for live member acceptance update on leader's screen)
    group_data = None
    led_group = Group.query.filter_by(leader_id=user_id).order_by(Group.id.desc()).first()
    if not led_group and memberships:
        # Check any group user is member of (chỉ lấy khi đã chính thức đồng ý tham gia)
        accepted_m = [m for m in memberships if m.status in ['accepted', 'joined']]
        if accepted_m:
            first_m = accepted_m[0]
            if first_m.group:
                led_group = first_m.group

    if led_group:
        g_topic = led_group.topics[0] if (led_group.topics and len(led_group.topics) > 0) else None
        
        status_map = {'waiting_for_members': 0, 'pending': 1, 'faculty_pending': 2, 'approved': 3, 'rejected': 0}
        step = status_map.get(g_topic.status if g_topic else '', 1)
        pct = 100 if (g_topic and g_topic.status == 'approved') else (50 if (g_topic and g_topic.status == 'faculty_pending') else (10 if (g_topic and g_topic.status == 'pending') else 0))
        
        status_labels = {
            'approved': 'ĐÃ PHÊ DUYỆT CHÍNH THỨC',
            'faculty_pending': 'GV ĐÃ DUYỆT • CHỜ KHOA DUYỆT',
            'waiting_for_members': 'CHỜ THÀNH VIÊN XÁC NHẬN',
            'rejected': 'TỪ CHỐI PHÊ DUYỆT',
            'pending': 'ĐANG CHỜ GV DUYỆT'
        }
        
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
                'pct': pct
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

    return jsonify({
        'total_badge_count': total_badge_count,
        'unread_notifs_count': unread_notifs_count,
        'pending_invitations_count': pending_inv_count,
        'invitations': received_invitations,
        'notifications': [
            {
                'id': n.id,
                'content': n.content,
                'is_read': n.is_read,
                'created_at': n.created_at.strftime('%d/%m/%Y %H:%M') if n.created_at else ''
            }
            for n in notifs
        ],
        'group_data': group_data
    }), 200
