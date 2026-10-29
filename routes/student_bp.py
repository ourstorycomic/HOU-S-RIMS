from flask import Blueprint, render_template, session, redirect, url_for, request
from models import db, User, Batch, Group, Topic, GroupMember, Notification, Milestone, Progress, Skill, Achievement, Experience, Meeting, Submission, Council, CouncilMember
from datetime import datetime
from sqlalchemy import func
import re

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.before_request
def require_student():
    if session.get('role') != 'student':
        return redirect(url_for('auth.login'))

@student_bp.context_processor
def inject_common_data():
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all() if user_id else []
    current_year = session.get('academic_year', '2025-2026')
    active_batch = Batch.query.filter_by(academic_year=current_year, status='active').first()
    if not active_batch:
        active_batch = Batch.query.filter_by(status='active').order_by(Batch.id.desc()).first()
    global_my_groups_count = Group.query.join(GroupMember).join(Batch).filter(GroupMember.student_id == user_id, Batch.status == 'active').count() if user_id else 0
    all_students = User.query.filter(User.role.ilike('student')).all()

    # Nhóm chat đã duyệt
    approved_chat_groups = []
    if current_user and active_batch:
        member_group_ids = [m.group_id for m in GroupMember.query.join(Group).filter(
            GroupMember.student_id == current_user.id,
            GroupMember.status.in_(['accepted', 'joined']),
            Group.batch_id == active_batch.id
        ).all()]
        my_groups = Group.query.filter(
            Group.batch_id == active_batch.id,
            (Group.leader_id == current_user.id) | (Group.id.in_(member_group_ids))
        ).all() if (member_group_ids or Group.query.filter_by(leader_id=current_user.id, batch_id=active_batch.id).first()) else []
        for g in my_groups:
            if (g.status == 'approved') or any(t.status == 'approved' for t in g.topics):
                approved_chat_groups.append(g)

    return dict(
        current_user=current_user,
        notifications=notifications,
        current_time=datetime.utcnow(),
        active_batch=active_batch,
        global_my_groups_count=global_my_groups_count,
        all_students=all_students,
        approved_chat_groups=approved_chat_groups
    )

@student_bp.route('/')
def index():
    return redirect('/student#s-explore')

@student_bp.route('/dashboard')
def dashboard():
    return redirect('/student#s-explore')

@student_bp.route('/mentors')
def mentors():
    return redirect('/student#s-mentors')

@student_bp.route('/members')
def members():
    return redirect('/student#s-members')

@student_bp.route('/portfolio')
def portfolio():
    return redirect('/student#s-profile')

@student_bp.route('/register')
def register():
    return redirect('/student#s-register')

@student_bp.route('/progress')
def progress():
    return redirect('/student#s-group')

@student_bp.route('/calendar')
def calendar():
    return redirect('/student#s-calendar')

@student_bp.route('/book-slot')
def book_slot():
    return render_template('student/book_slot.html')

@student_bp.route('/chat')
def chat():
    params = []
    if request.args.get('target_id'):
        params.append(f"target_id={request.args.get('target_id')}")
    if request.args.get('mentor'):
        params.append(f"mentor={request.args.get('mentor')}")
    query_str = ('?' + '&'.join(params)) if params else ''
    return redirect(f"/student{query_str}#s-chat")

@student_bp.route('/result')
def result():
    return redirect('/student#s-register')

@student_bp.route('/templates')
def templates_page():
    return redirect('/student#s-templates')

@student_bp.route('/submit')
def submit():
    return redirect('/student#s-submit')
