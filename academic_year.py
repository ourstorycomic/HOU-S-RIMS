from datetime import datetime
from flask import session


def year_from_date(d=None):
    """Năm học bắt đầu từ tháng 9: 10/2026 -> 2026-2027, 3/2027 -> 2026-2027."""
    d = d or datetime.now()
    start = d.year if d.month >= 9 else d.year - 1
    return f'{start}-{start + 1}'


def current_academic_year():
    """Ưu tiên năm học người dùng chọn trên giao diện; không có thì lấy năm học
    của đợt đang active mới nhất; không có nữa thì tính theo ngày hiện tại."""
    chosen = session.get('academic_year')
    if chosen:
        return chosen
    from models import Batch
    b = (Batch.query.filter_by(status='active')
         .order_by(Batch.academic_year.desc(), Batch.id.desc()).first())
    if b and b.academic_year:
        return b.academic_year
    return year_from_date()

