from flask import Blueprint, render_template, session, redirect, url_for
from models import db, User, Batch, Group, Topic, TopicRegistration, Council, GroupMember, Notification, Milestone, Progress
from datetime import datetime
from sqlalchemy import func

faculty_bp = Blueprint('faculty', __name__, url_prefix='/faculty')

@faculty_bp.before_request
def require_faculty():
    if session.get('role') not in ['faculty', 'admin']:
        return redirect(url_for('auth.login'))

def get_effective_academic_year():
    year = session.get('academic_year')
    if year:
        has_visible = Batch.query.filter(Batch.academic_year == year, Batch.status != 'hidden').first()
        if has_visible:
            return year

    # Default to active batch's academic year
    active_b = Batch.query.filter_by(status='active').first()
    if active_b and active_b.academic_year:
        session['academic_year'] = active_b.academic_year
        return active_b.academic_year

    # Otherwise latest non-hidden batch
    latest_b = Batch.query.filter(Batch.status != 'hidden').order_by(Batch.id.desc()).first()
    if latest_b and latest_b.academic_year:
        session['academic_year'] = latest_b.academic_year
        return latest_b.academic_year

    fallback = year or '2025-2026'
    session['academic_year'] = fallback
    return fallback

@faculty_bp.context_processor
def inject_common_data():
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    current_year = get_effective_academic_year()
    global_topic_count = Topic.query.join(Batch).filter(Batch.academic_year == current_year, Batch.status != 'hidden').count()
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.is_read.asc(), Notification.created_at.desc()).all() if user_id else []
    
    # Query distinct academic years from non-hidden batches
    available_years = [r[0] for r in db.session.query(Batch.academic_year).filter(Batch.status != 'hidden').distinct().all() if r[0]]
    if current_year not in available_years:
        available_years.append(current_year)
    available_years.sort(reverse=True)

    return dict(
        current_user=current_user, 
        current_time=datetime.utcnow(), 
        global_topic_count=global_topic_count, 
        notifications=notifications,
        current_academic_year=current_year,
        available_academic_years=available_years
    )

@faculty_bp.route('/')
def index():
    return redirect(url_for('faculty.dashboard'))

@faculty_bp.route('/dashboard')
def dashboard():
    current_year = get_effective_academic_year()
    topics = Topic.query.join(Batch).filter(Batch.academic_year == current_year, Batch.status != 'hidden').all()
    groups = Group.query.join(Batch).filter(Batch.academic_year == current_year, Batch.status != 'hidden').all()
    mentors = User.query.filter(func.lower(User.role) == 'lecturer').all()
    students = User.query.filter_by(role='student').all()
    # stats mapping from original web.py
    stats = {
        'total_topics': len(topics),
        'total_groups': len(groups),
        'total_mentors': len(mentors),
        'total_students': len(students)
    }
    return render_template('faculty/dashboard.html', stats=stats, topics=topics)

@faculty_bp.route('/batches')
def batches():
    current_year = get_effective_academic_year()
    all_batches = Batch.query.filter(Batch.academic_year == current_year, Batch.status != 'hidden').all()
    return render_template('faculty/batches.html', batches=all_batches)

@faculty_bp.route('/topics')
def topics():
    current_year = get_effective_academic_year()
    all_topics = Topic.query.join(Batch).filter(Batch.academic_year == current_year, Batch.status != 'hidden').all()
    mentors = User.query.filter(func.lower(User.role) == 'lecturer').all()
    return render_template('faculty/topics.html', topics=all_topics, mentors=mentors)

@faculty_bp.route('/lecturers')
def lecturers():
    all_lecturers = User.query.filter(func.lower(User.role) == 'lecturer').all()
    current_year = get_effective_academic_year()
    all_topics = Topic.query.join(Batch).filter(Batch.academic_year == current_year).all()
    return render_template('faculty/lecturers.html', mentors=all_lecturers, topics=all_topics)

@faculty_bp.route('/students')
def students():
    all_students = User.query.filter_by(role='student').all()
    return render_template('faculty/students.html', students=all_students)

@faculty_bp.route('/council')
def council():
    current_year = get_effective_academic_year()
    active_batch = Batch.query.filter_by(academic_year=current_year, status='active').first()
    councils = Council.query.join(Batch).filter(Batch.academic_year == current_year).all()
    mentors = User.query.filter(func.lower(User.role) == 'lecturer').all()
    topics = Topic.query.join(Batch).filter(Batch.academic_year == current_year).all()
    return render_template('faculty/council.html', councils=councils, mentors=mentors, active_batch=active_batch, topics=topics)

@faculty_bp.route('/rubric')
def rubric():
    return render_template('faculty/rubric.html')

@faculty_bp.route('/stats')
def stats_page():
    current_year = get_effective_academic_year()
    all_topics = Topic.query.join(Batch).filter(Batch.academic_year == current_year, Batch.status != 'hidden').all()
    return render_template('faculty/stats.html', topics=all_topics)

@faculty_bp.route('/set-academic-year', methods=['POST'])
def set_academic_year():
    from flask import request, jsonify
    year = request.json.get('year')
    if year:
        session['academic_year'] = year
        return jsonify({'success': True})
    return jsonify({'error': 'No year provided'}), 400
