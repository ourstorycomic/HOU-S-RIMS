from sqlalchemy import func
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
    from flask import session
    from models import Batch
    current_year = session.get('academic_year', '2025-2026')
    total = Topic.query.join(Batch).filter(Batch.academic_year == current_year).count()
    approved = Topic.query.join(Batch).filter(Topic.status=='approved', Batch.academic_year == current_year).count()
    pending = Topic.query.join(Batch).filter(Topic.status=='pending', Batch.academic_year == current_year).count()
    rejected = Topic.query.join(Batch).filter(Topic.status=='rejected', Batch.academic_year == current_year).count()

    progress_pct = int((approved / total * 100) if total > 0 else 0)
    return jsonify({
        'overall_progress': progress_pct,
        'topics_on_track': approved,
        'topics_pending': pending,
        'topics_rejected': rejected
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
    from flask import session
    from models import Batch
    current_year = session.get('academic_year', '2025-2026')
    
    total_topics = Topic.query.join(Batch).filter(Batch.academic_year == current_year).count()
    total_groups = Group.query.join(Batch).filter(Batch.academic_year == current_year).count()
    total_students = User.query.filter(func.lower(User.role) == 'student').count()
    total_mentors = User.query.filter(func.lower(User.role) == 'lecturer').count()
    
    return jsonify({
        'total_topics': total_topics,
        'total_groups': total_groups,
        'total_students': total_students,
        'total_mentors': total_mentors
    }), 200
