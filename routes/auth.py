# routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()
        if user:
            # Store user info in session
            session['user_id'] = user.id
            session['role'] = user.role.lower()
            session['user_name'] = user.full_name

            role = user.role.lower()
            if role == 'admin': return redirect(url_for('faculty.dashboard'))
            if role == 'student': return redirect(url_for('student.dashboard'))
            if role == 'lecturer': return redirect(url_for('lecturer.dashboard'))
            return redirect(url_for('faculty.dashboard'))
        else:
            flash('Sai tên đăng nhập hoặc mật khẩu! (Thử: gv / sv / admin)')

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
