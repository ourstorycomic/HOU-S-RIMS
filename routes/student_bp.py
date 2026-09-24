from flask import Blueprint, render_template, session, redirect, url_for
from models import db, User, Batch, Group, Topic, GroupMember, Notification, Milestone, Progress, Skill, Achievement, Experience
from datetime import datetime

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
    return dict(current_user=current_user, notifications=notifications, current_time=datetime.utcnow())

@student_bp.route('/')
def index():
    return redirect(url_for('student.dashboard'))

@student_bp.route('/dashboard')
def dashboard():
    return render_template('student/dashboard.html')

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
    mentors = User.query.filter_by(role='lecturer').all()
    my_groups = Group.query.join(GroupMember).filter(GroupMember.student_id == user_id).all()
    my_topics = []
    if my_groups:
        group_ids = [g.id for g in my_groups]
        my_topics = Topic.query.filter(Topic.group_id.in_(group_ids)).all()
    return render_template('student/register.html', batches=batches, mentors=mentors, my_groups=my_groups, my_topics=my_topics)

@student_bp.route('/progress')
def progress():
    user_id = session.get('user_id')
    my_groups = Group.query.join(GroupMember).filter(GroupMember.student_id == user_id).all()
    my_topics = []
    topic_milestones = []
    if my_groups:
        group_ids = [g.id for g in my_groups]
        my_topics = Topic.query.filter(Topic.group_id.in_(group_ids)).all()
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
    my_groups = Group.query.join(GroupMember).filter(GroupMember.student_id == user_id).all()
    return render_template('student/chat.html', my_groups=my_groups)

@student_bp.route('/result')
def result():
    return render_template('student/result.html')

@student_bp.route('/templates')
def templates_page():
    return render_template('student/templates.html')

@student_bp.route('/submit')
def submit():
    user_id = session.get('user_id')
    my_groups = Group.query.join(GroupMember).filter(GroupMember.student_id == user_id).all()
    my_topics = []
    if my_groups:
        group_ids = [g.id for g in my_groups]
        my_topics = Topic.query.filter(Topic.group_id.in_(group_ids)).all()
    topic_id = my_topics[0].id if my_topics else 1
    milestones = Milestone.query.filter_by(topic_id=topic_id).all() if my_topics else []
    return render_template('student/submit.html', topic_id=topic_id, milestones=milestones)
