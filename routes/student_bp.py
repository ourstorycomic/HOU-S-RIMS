from flask import Blueprint, render_template, session, redirect, url_for, request
from models import db, User, Batch, Group, Topic, GroupMember, Notification, Milestone, Progress, Skill, Achievement, Experience
from datetime import datetime
from sqlalchemy import func

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.before_request
def require_student():
    if session.get('role') != 'student':
        return redirect(url_for('auth.login'))

@student_bp.context_processor
def inject_common_data():
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.is_read.asc(), Notification.created_at.desc()).all() if user_id else []
    current_year = session.get('academic_year', '2025-2026')
    active_batch = Batch.query.filter_by(academic_year=current_year, status='active').first()
    global_my_groups_count = Group.query.join(GroupMember).join(Batch).filter(GroupMember.student_id == user_id, Batch.status == 'active').count() if user_id else 0
    all_students = User.query.filter(User.role.ilike('student')).all()
    return dict(current_user=current_user, notifications=notifications, current_time=datetime.utcnow(), active_batch=active_batch, global_my_groups_count=global_my_groups_count, all_students=all_students)

@student_bp.route('/')
def index():
    return redirect(url_for('student.dashboard'))

@student_bp.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    pending_invitations = []
    if user_id:
        pending_invitations = GroupMember.query.filter_by(student_id=user_id, status='pending').all()
    return render_template('student/dashboard.html', pending_invitations=pending_invitations)

@student_bp.route('/portfolio')
def portfolio():
    user_id = session.get('user_id')
    skills = Skill.query.filter_by(student_id=user_id).all()
    achievements = Achievement.query.filter_by(student_id=user_id).all()
    experiences = Experience.query.filter_by(student_id=user_id).all()
    return render_template('student/portfolio.html', skills=skills, achievements=achievements, experiences=experiences)

@student_bp.route('/register')
def register():
    user_id = session.get('user_id')
    batches = Batch.query.filter_by(status='active').all()
    mentors = User.query.filter(func.lower(User.role) == 'lecturer').all()
    my_groups = Group.query.join(GroupMember).join(Batch).filter(GroupMember.student_id == user_id, Batch.status == 'active').all()
    my_topics = []
    if my_groups:
        group_ids = [g.id for g in my_groups]
        my_topics = Topic.query.join(Batch).filter(Topic.group_id.in_(group_ids), Batch.status == 'active').all()
    return render_template('student/register.html', batches=batches, mentors=mentors, my_groups=my_groups, my_topics=my_topics)

@student_bp.route('/progress')
def progress():
    user_id = session.get('user_id')
    my_groups = Group.query.join(GroupMember).join(Batch).filter(GroupMember.student_id == user_id, Batch.status == 'active').all()
    my_topics = []
    topic_milestones = []
    if my_groups:
        group_ids = [g.id for g in my_groups]
        my_topics = Topic.query.join(Batch).filter(Topic.group_id.in_(group_ids), Batch.status == 'active').all()
        if my_topics:
            topic_milestones = Milestone.query.filter_by(topic_id=my_topics[0].id).order_by(Milestone.deadline.asc()).all()
            total_progress = 0
            for m in topic_milestones:
                p = Progress.query.filter_by(milestone_id=m.id).order_by(Progress.updated_at.desc()).first()
                m.progress_pct = p.percentage if p else 0
                total_progress += m.progress_pct
            if len(topic_milestones) > 0:
                total_progress = total_progress // len(topic_milestones)
            my_topics[0].total_progress = total_progress
            
    from models import Meeting
    my_meetings = Meeting.query.filter_by(organizer_id=user_id).order_by(Meeting.start_time.desc()).all()
    
    return render_template('student/progress.html', my_groups=my_groups, my_topics=my_topics, topic_milestones=topic_milestones, my_meetings=my_meetings)

@student_bp.route('/calendar')
def calendar():
    return render_template('student/calendar.html')

@student_bp.route('/chat')
def chat():
    user_id = session.get('user_id')
    my_groups = Group.query.join(GroupMember).join(Topic, Topic.group_id == Group.id).join(Batch, Batch.id == Group.batch_id).filter(
        GroupMember.student_id == user_id, 
        GroupMember.status == 'accepted', 
        Batch.status == 'active',
        Topic.status == 'approved'
    ).all()
    
    target_id = request.args.get('target_id')
    target_user = None
    if target_id:
        target_user = User.query.get(target_id)
        
    return render_template('student/chat.html', my_groups=my_groups, target_user=target_user)

@student_bp.route('/result')
def result():
    return render_template('student/result.html')

@student_bp.route('/templates')
def templates_page():
    return render_template('student/templates.html')

@student_bp.route('/submit')
def submit():
    user_id = session.get('user_id')
    my_groups = Group.query.join(GroupMember).join(Batch).filter(GroupMember.student_id == user_id, Batch.status == 'active').all()
    my_topics = []
    if my_groups:
        group_ids = [g.id for g in my_groups]
        my_topics = Topic.query.join(Batch).filter(Topic.group_id.in_(group_ids), Batch.status == 'active').all()
    topic_id = my_topics[0].id if my_topics else 1
    milestones = Milestone.query.filter_by(topic_id=topic_id).all() if my_topics else []
    return render_template('student/submit.html', topic_id=topic_id, milestones=milestones)
