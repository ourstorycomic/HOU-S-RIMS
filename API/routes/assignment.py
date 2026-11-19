"""
Task 11 - Logic Xét duyệt: Khoa luân chuyển (chuyển phân công) giảng viên hướng dẫn
dựa trên danh sách yêu cầu đăng ký đề tài.

  GET  /api/assignment/requests?status=pending,faculty_pending   danh sách yêu cầu
  GET  /api/assignment/suggest?topic_id=ID[&all=1]               gợi ý GV (Task 12)
  GET  /api/assignment/mentor-stats                              tải hướng dẫn mọi GV (Task 12)
  POST /api/assignment/reassign                                  chuyển GV (kèm email - Task 13)

Chỉ role faculty / admin (cùng quy ước với topics.py).
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Blueprint, jsonify, request, session

from models import (db, User, Batch, Group, GroupMember, Topic, TopicRegistration,
                    Meeting, AvailabilitySlot, Notification, Message)
from mentor_suggest import (suggest_mentors, mentor_stats, mentor_loads,
                            MAX_TOPICS_PER_MENTOR, get_department)
from event_mailer import emit

assignment_bp = Blueprint('assignment_api', __name__, url_prefix='/api/assignment')

REASSIGNABLE = ('pending', 'faculty_pending', 'approved')
DEFAULT_LIST = ('pending', 'faculty_pending')
LOCAL_TZ = ZoneInfo('Asia/Ho_Chi_Minh')


@assignment_bp.before_request
def require_faculty():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401
    if (session.get('role') or '').lower() not in ('faculty', 'admin'):
        return jsonify({'error': 'Permission denied'}), 403


def _year():
    return session.get('academic_year', '2025-2026')


def _err(msg, code, **extra):
    return jsonify({'error': msg, **extra}), code


@assignment_bp.route('/requests', methods=['GET'])
def list_requests():
    raw = request.args.get('status', '')
    if raw == 'all':
        statuses = REASSIGNABLE
    else:
        statuses = tuple(s for s in raw.split(',') if s in REASSIGNABLE) or DEFAULT_LIST

    topics = (Topic.query.join(Batch, Batch.id == Topic.batch_id)
              .filter(Batch.academic_year == _year(), Batch.status != 'hidden',
                      Topic.status.in_(statuses))
              .order_by(Topic.created_at.desc()).all())

    loads = mentor_loads(_year())
    users = {u.id: u for u in User.query.all()}
    group_ids = [t.group_id for t in topics if t.group_id]
    groups = {g.id: g for g in Group.query.filter(Group.id.in_(group_ids)).all()} if group_ids else {}
    members = {}
    if group_ids:
        for m in GroupMember.query.filter(GroupMember.group_id.in_(group_ids),
                                          GroupMember.status == 'accepted').all():
            u = users.get(m.student_id)
            members.setdefault(m.group_id, []).append(u.full_name if u else f'#{m.student_id}')

    result = []
    for t in topics:
        mentor = users.get(t.mentor_id)
        l = loads.get(t.mentor_id, {'total': 0})
        g = groups.get(t.group_id)
        result.append({
            'topic_id': t.id,
            'code': f'DT-00{t.id}',
            'title': t.title,
            'description': t.description,
            'status': t.status,
            'created_at': t.created_at.strftime('%d/%m/%Y %H:%M') if t.created_at else None,
            'group': {'id': g.id, 'name': g.name, 'members': members.get(g.id, [])} if g else None,
            'mentor': {
                'id': t.mentor_id,
                'full_name': mentor.full_name if mentor else None,
                'faculty': mentor.faculty if mentor else None,
                'department': get_department(mentor) if mentor else None,
                'current_topics': l['total'],
                'quota': MAX_TOPICS_PER_MENTOR,
            },
        })
    return jsonify(result), 200


@assignment_bp.route('/suggest', methods=['GET'])
def suggest():
    topic = db.session.get(Topic, request.args.get('topic_id', type=int) or 0)
    if not topic:
        return _err('Topic not found', 404)
    include_all = request.args.get('all') in ('1', 'true')
    ref = db.session.get(User, topic.mentor_id) if topic.mentor_id else None
    return jsonify({
        'topic_id': topic.id,
        'current_mentor': {
            'id': ref.id,
            'full_name': ref.full_name,
            'faculty': ref.faculty,
            'department': get_department(ref) if ref else ''
        } if ref else None,
        'suggestions': suggest_mentors(topic, _year(), include_all),
    }), 200


@assignment_bp.route('/mentor-stats', methods=['GET'])
def stats():
    return jsonify(mentor_stats(_year())), 200


def _release_group_slots(group_id, old_mentor_id):
    """Hủy các lịch báo cáo SẮP TỚI mà nhóm đã đặt với GV cũ (slot trở lại 'open')."""
    now = datetime.now(LOCAL_TZ).replace(tzinfo=None)
    slots = AvailabilitySlot.query.filter(
        AvailabilitySlot.group_id == group_id, AvailabilitySlot.lecturer_id == old_mentor_id,
        AvailabilitySlot.status == 'booked', AvailabilitySlot.end_time > now).all()
    for s in slots:
        if s.meeting_id:
            m = db.session.get(Meeting, s.meeting_id)
            if m:
                db.session.delete(m)
        s.meeting_id = None
        s.status = 'open'
        s.group_id = None
        s.booked_by_id = None
        s.booked_at = None
    return len(slots)


@assignment_bp.route('/reassign', methods=['POST'])
def reassign():
    """
    Body: {topic_id, new_mentor_id, reason?, force?, confirm_approved?}
      force            : cho phép chuyển cho GV đã đủ quota
      confirm_approved : bắt buộc khi đề tài đã được duyệt chính thức
    """
    d = request.get_json(silent=True) or {}
    if not d.get('topic_id') or not d.get('new_mentor_id'):
        return _err('Thiếu topic_id hoặc new_mentor_id', 400)

    topic = db.session.get(Topic, d['topic_id'])
    if not topic:
        return _err('Không tìm thấy đề tài', 404)
    if topic.status not in REASSIGNABLE:
        return _err(f'Đề tài đang ở trạng thái "{topic.status}", không thể chuyển GV', 400)
    if topic.status == 'approved' and not d.get('confirm_approved'):
        return _err('Đề tài đã được phê duyệt chính thức, cần xác nhận trước khi chuyển GV',
                    409, code='CONFIRM_APPROVED')

    new_m = db.session.get(User, d['new_mentor_id'])
    if not new_m or (new_m.role or '').lower() != 'lecturer':
        return _err('Giảng viên không hợp lệ', 400)
    if new_m.id == topic.mentor_id:
        return _err('Giảng viên mới trùng giảng viên hiện tại', 400)

    load = mentor_loads(_year()).get(new_m.id, {'total': 0})['total']
    if load >= MAX_TOPICS_PER_MENTOR and not d.get('force'):
        return _err(f'{new_m.full_name} đã giữ {load}/{MAX_TOPICS_PER_MENTOR} đề tài', 409, code='MENTOR_FULL')

    old_id = topic.mentor_id
    old_m = db.session.get(User, old_id) if old_id else None
    old_name = old_m.full_name if old_m else 'Chưa có'
    new_name = new_m.full_name
    reason = (d.get('reason') or '').strip()[:300]
    reason_suffix = f" Lý do: {reason}." if reason else ""

    try:
        # Cập nhật giảng viên mới cho đề tài
        topic.mentor_id = new_m.id
        # Khoa trực tiếp phê duyệt phân công, không cần GV mới phải accept lại
        topic.status = 'approved'
        if not topic.defense_status:
            topic.defense_status = 'pending'

        for reg in TopicRegistration.query.filter_by(topic_id=topic.id).all():
            reg.mentor_id = new_m.id
            reg.status = 'approved'

        group = db.session.get(Group, topic.group_id) if topic.group_id else None
        if not group:
            # Tạo nhóm nghiên cứu cho đề tài nếu chưa có
            reg = TopicRegistration.query.filter_by(topic_id=topic.id).first()
            leader_id = reg.group_id if (reg and db.session.get(User, reg.group_id)) else session.get('user_id')
            group = Group(
                name=f"Nhóm {topic.title}",
                batch_id=topic.batch_id,
                leader_id=leader_id,
                mentor_id=new_m.id,
                status='approved'
            )
            db.session.add(group)
            db.session.flush()
            topic.group_id = group.id
        else:
            group.mentor_id = new_m.id
            group.status = 'approved'

        # 1. Gửi thông báo chi tiết (Notification) có đầy đủ danh sách sinh viên nhóm & đề tài
        old_dept = get_department(old_m) if old_m else ''
        new_dept = get_department(new_m) if new_m else ''

        # Thu thập thông tin thành viên nhóm
        members_data = []
        if group:
            seen_uids = set()
            leader = group.leader or (db.session.get(User, group.leader_id) if group.leader_id else None)
            if leader:
                seen_uids.add(leader.id)
                members_data.append({
                    'id': leader.id,
                    'name': leader.full_name or leader.username,
                    'username': leader.username or '',
                    'email': leader.email or '',
                    'faculty': leader.faculty or 'Khoa CNTT',
                    'is_leader': True
                })
            for gm in (group.members or []):
                if gm.student_id not in seen_uids and gm.status in ('accepted', 'joined', 'pending', 'invited'):
                    u = gm.student or db.session.get(User, gm.student_id)
                    if u:
                        seen_uids.add(u.id)
                        members_data.append({
                            'id': u.id,
                            'name': u.full_name or u.username,
                            'username': u.username or '',
                            'email': u.email or '',
                            'faculty': u.faculty or 'Khoa CNTT',
                            'is_leader': False
                        })

        members_rows_html = ""
        for m in members_data:
            role_badge = (
                '<span class="badge bg-primary-subtle text-primary border border-primary-subtle rounded-pill px-2.5 py-0.5 fw-bold" style="font-size: 10.5px;">Trưởng nhóm</span>'
                if m['is_leader'] else
                '<span class="badge bg-secondary-subtle text-secondary border rounded-pill px-2.5 py-0.5" style="font-size: 10.5px;">Thành viên</span>'
            )
            members_rows_html += f"""
            <tr>
                <td class="ps-3 py-2">
                    <div class="fw-bold text-dark">{m['name']}</div>
                    <div class="text-muted" style="font-size: 11px;">{m['faculty']}</div>
                </td>
                <td class="py-2 font-monospace text-secondary fw-semibold">{m['username']}</td>
                <td class="py-2 text-muted">{m['email']}</td>
                <td class="pe-3 py-2 text-end">{role_badge}</td>
            </tr>"""

        group_members_card = f"""
        <div class="p-3 bg-white rounded-3 border mb-3">
            <div class="d-flex align-items-center justify-content-between mb-2 pb-2 border-bottom">
                <span class="fw-bold text-dark small">
                    <i class="fa-solid fa-users text-primary me-1.5"></i>THÀNH VIÊN NHÓM NGHIÊN CỨU ({len(members_data)} thành viên)
                </span>
                <span class="badge bg-primary-subtle text-primary border border-primary-subtle rounded-pill px-2.5 py-1">{group.name if group else 'Chưa có tên nhóm'}</span>
            </div>
            <div class="table-responsive">
                <table class="table table-sm table-hover align-middle mb-0" style="font-size: 12.5px;">
                    <thead class="bg-light text-muted" style="font-size: 11px; text-transform: uppercase;">
                        <tr>
                            <th class="ps-3 py-1.5">Sinh viên</th>
                            <th class="py-1.5">MSSV</th>
                            <th class="py-1.5">Email</th>
                            <th class="pe-3 py-1.5 text-end">Vai trò</th>
                        </tr>
                    </thead>
                    <tbody>
                        {members_rows_html if members_rows_html else '<tr><td colspan=\"4\" class=\"text-center text-muted py-3\">Chưa có thành viên nào trong nhóm</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>"""

        batch = db.session.get(Batch, topic.batch_id) if topic.batch_id else None
        batch_name = batch.name if batch else 'Đợt NCKH Sinh viên'
        acad_year = batch.academic_year if batch else _year()

        topic_overview_card = f"""
        <div class="p-3 bg-white rounded-3 border mb-3">
            <div class="d-flex align-items-center justify-content-between mb-2">
                <span class="badge bg-primary-subtle text-primary border border-primary-subtle rounded-pill px-2.5 py-1 fw-bold" style="font-size: 11px;"><i class="fa-solid fa-bookmark me-1"></i>MÃ ĐT: DT-00{topic.id}</span>
                <span class="badge bg-success-subtle text-success border border-success-subtle rounded-pill px-2.5 py-1 fw-bold" style="font-size: 11px;">{topic.status.upper()}</span>
            </div>
            <div class="fw-bold text-dark mb-1" style="font-size: 15px; line-height: 1.5;">{topic.title}</div>
            <div class="text-muted small mb-2" style="font-size: 11.5px;">
                <i class="fa-regular fa-calendar-check me-1 text-primary"></i>{batch_name} ({acad_year})
                {f' • <i class=\"fa-solid fa-layer-group ms-1 me-1 text-secondary\"></i>{topic.field}' if topic.field else ''}
            </div>
            <div class="row g-2 pt-2 border-top text-muted small" style="font-size: 12px;">
                <div class="col-sm-6">
                    <span class="text-muted">Cán bộ phụ trách trước:</span> <br>
                    <strong class="text-dark"><i class="fa-solid fa-user-tie me-1 text-secondary"></i>{old_name}</strong> {f'<span class=\"text-muted small\">({old_dept})</span>' if old_dept else ''}
                </div>
                <div class="col-sm-6">
                    <span class="text-muted">Giảng viên tiếp nhận mới:</span> <br>
                    <strong class="text-primary"><i class="fa-solid fa-user-check me-1 text-primary"></i>{new_name}</strong> {f'<span class=\"text-primary small\">({new_dept})</span>' if new_dept else ''}
                </div>
            </div>
        </div>"""

        reason_box_html = f"""
        <div class="p-3 rounded-3 mb-3" style="background: #fffbeb; border: 1px solid #fde68a; border-left: 4px solid #f59e0b;">
            <div class="fw-bold mb-1.5 d-flex align-items-center gap-1.5" style="color: #b45309; font-size: 12px;">
                <i class="fa-solid fa-comment-dots"></i> Ý KIẾN CHỈ ĐẠO & GHI CHÚ TỪ KHOA:
            </div>
            <div style="font-size: 13.5px; color: #334155; line-height: 1.6;">
                {reason}
            </div>
        </div>""" if reason else ""

        # A. Gửi cho toàn bộ sinh viên trong nhóm
        student_ids = set()
        if group and group.leader_id:
            student_ids.add(group.leader_id)
        if group:
            for gm in group.members:
                if gm.student_id:
                    student_ids.add(gm.student_id)

        student_notif = (
            f"<p class='mb-2 text-dark' style='font-size: 13.5px;'>Khoa Công nghệ thông tin đã ban hành quyết định điều chuyển Giảng viên hướng dẫn đề tài <strong>'{topic.title}'</strong> của nhóm từ Thầy/Cô <strong>{old_name}</strong> sang Thầy/Cô <strong>{new_name}</strong> ({new_dept}).</p>"
            f"{topic_overview_card}"
            f"{reason_box_html}"
            f"{group_members_card}"
            f"<a href='/student#s-chat' class='btn btn-primary btn-sm rounded-pill mt-2 fw-bold'>"
            f"<i class='fa-solid fa-comments me-1'></i>Vào Nhóm Chat trao đổi</a>"
        )
        for sid in student_ids:
            db.session.add(Notification(user_id=sid, content=student_notif))

        # B. Gửi cho Giảng viên cũ
        if old_id and old_id != new_m.id:
            old_mentor_notif = (
                f"<p class='mb-2 text-dark' style='font-size: 13.5px;'>Khoa Công nghệ thông tin đã điều chuyển đề tài NCKH <strong>'{topic.title}'</strong> từ Thầy/Cô sang Thầy/Cô <strong>{new_name}</strong> ({new_dept}).</p>"
                f"{topic_overview_card}"
                f"{reason_box_html}"
                f"{group_members_card}"
                f"<a href='/lecturer/progress' class='btn btn-outline-primary btn-sm rounded-pill mt-2 fw-bold'>"
                f"<i class='fa-solid fa-bars-progress me-1'></i>Xem danh sách đề tài</a>"
            )
            db.session.add(Notification(user_id=old_id, content=old_mentor_notif))

        # C. Gửi cho Giảng viên mới
        new_mentor_notif = (
            f"<p class='mb-2 text-dark' style='font-size: 13.5px;'>Khoa Công nghệ thông tin đã ban hành quyết định phân công Thầy/Cô làm Giảng viên hướng dẫn đề tài NCKH <strong>'{topic.title}'</strong> (điều chuyển từ Thầy/Cô <strong>{old_name}</strong>).</p>"
            f"{topic_overview_card}"
            f"{reason_box_html}"
            f"{group_members_card}"
            f"<a href='/lecturer/chat?group_id={group.id if group else ''}' class='btn btn-primary btn-sm rounded-pill mt-2 fw-bold'>"
            f"<i class='fa-solid fa-comments me-1'></i>Vào Nhóm Chat trao đổi</a>"
        )
        db.session.add(Notification(user_id=new_m.id, content=new_mentor_notif))

        # 2. Tạo tin nhắn nhóm chat tự động kết nối sinh viên và giảng viên mới
        welcome_chat = Message(
            sender_id=session.get('user_id', new_m.id),
            group_id=group.id,
            content=(
                f"📢 [Thông báo hệ thống] Khoa đã điều chuyển Giảng viên hướng dẫn của nhóm từ "
                f"Thầy/Cô {old_name} sang Thầy/Cô {new_name}. "
                f"Nhóm chat đã sẵn sàng để Thầy/Cô và các bạn sinh viên bắt đầu trao đổi!"
            ),
            message_type='text',
            timestamp=datetime.utcnow()
        )
        db.session.add(welcome_chat)

        released = _release_group_slots(group.id, old_id) if (group.id and old_id) else 0
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return _err(str(e), 500)

    # Gửi email thông báo không block request
    emit('mentor_reassigned', topic_id=topic.id, old_mentor_id=old_id,
         new_mentor_id=new_m.id, reason=reason, released_slots=released, inapp=False)
    return jsonify({
        'message': f'Đã điều chuyển đề tài sang Thầy/Cô {new_name} và cập nhật nhóm chat thành công!',
        'topic_id': topic.id,
        'mentor_id': new_m.id,
        'mentor_name': new_name,
        'status': topic.status,
        'released_slots': released
    }), 200
