# routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import User

auth_bp = Blueprint('auth', __name__)

from werkzeug.security import check_password_hash
from sqlalchemy import func, or_

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        raw_username = (request.form.get('username') or '').strip()
        password = request.form.get('password', '').strip()

        # Ánh xạ bí danh (alias) đăng nhập tiện lợi
        alias_map = {
            'sv': 'student1',
            'sv01': 'student1',
            'student': 'student1',
            'gv': 'lecturer1',
            'gv1': 'lecturer1',
            'gv01': 'lecturer1',
            'lecturer': 'lecturer1',
            'lecture': 'lecturer1',
            'lecture1': 'lecturer1',
            'lecturer1': 'lecturer1',
            'lecturer2': 'lecturer2',
            'lecturer3': 'lecturer3',
            'lecturer4': 'lecturer4',
            'lecturer5': 'lecturer5',
            'lecturer6': 'lecturer6',
            'lecturer7': 'lecturer7',
            'khoa': 'faculty1',
            'faculty': 'faculty1',
            'admin': 'admin'
        }
        lookup_username = alias_map.get(raw_username.lower(), raw_username)

        user = User.query.filter(
            or_(
                func.lower(User.username) == lookup_username.lower(),
                func.lower(User.username) == raw_username.lower(),
                func.lower(User.student_id) == raw_username.lower()
            )
        ).first()

        valid_pw = False
        if user:
            # Cho phép mật khẩu demo 123456 / 123 hoặc so khớp hash / chuỗi
            if password in ['123', '123456'] or not user.password_hash or password == user.password_hash:
                valid_pw = True
            else:
                try:
                    if check_password_hash(user.password_hash, password):
                        valid_pw = True
                except Exception:
                    pass

        if user and valid_pw:
            # Store user info in session
            session['user_id'] = user.id
            session['role'] = user.role.lower()
            session['user_name'] = user.full_name

            role = user.role.lower()
            if role == 'admin':
                return redirect(url_for('web.admin_page'))
            if role == 'faculty':
                return redirect(url_for('faculty.dashboard'))
            if role == 'student':
                return redirect(url_for('web.student_page'))
            if role == 'lecturer':
                return redirect(url_for('lecturer.dashboard'))
            return redirect(url_for('web.admin_page'))
        else:
            flash('Sai tên đăng nhập hoặc mật khẩu! Mẹo: Bạn có thể nhập student1 / lecturer1 / faculty1 / admin (mật khẩu: 123456).')

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

# --- API Endpoints ---
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
    
    if user and (user.password_hash == password or not user.password_hash or password in ['123', '123456']):
        access_token = create_access_token(identity=user.username, additional_claims={"role": user.role, "name": user.full_name})
        return jsonify(access_token=access_token, user=user.to_dict()), 200

    return jsonify({"msg": "Sai tên đăng nhập hoặc mật khẩu"}), 401

@auth_bp.route('/api/auth/logout', methods=['POST'])
@jwt_required()
def api_logout():
    current_user = get_jwt_identity()
    return jsonify({"msg": f"User {current_user} đã đăng xuất thành công"}), 200
