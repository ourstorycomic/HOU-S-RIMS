# routes/web.py
from flask import Blueprint, render_template, session, redirect, url_for, request
from models import User, Topic, Group, GroupMember, Batch, Notification

web_bp = Blueprint('web', __name__)

@web_bp.before_request
def check_login():
    if 'user_id' not in session and request.endpoint != 'auth.login':
        return redirect(url_for('auth.login'))

@web_bp.route('/')
def home():
    role = session.get('role', '').lower()
    if role == 'admin': return redirect(url_for('web.admin_page'))
    if role == 'student': return redirect(url_for('student.dashboard'))
    if role == 'lecturer': return redirect(url_for('lecturer.dashboard'))
    if role == 'faculty': return redirect(url_for('faculty.dashboard'))
    return redirect(url_for('web.admin_page'))

@web_bp.route('/admin')
def admin_page():
    if session.get('role') not in ['admin', 'faculty']:
        return redirect(url_for('auth.login'))
    
    from models import Topic, User, Batch, Council, Group
    topics = Topic.query.all()
    users = User.query.all()
    batches = Batch.query.order_by(Batch.id.desc()).all()
    councils = Council.query.all()
    groups = Group.query.all()
    return render_template('admin.html', topics=topics, users=users, batches=batches, councils=councils, groups=groups)

@web_bp.route('/repository')
def repository_page():
    return render_template('repository.html')

@web_bp.route('/analysis')
def analysis_page():
    return render_template('analysis.html')

@web_bp.route('/student')
def student_page():
    if session.get('role') != 'student':
        return redirect(url_for('auth.login'))
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    return render_template('student.html', current_user=current_user)
# Danh sách giảng viên hướng dẫn (Mentor List)
@web_bp.route('/mentors')
def mentors_page():
    return render_template('mentors.html')

# Chi tiết giảng viên (Mentor Detail)
@web_bp.route('/mentor/detail')
@web_bp.route('/mentor/<int:mentor_id>')
def mentor_detail_page(mentor_id=1):
    return render_template('mentor_detail.html', mentor_id=mentor_id)
