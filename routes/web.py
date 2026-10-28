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
    if role == 'student': return redirect(url_for('web.student_page'))
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
    pending_invitations = []
    sent_pending_invitations = []
    skills = []
    achievements = []
    experiences = []

    if current_user:
        from models import Skill, Achievement, Experience
        member_group_ids = [m.group_id for m in GroupMember.query.filter_by(student_id=current_user.id).all()]
        my_groups = Group.query.filter(
            (Group.leader_id == current_user.id) | (Group.id.in_(member_group_ids))
        ).all()
        if my_groups:
            group_ids = [g.id for g in my_groups]
            my_topics = Topic.query.filter(Topic.group_id.in_(group_ids)).order_by(Topic.id.desc()).all()
            for g in my_groups:
                is_approved = (g.status == 'approved') or any(t.status == 'approved' for t in g.topics)
                if is_approved:
                    approved_chat_groups.append(g)
        else:
            my_topics = Topic.query.join(Group).filter(Group.leader_id == current_user.id).order_by(Topic.id.desc()).all()

        pending_invitations = GroupMember.query.filter(
            GroupMember.student_id == current_user.id,
            GroupMember.status.in_(['pending', 'invited'])
        ).all()

        sent_pending_invitations = GroupMember.query.join(Group).filter(
            Group.leader_id == current_user.id,
            GroupMember.student_id != current_user.id,
            GroupMember.status.in_(['pending', 'invited'])
        ).all()

        skills = Skill.query.filter_by(student_id=current_user.id).all()
        achievements = Achievement.query.filter_by(student_id=current_user.id).all()
        experiences = Experience.query.filter_by(student_id=current_user.id).all()

    batches = Batch.query.filter_by(status='active').order_by(Batch.id.desc()).all()
    if not batches:
        batches = Batch.query.order_by(Batch.id.desc()).all()

    from sqlalchemy import func
    mentors = User.query.filter(func.lower(User.role) == 'lecturer').all()
    faculties = {}
    for m in mentors:
        fac = m.faculty or 'Khoa Công nghệ thông tin'
        if fac not in faculties:
            faculties[fac] = []
        faculties[fac].append(m)

    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.is_read.asc(), Notification.created_at.desc()).all() if user_id else []

    # Danh sách sinh viên cho tính năng Tìm kiếm thành viên (ghép nhóm NCKH)
    all_students = User.query.filter(func.lower(User.role) == 'student').order_by(User.id.asc()).all()
    students_list = []
    major_map = {
        '24A1001D0341': 'Kỹ thuật phần mềm',
        '24A1001D0391': 'Trí tuệ nhân tạo',
        '24A1001D0343': 'Hệ thống thông tin',
        '24A1001D0344': 'Khoa học máy tính',
        '24A1001D0345': 'Mạng máy tính & ATTT',
        '24A1001D0346': 'Trí tuệ nhân tạo',
        '24A1001D0347': 'Kỹ thuật phần mềm',
        '24A1001D0348': 'Hệ thống thông tin',
    }
    
    for s in all_students:
        s_skills = [sk.name for sk in Skill.query.filter_by(student_id=s.id).all()]
        major = major_map.get(s.student_id, 'Kỹ thuật phần mềm')
        
        # Check active group membership
        accepted_memberships = GroupMember.query.filter_by(student_id=s.id, status='accepted').all()
        lead_groups = Group.query.filter_by(leader_id=s.id).all()
        
        has_group = bool(accepted_memberships or lead_groups)
        group_member_count = 0
        if lead_groups:
            group_member_count = GroupMember.query.filter(GroupMember.group_id == lead_groups[0].id, GroupMember.status.in_(['accepted', 'joined'])).count() + 1
        elif accepted_memberships:
            group_member_count = GroupMember.query.filter(GroupMember.group_id == accepted_memberships[0].group_id, GroupMember.status.in_(['accepted', 'joined'])).count() + 1
            
        group_status = 'seeking'
        group_status_label = 'Đang tìm nhóm'
        if has_group:
            if group_member_count >= 5:
                group_status = 'full'
                group_status_label = 'Đã đủ nhóm'
            else:
                group_status = 'open'
                group_status_label = f'Nhóm còn chỗ ({group_member_count}/5)'
                
        students_list.append({
            'user': s,
            'major': major,
            'skills': s_skills,
            'has_group': has_group,
            'group_status': group_status,
            'group_status_label': group_status_label,
            'group_member_count': group_member_count
        })

    return render_template('student.html', 
                           current_user=current_user,
                           current_group=active_group,
                           my_groups=my_groups,
                           approved_chat_groups=approved_chat_groups,
                           my_topics=my_topics,
                           batches=batches,
                           mentors=mentors,
                           faculties=faculties,
                           notifications=notifications,
                           pending_invitations=pending_invitations,
                           sent_pending_invitations=sent_pending_invitations,
                           skills=skills,
                           achievements=achievements,
                           experiences=experiences,
                           students_list=students_list)

# Danh sách giảng viên hướng dẫn (Mentor List)
@web_bp.route('/mentors')
def mentors_page():
    return render_template('mentors.html')

# Chi tiết giảng viên (Mentor Detail)
@web_bp.route('/mentor/detail')
@web_bp.route('/mentor/<int:mentor_id>')
def mentor_detail_page(mentor_id=1):
    return render_template('mentor_detail.html', mentor_id=mentor_id)
