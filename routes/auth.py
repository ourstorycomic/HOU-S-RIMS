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
        
        from models import User
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:
            # Lưu session
            session['user_id'] = user.username
            session['role'] = user.role
            session['user_name'] = user.name
            
            # Chuyển hướng theo role
            if user.role == 'admin': return redirect(url_for('web.admin_page'))
            if user.role == 'faculty': return redirect(url_for('web.faculty_page'))
            if user.role == 'lecturer': return redirect(url_for('web.lecturer_page'))
            if user.role == 'student': return redirect(url_for('web.student_page'))
            return redirect(url_for('web.admin_page'))
        else:
            flash('Sai tên đăng nhập hoặc mật khẩu!')
            
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

# --- API Endpoints ---
from flask import jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import User

@auth_bp.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json()
    if not data:
        return jsonify({"msg": "Missing JSON in request"}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400

    user = User.query.filter_by(username=username).first()
    
    # So sánh password plain-text (Trong thực tế nên dùng hash)
    if user and user.password == password:
        # Tạo JWT token
        access_token = create_access_token(identity=user.username, additional_claims={"role": user.role, "name": user.name})
        return jsonify(access_token=access_token, user=user.to_dict()), 200

    return jsonify({"msg": "Sai tên đăng nhập hoặc mật khẩu"}), 401

@auth_bp.route('/api/auth/logout', methods=['POST'])
@jwt_required()
def api_logout():
    # Với JWT mặc định, việc logout thực chất là xoá token ở phía Client.
    # Để an toàn hơn ở server, cần triển khai Token Blocklist (JWT Revocation),
    # tạm thời trả về báo thành công.
    current_user = get_jwt_identity()
    return jsonify({"msg": f"User {current_user} đã đăng xuất thành công"}), 200