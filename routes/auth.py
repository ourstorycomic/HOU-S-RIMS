# routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
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