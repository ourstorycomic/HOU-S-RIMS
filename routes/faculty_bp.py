from flask import Blueprint, render_template, session, redirect, url_for
from models import db, User, Batch, Group, Topic, TopicRegistration, Council, GroupMember, Notification, Milestone, Progress
from datetime import datetime
from sqlalchemy import func

faculty_bp = Blueprint('faculty', __name__, url_prefix='/faculty')

@faculty_bp.before_request
def require_faculty():
    if session.get('role') != 'faculty':
        return redirect(url_for('auth.login'))

@faculty_bp.context_processor
def inject_common_data():
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    return dict(current_user=current_user, current_time=datetime.utcnow())

@faculty_bp.route('/')
def index():
    return redirect(url_for('faculty.dashboard'))

@faculty_bp.route('/dashboard')
def dashboard():
    topics = Topic.query.all()
    groups = Group.query.all()
    mentors = User.query.filter_by(role='lecturer').all()
    students = User.query.filter_by(role='student').all()
    # stats mapping from original web.py
    stats = {
        'total_topics': len(topics),
        'total_groups': len(groups),
        'total_mentors': len(mentors),
        'total_students': len(students)
    }
    return render_template('faculty/dashboard.html', stats=stats)

@faculty_bp.route('/batches')
def batches():
    all_batches = Batch.query.all()
    return render_template('faculty/batches.html', batches=all_batches)

@faculty_bp.route('/topics')
def topics():
    pending_topics = Topic.query.filter_by(status='faculty_pending').all()
    approved_topics = Topic.query.filter_by(status='approved').all()
    return render_template('faculty/topics.html', pending_topics=pending_topics, approved_topics=approved_topics)

@faculty_bp.route('/lecturers')
def lecturers():
    all_lecturers = User.query.filter_by(role='lecturer').all()
    return render_template('faculty/lecturers.html', lecturers=all_lecturers)

@faculty_bp.route('/students')
def students():
    all_students = User.query.filter_by(role='student').all()
    return render_template('faculty/students.html', students=all_students)

@faculty_bp.route('/council')
def council():
    councils = Council.query.all()
    return render_template('faculty/council.html', councils=councils)

@faculty_bp.route('/rubric')
def rubric():
    return render_template('faculty/rubric.html')

@faculty_bp.route('/stats')
def stats_page():
    return render_template('faculty/stats.html')
