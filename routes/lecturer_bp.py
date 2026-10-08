from flask import Blueprint, render_template, session, redirect, url_for, request
from models import db, User, Batch, Group, Topic, TopicRegistration, Council, GroupMember, Milestone, Progress, Submission
from datetime import datetime

lecturer_bp = Blueprint('lecturer', __name__, url_prefix='/lecturer')

@lecturer_bp.before_request
def require_lecturer():
    if session.get('role') != 'lecturer':
        return redirect(url_for('auth.login'))

@lecturer_bp.context_processor
def inject_common_data():
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    current_year = session.get('academic_year', '2025-2026')
    active_batch = Batch.query.filter_by(academic_year=current_year, status='active').first()
    
    global_pending_topics_count = Topic.query.join(Batch).filter(Topic.mentor_id == user_id, Topic.status == 'pending', Batch.status == 'active').count() if user_id else 0
    global_my_groups_count = Topic.query.join(Batch).filter(Topic.mentor_id == user_id, Topic.status == 'approved', Topic.group_id.isnot(None), Batch.status == 'active').count() if user_id else 0
    
    from models import Notification
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all() if user_id else []
    
    return dict(current_user=current_user, current_time=datetime.utcnow(), active_batch=active_batch, global_pending_topics_count=global_pending_topics_count, global_my_groups_count=global_my_groups_count, notifications=notifications)

@lecturer_bp.route('/')
def index():
    return redirect(url_for('lecturer.dashboard'))

@lecturer_bp.route('/dashboard')
def dashboard():
    return render_template('lecturer/dashboard.html')

@lecturer_bp.route('/approve')
def approve():
    user_id = session.get('user_id')
    pending_topics = Topic.query.join(Batch).filter(Topic.mentor_id == user_id, Topic.status == 'pending', Batch.status == 'active').all()
    approved_topics = Topic.query.join(Batch).filter(Topic.mentor_id == user_id, Topic.status != 'pending', Batch.status == 'active').all()
    return render_template('lecturer/approve.html', pending_topics=pending_topics, approved_topics=approved_topics)

@lecturer_bp.route('/progress')
def progress():
    user_id = session.get('user_id')
    my_topics = Topic.query.join(Batch).filter(Topic.mentor_id == user_id, Topic.status.in_(['faculty_pending', 'approved']), Batch.status == 'active').all()
    all_milestones = []
    
    if my_topics:
        # Get progress for all topics mentored by this lecturer
        for t in my_topics:
            t.submissions = Submission.query.filter_by(topic_id=t.id).order_by(Submission.submitted_at.desc()).all()
            t.milestones_list = Milestone.query.filter_by(topic_id=t.id).order_by(Milestone.deadline.asc()).all()
            total_progress = 0
            for m in t.milestones_list:
                p = Progress.query.filter_by(milestone_id=m.id).order_by(Progress.updated_at.desc()).first()
                m.progress_pct = p.percentage if p else 0
                total_progress += m.progress_pct
                all_milestones.append(m)
            
            if len(t.milestones_list) > 0:
                total_progress = total_progress // len(t.milestones_list)
            t.total_progress = total_progress
            
    return render_template('lecturer/progress.html', all_mentored_topics=my_topics, all_milestones=all_milestones)

@lecturer_bp.route('/chat')
def chat():
    user_id = session.get('user_id')
    # Lecturers get groups associated with the topics they mentor that are approved
    my_topics = Topic.query.join(Batch).filter(Topic.mentor_id == user_id, Topic.status == 'approved', Batch.status == 'active').all()
    group_ids = [t.group_id for t in my_topics if t.group_id]
    my_groups = Group.query.filter(Group.id.in_(group_ids)).all() if group_ids else []
    
    target_id = request.args.get('target_id')
    target_user = None
    if target_id:
        target_user = User.query.get(target_id)
        
    return render_template('lecturer/chat.html', my_groups=my_groups, target_user=target_user)

@lecturer_bp.route('/calendar')
def calendar():
    user_id = session.get('user_id')
    my_topics = Topic.query.join(Batch).filter(Topic.mentor_id == user_id, Topic.status == 'approved', Batch.status == 'active').all()
    return render_template('lecturer/calendar.html', my_topics=my_topics)

@lecturer_bp.route('/council')
def council():
    user_id = session.get('user_id')
    from models import CouncilMember, Council
    # Find all councils where this lecturer is a member
    memberships = CouncilMember.query.filter_by(mentor_id=user_id).all()
    council_ids = [m.council_id for m in memberships]
    my_councils = Council.query.filter(Council.id.in_(council_ids)).all() if council_ids else []
    return render_template('lecturer/council.html', my_councils=my_councils)
