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
    approved_topics = Topic.query.join(Batch).filter(Topic.mentor_id == user_id, Topic.status.in_(['faculty_pending', 'approved']), Batch.status == 'active').all()
    return render_template('lecturer/approve.html', pending_topics=pending_topics, approved_topics=approved_topics)

@lecturer_bp.route('/progress')
def progress():
    user_id = session.get('user_id')
    my_topics = Topic.query.filter(Topic.mentor_id == user_id, Topic.status.in_(['faculty_pending', 'approved'])).order_by(Topic.id.desc()).all()
    all_milestones = []
    
    if my_topics:
        from models import Evaluation
        # Get progress for all topics mentored by this lecturer
        for t in my_topics:
            t.submissions = Submission.query.filter_by(topic_id=t.id).order_by(
                Submission.submitted_at.desc(), 
                Submission.version.desc(), 
                Submission.id.desc()
            ).all()
            t.milestones_list = Milestone.query.filter_by(topic_id=t.id).order_by(Milestone.deadline.asc()).all()
            
            # Đánh dấu bản nộp mới nhất vs bản nộp cũ (cho từng loại bài nộp/cột mốc)
            latest_by_group = {}
            for s in t.submissions:
                group_key = (s.type, s.milestone_id)
                if group_key not in latest_by_group:
                    latest_by_group[group_key] = s
                    s.is_latest = True
                    s.latest_version = s.version or 1
                else:
                    s.is_latest = False
                    s.latest_version = latest_by_group[group_key].version or 1
            
            # Phân loại bài nộp theo chu trình tiến độ NCKH
            outline_subs = [s for s in t.submissions if s.type == 'outline']
            progress_subs = [s for s in t.submissions if s.type == 'progress']
            final_subs = [s for s in t.submissions if s.type in ['final', 'slide']]
            
            latest_outline = next((s for s in outline_subs if getattr(s, 'is_latest', False)), None)
            latest_progress = next((s for s in progress_subs if getattr(s, 'is_latest', False)), None)
            latest_final = next((s for s in final_subs if getattr(s, 'is_latest', False)), None)

            t.outline_status = latest_outline.status if latest_outline else 'none'
            t.progress_status = latest_progress.status if latest_progress else 'none'
            t.final_status = latest_final.status if latest_final else 'none'
            
            evaluations = Evaluation.query.filter_by(topic_id=t.id).all()
            t.is_evaluated = len(evaluations) > 0
            
            # Tính toán tiến độ tổng thể theo Chu trình tiến độ thực của đề tài NCKH
            # 1. Giai đoạn Phê duyệt đề tài (Trọng số 20%):
            pct = 20 if t.status == 'approved' else (12 if t.status == 'faculty_pending' else 5)
            
            # 2. Giai đoạn Đề cương chi tiết (Trọng số 20%):
            if t.outline_status == 'approved':
                pct += 20
            elif t.outline_status == 'submitted':
                pct += 10
                
            # 3. Giai đoạn Thực hiện & Báo cáo tiến độ (Trọng số 30%):
            if t.milestones_list:
                ms_pct_sum = 0
                for m in t.milestones_list:
                    p = Progress.query.filter_by(milestone_id=m.id).order_by(Progress.updated_at.desc()).first()
                    m.progress_pct = p.percentage if p else 0
                    ms_pct_sum += m.progress_pct
                    all_milestones.append(m)
                avg_ms = ms_pct_sum / len(t.milestones_list)
                pct += int(round(avg_ms * 0.3))
            else:
                if t.progress_status == 'approved':
                    pct += 30
                elif t.progress_status == 'submitted':
                    pct += 15
                    
            # 4. Giai đoạn Báo cáo tổng kết & Slide (Trọng số 20%):
            if t.final_status == 'approved':
                pct += 20
            elif t.final_status == 'submitted':
                pct += 10
                
            # 5. Giai đoạn Nghiệm thu & Bảo vệ hội đồng (Trọng số 10%):
            if t.is_evaluated:
                pct += 10
                
            t.total_progress = min(max(pct, 0), 100)
            
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
