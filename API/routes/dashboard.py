from flask import Blueprint, jsonify
from models import Topic, Group, User

dashboard_bp = Blueprint('dashboard_api', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('/progress', methods=['GET'])
def get_progress_dashboard():
    """
    Get progress dashboard data
    ---
    tags:
      - Dashboard
    responses:
      200:
        description: Progress data
    """
    # Mocking aggregated progress for dashboard
    return jsonify({
        'overall_progress': 75,
        'topics_on_track': 10,
        'topics_behind': 2
    }), 200

@dashboard_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    Get system statistics
    ---
    tags:
      - Dashboard
    responses:
      200:
        description: System stats
    """
    total_topics = Topic.query.count()
    total_groups = Group.query.count()
    total_students = User.query.filter_by(role='Student').count()
    total_mentors = User.query.filter_by(role='Mentor').count()
    
    return jsonify({
        'total_topics': total_topics,
        'total_groups': total_groups,
        'total_students': total_students,
        'total_mentors': total_mentors
    }), 200
