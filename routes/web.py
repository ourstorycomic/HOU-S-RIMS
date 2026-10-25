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
    
    # Tìm nhóm của sinh viên (nếu có)
    active_group = None
    if current_user:
        active_group = Group.query.filter_by(leader_id=current_user.id).order_by(Group.id.desc()).first()
        if not active_group:
            membership = GroupMember.query.filter_by(student_id=current_user.id).order_by(GroupMember.id.desc()).first()
            if membership:
                active_group = Group.query.get(membership.group_id)
                
    # Lấy danh sách nhóm & đề tài của sinh viên
    my_groups = []
    my_topics = []
    approved_chat_groups = []
    if current_user:
        member_group_ids = [m.group_id for m in GroupMember.query.filter_by(student_id=current_user.id).all()]
        my_groups = Group.query.filter(
            (Group.leader_id == current_user.id) | (Group.id.in_(member_group_ids))
        ).all()
        if my_groups:
            group_ids = [g.id for g in my_groups]
            my_topics = Topic.query.filter(Topic.group_id.in_(group_ids)).order_by(Topic.id.desc()).all()
            for g in my_groups:
                # Chỉ những nhóm có đề tài đã được Khoa/Viện phê duyệt mới có nhóm thảo luận chung chính thức
                is_approved = (g.status == 'approved') or any(t.status == 'approved' for t in g.topics)
                if is_approved:
                    approved_chat_groups.append(g)
        else:
            my_topics = Topic.query.join(Group).filter(Group.leader_id == current_user.id).order_by(Topic.id.desc()).all()

    batches = Batch.query.filter_by(status='active').order_by(Batch.id.desc()).all()
    if not batches:
        batches = Batch.query.order_by(Batch.id.desc()).all()

    # Lấy danh sách giảng viên / Mentor
    from sqlalchemy import func
    mentors = User.query.filter(func.lower(User.role) == 'lecturer').all()
    faculties = {}
    for m in mentors:
        fac = m.faculty or 'Khoa Công nghệ thông tin'
        if fac not in faculties:
            faculties[fac] = []
        faculties[fac].append(m)

    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.is_read.asc(), Notification.created_at.desc()).all() if user_id else []

    return render_template('student.html', 
                           current_user=current_user,
                           current_group=active_group,
                           my_groups=my_groups,
                           approved_chat_groups=approved_chat_groups,
                           my_topics=my_topics,
                           batches=batches,
                           mentors=mentors,
                           faculties=faculties,
                           notifications=notifications)
# Danh sách giảng viên hướng dẫn (Mentor List)
@web_bp.route('/mentors')
def mentors_page():
    return render_template('mentors.html')

# Chi tiết giảng viên (Mentor Detail)
@web_bp.route('/mentor/detail')
@web_bp.route('/mentor/<int:mentor_id>')
def mentor_detail_page(mentor_id=1):
    return render_template('mentor_detail.html', mentor_id=mentor_id)
