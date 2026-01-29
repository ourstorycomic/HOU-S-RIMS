# routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

auth_bp = Blueprint('auth', __name__)

# Dữ liệu người dùng giả lập (Sau này thay bằng Database)
USERS = {
    "admin":   {"pass": "123", "role": "admin",    "name": "Admin Trường", "redirect": "web.admin_page"},
    "faculty": {"pass": "123", "role": "faculty",  "name": "Thư ký Khoa CNTT", "redirect": "web.faculty_page"},
    "gv":      {"pass": "123", "role": "lecturer", "name": "TS. Nguyễn Văn A", "redirect": "web.lecturer_page"},
    "sv":      {"pass": "123", "role": "student",  "name": "Nguyễn Văn Học", "redirect": "web.student_page"}
}

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = USERS.get(username)
        if user and user['pass'] == password:
            # Lưu session
            session['user_id'] = username
            session['role'] = user['role']
            session['user_name'] = user['name']
            
            return redirect(url_for(user['redirect']))
        else:
            flash('Sai tên đăng nhập hoặc mật khẩu!')
            
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))