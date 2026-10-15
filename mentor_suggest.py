"""
Task 12 - Thống kê & Gợi ý Mentor thông minh.

Đặt cạnh app.py (cùng cấp với email_utils.py).

"Cùng chuyên môn" được hiểu từ dữ liệu hiện có, KHÔNG cần thêm bảng/cột:
  - Bộ môn          : User.faculty  (Công nghệ phần mềm / Khoa học máy tính / ...)
  - Hướng nghiên cứu: User.bio      (nhập ở màn Khoa > Giảng viên, vd "Học máy, IoT, Blockchain")

Điểm gợi ý = 3 (cùng bộ môn với GV hiện tại) + số từ khoá hướng nghiên cứu của ứng viên
trùng với từ khoá của GV hiện tại hoặc xuất hiện trong tên/mô tả đề tài.

"Số đề tài đang giữ" = số đề tài của GV trong năm học hiện tại có status khác 'rejected'.
Quota mặc định 5 (khớp ô "Quota hướng dẫn" trên giao diện), đổi bằng biến môi trường
MENTOR_MAX_TOPICS trong .env. (Quota hiện chưa được lưu xuống DB.)
"""
import os
import re
import unicodedata

from sqlalchemy import func
from models import db, User, Topic, Batch

MAX_TOPICS_PER_MENTOR = int(os.getenv('MENTOR_MAX_TOPICS', '5'))
SAME_DEPT_BONUS = 3


# ---------- phần thuần (không đụng DB, dễ test) ----------
def normalize(text):
    """Chữ thường, bỏ dấu tiếng Việt, gọn khoảng trắng."""
    s = (text or '').lower().replace('đ', 'd')
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', s).strip()


def keywords(text):
    """'Học máy, IoT; Blockchain' -> {'hoc may', 'iot', 'blockchain'}"""
    parts = re.split(r'[,;/|\n]+', text or '')
    return {k for k in (normalize(p) for p in parts) if len(k) >= 2}


def _in_text(keyword, normalized_text):
    """Khớp nguyên từ (tránh 'ai' khớp nhầm trong 'hai')."""
    return re.search(r'(?<!\w)' + re.escape(keyword) + r'(?!\w)', normalized_text) is not None


def match_info(ref_dept, ref_keywords, topic_text, cand_dept, cand_bio):
    """Trả về (score, same_dept, matched_keywords)."""
    same_dept = bool(ref_dept) and normalize(cand_dept) == ref_dept
    topic_norm = normalize(topic_text)
    matched = sorted(k for k in keywords(cand_bio)
                     if k in ref_keywords or _in_text(k, topic_norm))
    score = (SAME_DEPT_BONUS if same_dept else 0) + len(matched)
    return score, same_dept, matched


# ---------- phần có DB ----------
def _is_lecturer():
    return func.lower(User.role) == 'lecturer'


def mentor_loads(academic_year):
    """{mentor_id: {'total': n, 'approved': n, 'pending': n}} trong năm học."""
    rows = (db.session.query(Topic.mentor_id, Topic.status, func.count(Topic.id))
            .join(Batch, Batch.id == Topic.batch_id)
            .filter(Batch.academic_year == academic_year, Batch.status != 'hidden',
                    Topic.mentor_id.isnot(None), Topic.status != 'rejected')
            .group_by(Topic.mentor_id, Topic.status).all())
    loads = {}
    for mid, status, n in rows:
        d = loads.setdefault(mid, {'total': 0, 'approved': 0, 'pending': 0})
        d['total'] += n
        d['approved' if status == 'approved' else 'pending'] += n
    return loads


def _load_of(loads, mentor_id):
    return loads.get(mentor_id, {'total': 0, 'approved': 0, 'pending': 0})


def mentor_stats(academic_year):
    """Thống kê tải hướng dẫn của mọi giảng viên (cho panel 'Thống kê')."""
    loads = mentor_loads(academic_year)
    out = []
    for u in User.query.filter(_is_lecturer()).order_by(User.full_name).all():
        l = _load_of(loads, u.id)
        out.append({'id': u.id, 'full_name': u.full_name, 'faculty': u.faculty,
                    'current_topics': l['total'], 'approved': l['approved'],
                    'pending': l['pending'], 'quota': MAX_TOPICS_PER_MENTOR,
                    'available': l['total'] < MAX_TOPICS_PER_MENTOR})
    return out


def suggest_mentors(topic, academic_year, include_all=False):
    """
    Danh sách GV có thể nhận đề tài `topic` thay cho GV hiện tại.
    Mặc định chỉ trả GV cùng chuyên môn; include_all=True trả tất cả (kèm cờ same_specialty).
    Sắp xếp: còn chỗ trước -> điểm cao -> ít đề tài -> theo tên.
    """
    ref = db.session.get(User, topic.mentor_id) if topic.mentor_id else None
    ref_dept = normalize(ref.faculty) if ref and ref.faculty else ''
    ref_kw = keywords(ref.bio) if ref else set()
    topic_text = f'{topic.title or ""} {topic.description or ""}'
    loads = mentor_loads(academic_year)

    result = []
    for u in User.query.filter(_is_lecturer()).all():
        if ref and u.id == ref.id:
            continue
        score, same_dept, matched = match_info(ref_dept, ref_kw, topic_text, u.faculty, u.bio)
        same_specialty = same_dept or bool(matched)
        if not same_specialty and not include_all:
            continue
        l = _load_of(loads, u.id)
        result.append({
            'id': u.id, 'full_name': u.full_name, 'email': u.email, 'faculty': u.faculty,
            'bio': u.bio, 'same_department': same_dept, 'matched_keywords': matched,
            'same_specialty': same_specialty, 'score': score,
            'current_topics': l['total'], 'approved': l['approved'], 'pending': l['pending'],
            'quota': MAX_TOPICS_PER_MENTOR, 'available': l['total'] < MAX_TOPICS_PER_MENTOR,
        })
    result.sort(key=lambda m: (not m['available'], -m['score'], m['current_topics'], m['full_name'] or ''))
    return result
