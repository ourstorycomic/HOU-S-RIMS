"""
Task 1 (Le Van Dat) - Tien ich Giang vien: Quan ly lich hen noi bo.

Giang vien tao cac "slot" thoi gian ranh, he thong tu chia thanh cac khung gio
(mac dinh 30 phut / nhom). Sinh vien (nhom do GV huong dan) vao dang ky 1 slot
de bao cao tien do.

Endpoints:
  GV : POST   /api/slots                 tao slot (chia khung gio tu dong)
       GET    /api/slots/mine            danh sach slot cua toi
       DELETE /api/slots/<id>            xoa slot (neu da co nhom dat -> huy + thong bao)
  SV : GET    /api/slots/mentors         GV huong dan cua toi
       GET    /api/slots/available       slot con trong (?lecturer_id=)
       POST   /api/slots/<id>/book       dang ky slot
       GET    /api/slots/my-bookings     lich da dat cua toi
  Chung: POST /api/slots/<id>/cancel     huy lich da dat (SV dat hoac GV)
"""
from datetime import datetime, timedelta, date as date_cls
from zoneinfo import ZoneInfo

from flask import Blueprint, request, jsonify, session
from models import (db, User, Group, GroupMember, Topic, Meeting,
                    Notification, AvailabilitySlot)

slots_bp = Blueprint('slots_api', __name__, url_prefix='/api/slots')

# ---- Cau hinh ---------------------------------------------------------------
LOCAL_TZ = ZoneInfo('Asia/Ho_Chi_Minh')
DEFAULT_SLOT_MINUTES = 30
MIN_SLOT_MINUTES, MAX_SLOT_MINUTES = 10, 120
MAX_SLOTS_PER_REQUEST = 200
MAX_ACTIVE_BOOKINGS_PER_GROUP = 1      # 1 nhom chi giu 1 lich sap toi / GV
ACCEPTED_MEMBER_STATUSES = ('accepted', 'joined')


def now_local():
    """Gio hien tai (naive) theo mui gio VN - cung kieu voi Meeting.start_time."""
    return datetime.now(LOCAL_TZ).replace(tzinfo=None)


# ---- Helpers ----------------------------------------------------------------
def _role():
    return (session.get('role') or '').lower()


def _err(msg, code):
    return jsonify({'error': msg}), code


def _require(role):
    """Tra ve (user_id, None) neu hop le, nguoc lai (None, response)."""
    uid = session.get('user_id')
    if not uid:
        return None, _err('Unauthorized', 401)
    if _role() != role:
        return None, _err('Permission denied', 403)
    return uid, None


def _parse_time(value):
    return datetime.strptime(value, '%H:%M').time()


def _notify(user_id, content, email_subject=None):
    """Tao thong bao trong he thong (+ gui email neu co email_subject).

    Email gui nen (thread rieng) va khong bao gio lam hong request neu loi.
    Quy uoc noi dung: thong bao gui cho SV KHONG chua ten GV; gui cho GV hien day du ten SV.
    """
    db.session.add(Notification(user_id=user_id, content=content))
    if email_subject:
        user = User.query.get(user_id)
        if user and user.email:
            try:
                from email_utils import send_email_async
                send_email_async(user.email, f'[HOU S-RIMS] {email_subject}',
                                 f'Xin chào {user.full_name},\n\n{content}\n\nTrân trọng,\nHOU S-RIMS')
            except Exception as e:                      # khong de loi email lam fail dat lich
                print(f'Email error (slots): {e}')


def _fmt(slot):
    return f"{slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')} ngày {slot.start_time.strftime('%d/%m/%Y')}"


def _student_groups(student_id):
    """Cac nhom ma sinh vien la truong nhom hoac thanh vien da chap nhan trong dot active."""
    from models import Batch
    active_batch = Batch.query.filter_by(status='active').order_by(Batch.id.desc()).first()
    
    member_q = GroupMember.query.filter(
        GroupMember.student_id == student_id,
        GroupMember.status.in_(ACCEPTED_MEMBER_STATUSES))
    if active_batch:
        member_q = member_q.join(Group).filter(Group.batch_id == active_batch.id)
    member_ids = [m.group_id for m in member_q.all()]
    
    cond = Group.leader_id == student_id
    if member_ids:
        cond = cond | Group.id.in_(member_ids)
    q = Group.query.filter(cond)
    if active_batch:
        q = q.filter(Group.batch_id == active_batch.id)
    return q.all()


def _group_mentor_ids(group):
    ids = set()
    if group.mentor_id:
        ids.add(group.mentor_id)
    for t in Topic.query.filter_by(group_id=group.id).all():
        if t.mentor_id:
            ids.add(t.mentor_id)
    return ids


def _student_mentor_map(student_id):
    """{lecturer_id: [group, ...]} - GV huong dan cua cac nhom cua sinh vien."""
    result = {}
    for g in _student_groups(student_id):
        for mid in _group_mentor_ids(g):
            result.setdefault(mid, []).append(g)
    return result


def _remove_meeting(slot):
    if slot.meeting_id:
        m = Meeting.query.get(slot.meeting_id)
        if m:
            db.session.delete(m)
    slot.meeting_id = None


def _release(slot):
    """Dua slot ve trang thai trong."""
    _remove_meeting(slot)
    slot.status = 'open'
    slot.group_id = None
    slot.booked_by_id = None
    slot.booked_at = None


# ---- Giang vien -------------------------------------------------------------
@slots_bp.route('', methods=['POST'])
def create_slots():
    """
    GV tao slot ranh, tu dong chia khung gio
    ---
    tags: [Slots]
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            dates: {type: array, items: {type: string}, example: ["2026-10-20"]}
            start_time: {type: string, example: "08:00"}
            end_time: {type: string, example: "11:30"}
            slot_minutes: {type: integer, example: 30}
            location: {type: string}
            note: {type: string}
    responses:
      201: {description: Created}
    """
    uid, err = _require('lecturer')
    if err:
        return err
    data = request.get_json(silent=True) or {}

    dates = data.get('dates') or ([data['date']] if data.get('date') else [])
    if not dates or not data.get('start_time') or not data.get('end_time'):
        return _err('Thiếu dữ liệu (dates, start_time, end_time)', 400)
    try:
        t_start, t_end = _parse_time(data['start_time']), _parse_time(data['end_time'])
        day_list = sorted({datetime.strptime(d, '%Y-%m-%d').date() for d in dates})
        minutes = int(data.get('slot_minutes') or DEFAULT_SLOT_MINUTES)
    except (ValueError, TypeError):
        return _err('Định dạng ngày/giờ không hợp lệ (YYYY-MM-DD, HH:MM)', 400)

    if not (MIN_SLOT_MINUTES <= minutes <= MAX_SLOT_MINUTES):
        return _err(f'Độ dài mỗi khung phải từ {MIN_SLOT_MINUTES} đến {MAX_SLOT_MINUTES} phút', 400)
    if t_end <= t_start:
        return _err('Giờ kết thúc phải sau giờ bắt đầu', 400)

    step = timedelta(minutes=minutes)
    now = now_local()
    candidates = []
    for d in day_list:
        cur = datetime.combine(d, t_start)
        limit = datetime.combine(d, t_end)
        while cur + step <= limit:          # phan du < 1 khung bi bo
            candidates.append((cur, cur + step))
            cur += step
    if len(candidates) > MAX_SLOTS_PER_REQUEST:
        return _err(f'Tối đa {MAX_SLOTS_PER_REQUEST} khung giờ mỗi lần tạo', 400)

    skipped_past = skipped_overlap = 0
    created = []
    if candidates:
        lo, hi = candidates[0][0], candidates[-1][1]
        existing = AvailabilitySlot.query.filter(
            AvailabilitySlot.lecturer_id == uid,
            AvailabilitySlot.start_time < hi,
            AvailabilitySlot.end_time > lo).all()
        taken = [(s.start_time, s.end_time) for s in existing]
        for s, e in candidates:
            if s <= now:
                skipped_past += 1
                continue
            if any(s < te and e > ts for ts, te in taken):
                skipped_overlap += 1
                continue
            slot = AvailabilitySlot(lecturer_id=uid, start_time=s, end_time=e,
                                    location=(data.get('location') or '').strip() or None,
                                    note=(data.get('note') or '').strip() or None)
            db.session.add(slot)
            created.append(slot)
            taken.append((s, e))
    db.session.commit()

    return jsonify({
        'message': f'Đã tạo {len(created)} khung giờ',
        'created': len(created),
        'skipped_past': skipped_past,
        'skipped_overlap': skipped_overlap,
        'slots': [s.to_dict() for s in created],
    }), 201


@slots_bp.route('/mine', methods=['GET'])
def my_slots():
    """GV xem cac slot cua minh (?from=YYYY-MM-DD&include_past=1)"""
    uid, err = _require('lecturer')
    if err:
        return err
    q = AvailabilitySlot.query.filter_by(lecturer_id=uid)
    if request.args.get('include_past') != '1':
        q = q.filter(AvailabilitySlot.end_time >= now_local())
    slots = q.order_by(AvailabilitySlot.start_time).all()
    return jsonify([s.to_dict() for s in slots]), 200


@slots_bp.route('/<int:slot_id>', methods=['DELETE'])
def delete_slot(slot_id):
    """GV xoa slot; neu da co nhom dat thi huy lich va thong bao cho nhom"""
    uid, err = _require('lecturer')
    if err:
        return err
    slot = AvailabilitySlot.query.get(slot_id)
    if not slot:
        return _err('Không tìm thấy khung giờ', 404)
    if slot.lecturer_id != uid:
        return _err('Permission denied', 403)

    if slot.status == 'booked' and slot.booked_by_id:
        _notify(slot.booked_by_id,
                f"Giảng viên đã hủy khung giờ báo cáo tiến độ {_fmt(slot)}. Vui lòng đăng ký khung giờ khác.",
                'Khung giờ báo cáo tiến độ đã bị hủy')
    _remove_meeting(slot)
    db.session.delete(slot)
    db.session.commit()
    return jsonify({'message': 'Đã xóa khung giờ'}), 200


# ---- Sinh vien --------------------------------------------------------------
@slots_bp.route('/mentors', methods=['GET'])
def my_mentors():
    """SV: danh sach GV huong dan cua cac nhom cua toi"""
    uid, err = _require('student')
    if err:
        return err
    mm = _student_mentor_map(uid)
    users = User.query.filter(User.id.in_(list(mm.keys()))).all() if mm else []
    return jsonify([{'id': u.id, 'name': u.full_name, 'faculty': u.faculty,
                     'groups': [g.name for g in mm[u.id]]} for u in users]), 200


@slots_bp.route('/available', methods=['GET'])
def available_slots():
    """SV: cac slot con trong cua GV huong dan (?lecturer_id=)"""
    uid, err = _require('student')
    if err:
        return err
    mm = _student_mentor_map(uid)
    lecturer_id = request.args.get('lecturer_id', type=int)
    allowed = [lecturer_id] if lecturer_id else list(mm.keys())
    if lecturer_id and lecturer_id not in mm:
        return _err('Bạn chỉ xem được lịch của giảng viên hướng dẫn nhóm mình', 403)
    if not allowed:
        return jsonify([]), 200
    slots = AvailabilitySlot.query.filter(
        AvailabilitySlot.lecturer_id.in_(allowed),
        AvailabilitySlot.status == 'open',
        AvailabilitySlot.start_time > now_local()
    ).order_by(AvailabilitySlot.start_time).all()
    return jsonify([s.to_dict() for s in slots]), 200


@slots_bp.route('/<int:slot_id>/book', methods=['POST'])
def book_slot(slot_id):
    """
    SV dang ky 1 slot de bao cao tien do
    ---
    tags: [Slots]
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            group_id: {type: integer, description: "Bo trong neu SV chi co 1 nhom do GV nay huong dan"}
    """
    uid, err = _require('student')
    if err:
        return err
    slot = AvailabilitySlot.query.get(slot_id)
    if not slot:
        return _err('Không tìm thấy khung giờ', 404)
    if slot.start_time <= now_local():
        return _err('Khung giờ này đã qua', 400)

    groups = _student_mentor_map(uid).get(slot.lecturer_id)
    if not groups:
        return _err('Bạn chỉ được đăng ký lịch của giảng viên hướng dẫn nhóm mình', 403)
    data = request.get_json(silent=True) or {}
    gid = data.get('group_id')
    if gid:
        group = next((g for g in groups if g.id == int(gid)), None)
        if not group:
            return _err('Nhóm không hợp lệ', 400)
    elif len(groups) == 1:
        group = groups[0]
    else:
        return jsonify({'error': 'Bạn thuộc nhiều nhóm, hãy chọn nhóm',
                        'groups': [{'id': g.id, 'name': g.name} for g in groups]}), 400

    # Gioi han so lich sap toi cua 1 nhom voi 1 GV
    active = AvailabilitySlot.query.filter(
        AvailabilitySlot.group_id == group.id,
        AvailabilitySlot.lecturer_id == slot.lecturer_id,
        AvailabilitySlot.status == 'booked',
        AvailabilitySlot.end_time > now_local()).count()
    if active >= MAX_ACTIVE_BOOKINGS_PER_GROUP:
        return _err('Nhóm đã có lịch báo cáo sắp tới với giảng viên này. Hãy hủy lịch cũ trước khi đặt lịch mới.', 409)

    # Dat atomically: chi 1 nguoi thang neu nhieu SV bam cung luc
    updated = AvailabilitySlot.query.filter_by(id=slot_id, status='open').update(
        {'status': 'booked', 'group_id': group.id, 'booked_by_id': uid,
         'booked_at': datetime.utcnow()}, synchronize_session=False)
    if updated != 1:
        db.session.rollback()
        return _err('Khung giờ vừa có nhóm khác đăng ký. Vui lòng chọn khung giờ khác.', 409)

    db.session.expire_all()
    slot = AvailabilitySlot.query.get(slot_id)
    topic = Topic.query.filter_by(group_id=group.id, mentor_id=slot.lecturer_id).first()
    meeting = Meeting(title=f'Báo cáo tiến độ - {group.name}',
                      description=slot.location and f'Địa điểm: {slot.location}' or '',
                      start_time=slot.start_time, end_time=slot.end_time,
                      organizer_id=uid, topic_id=topic.id if topic else None,
                      status='approved')
    db.session.add(meeting)
    db.session.flush()
    slot.meeting_id = meeting.id

    student = User.query.get(uid)
    _notify(slot.lecturer_id,
            f"Nhóm '{group.name}' ({student.full_name if student else ''}) đã đăng ký báo cáo tiến độ {_fmt(slot)}"
            + (f" tại {slot.location}." if slot.location else "."),
            'Nhóm sinh viên đăng ký báo cáo tiến độ')
    db.session.commit()
    return jsonify({'message': 'Đăng ký thành công', 'slot': slot.to_dict()}), 200


@slots_bp.route('/my-bookings', methods=['GET'])
def my_bookings():
    """SV: cac lich bao cao da dat cua cac nhom toi"""
    uid, err = _require('student')
    if err:
        return err
    gids = [g.id for g in _student_groups(uid)]
    if not gids:
        return jsonify([]), 200
    slots = AvailabilitySlot.query.filter(
        AvailabilitySlot.group_id.in_(gids), AvailabilitySlot.status == 'booked'
    ).order_by(AvailabilitySlot.start_time).all()
    return jsonify([s.to_dict() for s in slots]), 200


# ---- Huy lich da dat --------------------------------------------------------
@slots_bp.route('/<int:slot_id>/cancel', methods=['POST'])
def cancel_booking(slot_id):
    """SV trong nhom hoac GV huy lich da dat; slot tro lai trang thai trong"""
    uid = session.get('user_id')
    if not uid:
        return _err('Unauthorized', 401)
    slot = AvailabilitySlot.query.get(slot_id)
    if not slot:
        return _err('Không tìm thấy khung giờ', 404)
    if slot.status != 'booked':
        return _err('Khung giờ chưa có ai đăng ký', 400)

    role = _role()
    if role == 'lecturer' and slot.lecturer_id == uid:
        by_lecturer = True
    elif role == 'student' and slot.group_id in [g.id for g in _student_groups(uid)]:
        by_lecturer = False
    else:
        return _err('Permission denied', 403)

    booker, group_name = slot.booked_by_id, slot.group.name if slot.group else ''
    actor = User.query.get(uid)
    text = _fmt(slot)
    _release(slot)
    if by_lecturer:
        if booker:
            _notify(booker, f"Giảng viên đã hủy lịch báo cáo tiến độ {text} của nhóm '{group_name}'. Vui lòng đăng ký khung giờ khác.",
                    'Lịch báo cáo tiến độ đã bị hủy')
    else:
        _notify(slot.lecturer_id,
                f"Sinh viên {actor.full_name} (nhóm '{group_name}') đã hủy lịch báo cáo tiến độ {text}. Khung giờ đã được mở lại.",
                'Nhóm sinh viên hủy lịch báo cáo tiến độ')
    db.session.commit()
    return jsonify({'message': 'Đã hủy lịch', 'slot': slot.to_dict()}), 200
