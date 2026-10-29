"""
Task 13 - Service gửi mail độc lập, kích hoạt theo sự kiện.

Đặt cạnh app.py (cùng cấp với email_utils.py). Gửi mail qua email_utils.send_email_async
có sẵn của dự án, nên cấu hình SMTP vẫn nằm ở email_utils/.env như cũ.

Dùng trong route (GỌI SAU khi đã db.session.commit()):

    from event_mailer import emit
    emit('mentor_reassigned', topic_id=t.id, old_mentor_id=1, new_mentor_id=2)

Các sự kiện:
    mentor_reassigned     Khoa chuyển GV hướng dẫn                (mail + thông báo)
    topic_mentor_accepted GV đồng ý hướng dẫn -> chờ Khoa duyệt   (mail + thông báo)
    topic_faculty_decision Khoa duyệt / từ chối đề tài            (mail + thông báo)
    slot_booked / slot_cancelled  lịch báo cáo tiến độ            (chỉ mail; slots.py đã tự tạo thông báo)

Quy tắc hiển thị tên (cấu hình MASK_MENTOR_FOR_STUDENT trong .env, mặc định true):
    - gửi cho SINH VIÊN : ẩn tên GV, chỉ ghi "Giảng viên hướng dẫn"
    - gửi cho GIẢNG VIÊN: hiện FULL tên (tên GV liên quan và họ tên đầy đủ các sinh viên trong nhóm)

emit() KHÔNG BAO GIỜ ném lỗi ra ngoài: lỗi gửi mail chỉ được log, request chính vẫn thành công.
"""
import html
import logging
import os

from models import db, User, Topic, Group, GroupMember, Notification

log = logging.getLogger(__name__)

BASE_URL = os.getenv('APP_BASE_URL', 'http://127.0.0.1:5000').rstrip('/')
MASK_MENTOR_FOR_STUDENT = os.getenv('MASK_MENTOR_FOR_STUDENT', 'true').strip().lower() in ('1', 'true', 'yes', 'on')
HIDDEN_MENTOR_LABEL = 'Giảng viên hướng dẫn'


# ---------- helpers ----------
def _esc(s):
    return html.escape(str(s if s is not None else ''))


def _b(s):
    return f'<strong>{_esc(s)}</strong>'


def _is_student(user):
    return (user.role or '').lower() == 'student'


def mentor_display_name(mentor, recipient):
    """Tên GV hiển thị cho `recipient` (ẩn nếu recipient là sinh viên)."""
    if mentor is None:
        return 'Chưa phân công'
    if _is_student(recipient) and MASK_MENTOR_FOR_STUDENT:
        return HIDDEN_MENTOR_LABEL
    return mentor.full_name


def _group_students(group_id):
    if not group_id:
        return []
    ids = [m.student_id for m in GroupMember.query.filter_by(group_id=group_id, status='accepted').all()]
    return User.query.filter(User.id.in_(ids)).all() if ids else []


def _group_line(group_id):
    """[ 'Nhóm: X — sinh viên: Họ tên A, Họ tên B' ] - full tên, CHỈ dùng trong mail gửi GV."""
    group = db.session.get(Group, group_id) if group_id else None
    if not group:
        return []
    names = ', '.join(s.full_name for s in _group_students(group_id))
    return [f'Nhóm: {_b(group.name)}' + (f' — sinh viên: {_esc(names)}' if names else '')]


def _fmt_range(start, end):
    return f"{start.strftime('%H:%M')}-{end.strftime('%H:%M')} ngày {start.strftime('%d/%m/%Y')}"


def _role_home(user):
    role = (user.role or '').lower()
    return {'student': '/student/progress', 'lecturer': '/lecturer/progress'}.get(role, '/faculty/topics')


def _msg(user, subject, heading, color, paragraphs, link=None, link_label='Xem chi tiết'):
    """Một thông điệp gửi tới 1 người. `paragraphs` là HTML đã escape."""
    return {'user': user, 'subject': subject, 'heading': heading, 'color': color,
            'paragraphs': paragraphs, 'link': link or _role_home(user), 'link_label': link_label}


# ---------- dựng nội dung ----------
def _inapp_html(m):
    body = ''.join(f'<p>{p}</p>' for p in m['paragraphs'])
    return (f"<p>Xin chào {_b(m['user'].full_name)},</p>{body}"
            f"<a href='{_esc(m['link'])}' class='btn btn-primary rounded-pill btn-sm mt-2'>{_esc(m['link_label'])}</a>")


def _email_html(m):
    body = ''.join(f'<p>{p}</p>' for p in m['paragraphs'])
    return f"""
    <div style='font-family: Arial, sans-serif; padding: 20px; color: #333;'>
        <h2 style='color: {m["color"]};'>{_esc(m['heading'])}</h2>
        <p>Xin chào {_b(m['user'].full_name)},</p>
        {body}
        <a href='{BASE_URL}{_esc(m['link'])}' style='display: inline-block; padding: 10px 20px; background-color: {m["color"]}; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px;'>{_esc(m['link_label'])}</a>
        <br><br><p style='color: #666; font-size: 12px;'>Trân trọng,<br>Hệ thống HOU S-RIMS</p>
    </div>"""


def _deliver(messages, inapp):
    if inapp:
        for m in messages:
            db.session.add(Notification(user_id=m['user'].id, content=_inapp_html(m)))
        db.session.commit()
    try:
        from email_utils import send_email_async
    except Exception:
        log.exception('Không import được email_utils.send_email_async - bỏ qua gửi mail')
        return
    for m in messages:
        if not m['user'].email:
            continue
        try:
            send_email_async(m['user'].email, m['subject'], m['subject'], _email_html(m))
        except Exception:
            log.exception('Gửi mail tới %s thất bại', m['user'].email)


# ---------- handlers: mỗi handler trả list[_msg] ----------
def _on_mentor_reassigned(topic_id, old_mentor_id, new_mentor_id, reason='', released_slots=0):
    topic = db.session.get(Topic, topic_id)
    new_m = db.session.get(User, new_mentor_id)
    old_m = db.session.get(User, old_mentor_id) if old_mentor_id else None
    title = topic.title
    msgs = []

    extra = []
    if reason:
        extra.append(f'Lý do: <em>{_esc(reason)}</em>')

    old_name = old_m.full_name if old_m else "Chưa phân công"
    new_name = new_m.full_name if new_m else "Giảng viên mới"

    if new_m:
        msgs.append(_msg(new_m, '[HOU S-RIMS] Phân công hướng dẫn đề tài mới',
                         'Khoa phân công bạn hướng dẫn đề tài', '#4f46e5',
                         [f'Khoa vừa phân công bạn làm Giảng viên hướng dẫn đề tài NCKH {_b(title)} (điều chuyển từ Thầy/Cô {_b(old_name)}).',
                          'Đề tài đã được duyệt chính thức và nhóm chat nghiên cứu đã được kích hoạt.'] + _group_line(topic.group_id) + extra,
                         '/lecturer/progress', 'Xem tiến độ & Nhóm'))
    if old_m and old_m.id != new_mentor_id:
        text = [f'Đề tài NCKH {_b(title)} đã được Khoa điều chuyển từ bạn sang Thầy/Cô {_b(new_name)} hướng dẫn.']
        if released_slots:
            text.append(f'{released_slots} lịch báo cáo tiến độ nhóm đã đặt với bạn cho đề tài này đã được hủy.')
        msgs.append(_msg(old_m, '[HOU S-RIMS] Đề tài đã được điều chuyển sang giảng viên khác',
                         'Đề tài được chuyển cho giảng viên khác', '#f59e0b',
                         text + _group_line(topic.group_id) + extra,
                         '/lecturer/progress'))
    for s in _group_students(topic.group_id):
        text = [f'Khoa đã điều chuyển Giảng viên hướng dẫn đề tài {_b(title)} của nhóm bạn từ Thầy/Cô {_b(old_name)} sang Thầy/Cô {_b(new_name)}.',
                'Đề tài đã sẵn sàng, bạn có thể trao đổi với Thầy/Cô mới qua mục Chatgroups và theo dõi tiến độ.']
        if released_slots:
            text.append(f'{released_slots} lịch báo cáo tiến độ đã đặt trước đó với GV cũ bị hủy, vui lòng đặt lại lịch mới nếu cần.')
        msgs.append(_msg(s, '[HOU S-RIMS] Thông báo điều chuyển Giảng viên hướng dẫn', 'Điều chuyển Giảng viên hướng dẫn',
                         '#4f46e5', text, '/student#s-chat', 'Vào Chatgroup'))
    return msgs


def _on_topic_mentor_accepted(topic_id):
    topic = db.session.get(Topic, topic_id)
    mentor = db.session.get(User, topic.mentor_id) if topic.mentor_id else None
    msgs = []
    for s in _group_students(topic.group_id):
        who = mentor_display_name(mentor, s)
        who_text = 'Giảng viên hướng dẫn' if who == HIDDEN_MENTOR_LABEL else f'Giảng viên {_b(who)}'
        msgs.append(_msg(s, '[HOU S-RIMS] Giảng viên đồng ý hướng dẫn', 'Giảng viên đã đồng ý hướng dẫn', '#3b82f6',
                         [f'{who_text} vừa đồng ý hướng dẫn đề tài NCKH {_b(topic.title)} của nhóm bạn.',
                          'Đề tài đang chờ Khoa/Viện phê duyệt chính thức.']))
    return msgs


def _on_topic_faculty_decision(topic_id, approved, reason=''):
    topic = db.session.get(Topic, topic_id)
    mentor = db.session.get(User, topic.mentor_id) if topic.mentor_id else None
    word = 'được Khoa chính thức phê duyệt' if approved else 'bị Khoa từ chối'
    color = '#10b981' if approved else '#ef4444'
    heading = 'Đề tài NCKH đã được phê duyệt' if approved else 'Đề tài NCKH bị từ chối'
    extra = [f'Lý do: <em>{_esc(reason)}</em>'] if (reason and not approved) else []
    msgs = []
    if mentor:
        msgs.append(_msg(mentor, f'[HOU S-RIMS] {heading}', heading, color,
                         [f'Đề tài NCKH {_b(topic.title)} do bạn hướng dẫn đã {word}.']
                         + _group_line(topic.group_id) + extra))
    for s in _group_students(topic.group_id):
        msgs.append(_msg(s, f'[HOU S-RIMS] {heading}', heading, color,
                         [f'Đề tài NCKH {_b(topic.title)} của nhóm bạn đã {word}.'] + extra))
    return msgs


def _on_slot_booked(lecturer_id, group_id, start_time, end_time, location=None):
    mentor = db.session.get(User, lecturer_id)
    when = _fmt_range(start_time, end_time)
    where = [f'Địa điểm: {_b(location)}.'] if location else []
    msgs = []
    if mentor:
        msgs.append(_msg(mentor, '[HOU S-RIMS] Nhóm đã đặt lịch báo cáo tiến độ', 'Có nhóm đặt lịch báo cáo', '#4f46e5',
                         [f'Nhóm sinh viên đã đăng ký báo cáo tiến độ {_b(when)}.'] + _group_line(group_id) + where,
                         '/lecturer/calendar'))
    for s in _group_students(group_id):
        who = mentor_display_name(mentor, s)
        with_who = '' if who == HIDDEN_MENTOR_LABEL else f' với giảng viên {_b(who)}'
        msgs.append(_msg(s, '[HOU S-RIMS] Xác nhận lịch báo cáo tiến độ', 'Đặt lịch báo cáo thành công', '#10b981',
                         [f'Nhóm bạn đã đặt lịch báo cáo tiến độ{with_who} lúc {_b(when)}.'] + where,
                         '/student/book-slot', 'Xem lịch'))
    return msgs


def _on_slot_cancelled(lecturer_id, group_id, start_time, end_time, by='group'):
    mentor = db.session.get(User, lecturer_id)
    when = _fmt_range(start_time, end_time)
    msgs = []
    if by == 'lecturer':
        for s in _group_students(group_id):
            who = mentor_display_name(mentor, s)
            by_text = 'Giảng viên' if who == HIDDEN_MENTOR_LABEL else f'Giảng viên {_b(who)}'
            msgs.append(_msg(s, '[HOU S-RIMS] Lịch báo cáo tiến độ bị hủy', 'Lịch báo cáo bị hủy', '#ef4444',
                             [f'{by_text} đã hủy lịch báo cáo tiến độ {_b(when)} của nhóm bạn.',
                              'Vui lòng đăng ký khung giờ khác.'], '/student/book-slot', 'Đặt lịch lại'))
    elif mentor:
        msgs.append(_msg(mentor, '[HOU S-RIMS] Nhóm đã hủy lịch báo cáo', 'Nhóm hủy lịch báo cáo', '#f59e0b',
                         [f'Nhóm sinh viên đã hủy lịch báo cáo tiến độ {_b(when)}. Khung giờ đã được mở lại.']
                         + _group_line(group_id), '/lecturer/slots'))
    return msgs


HANDLERS = {
    'mentor_reassigned': _on_mentor_reassigned,
    'topic_mentor_accepted': _on_topic_mentor_accepted,
    'topic_faculty_decision': _on_topic_faculty_decision,
    'slot_booked': _on_slot_booked,
    'slot_cancelled': _on_slot_cancelled,
}


def emit(event, *, inapp=True, **ctx):
    """
    Phát sự kiện. inapp=False nếu route đã tự tạo Notification (vd slots.py) để không trùng.
    Không bao giờ raise.
    """
    try:
        handler = HANDLERS.get(event)
        if handler is None:
            log.warning('Sự kiện chưa có handler: %s', event)
            return
        _deliver(handler(**ctx), inapp)
    except Exception:
        db.session.rollback()
        log.exception('emit(%s) thất bại', event)
