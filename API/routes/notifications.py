from flask import Blueprint, jsonify

notifications_bp = Blueprint('notifications_api', __name__, url_prefix='/api/notifications')

@notifications_bp.route('', methods=['GET'])
def get_notifications():
    """
    Get all notifications for the current user
    ---
    tags:
      - Notifications
    responses:
      200:
        description: List of notifications
    """
    # Mocking notifications
    return jsonify([
        {
            'id': 1,
            'title': 'Hồ sơ đã được duyệt',
            'message': 'Đề tài của bạn đã được TS. Nguyễn Văn A duyệt.',
            'created_at': '2026-09-10 08:00:00',
            'is_read': False
        },
        {
            'id': 2,
            'title': 'Đến hạn nộp báo cáo',
            'message': 'Vui lòng nộp báo cáo định kỳ tháng 9 trước ngày 15.',
            'created_at': '2026-09-09 10:00:00',
            'is_read': True
        }
    ]), 200
