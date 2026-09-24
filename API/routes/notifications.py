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

    notifs = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
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
