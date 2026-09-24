# routes/web.py
from flask import Blueprint, render_template, session, redirect, url_for, request
from models import User, Topic, Group, GroupMember, Batch, Notification

web_bp = Blueprint('web', __name__)

@web_bp.before_request
def check_login():
    if 'user_id' not in session and request.endpoint != 'auth.login':
        return redirect(url_for('auth.login'))

@web_bp.route('/')
def home():
    role = session.get('role', '').lower()
    if role == 'admin': return redirect(url_for('web.admin_page'))
    if role == 'student': return redirect(url_for('student.dashboard'))
    if role == 'lecturer': return redirect(url_for('lecturer.dashboard'))
    if role == 'faculty': return redirect(url_for('faculty.dashboard'))
    return redirect(url_for('web.admin_page'))

@web_bp.route('/admin')
def admin_page():
    return redirect(url_for('faculty.dashboard'))

@web_bp.route('/repository')
def repository_page():
    return render_template('repository.html')

@web_bp.route('/analysis')
def analysis_page():
    return render_template('analysis.html')
