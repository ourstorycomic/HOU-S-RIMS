from flask import Blueprint, render_template, session, redirect, url_for, request

web_bp = Blueprint('web', __name__)

# Middleware kiểm tra đăng nhập cho tất cả các route trong web_bp
@web_bp.before_request
def check_login():
    # Nếu chưa đăng nhập và không phải đang ở trang login/static -> Đẩy về login
    if 'user_id' not in session and request.endpoint != 'auth.login':
        return redirect(url_for('auth.login'))

@web_bp.route('/')
def home():
    # Điều hướng thông minh dựa vào quyền
    role = session.get('role')
    if role == 'admin': return redirect(url_for('web.admin_page'))
    if role == 'student': return redirect(url_for('web.student_page'))
    if role == 'lecturer': return redirect(url_for('web.lecturer_page'))
    return redirect(url_for('web.admin_page')) # Mặc định

@web_bp.route('/admin')
def admin_page():
    if session.get('role') != 'admin': return "Không có quyền truy cập", 403
    return render_template('admin.html')

@web_bp.route('/faculty')
def faculty_page():
    # Admin cũng xem được trang khoa
    if session.get('role') not in ['admin', 'faculty']: return "Không có quyền truy cập", 403
    return render_template('faculty.html')

@web_bp.route('/lecturer')
def lecturer_page():
    if session.get('role') != 'lecturer': return "Không có quyền truy cập", 403
    return render_template('lecturer.html')

@web_bp.route('/student')
def student_page():
    if session.get('role') != 'student': return "Không có quyền truy cập", 403
    return render_template('student.html')

# Công cụ hỗ trợ - AI CŨNG CẦN LOGIN MỚI DÙNG ĐƯỢC
@web_bp.route('/repository')
def repository_page():
    return render_template('repository.html')

@web_bp.route('/analysis')
def analysis_page():
    return render_template('analysis.html')