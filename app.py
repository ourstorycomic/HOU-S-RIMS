
# app.py
import numpy as np
np.long = np.int64
np.ulong = np.uint64
np.longlong = np.int64
np.ulonglong = np.uint64
np.float = np.float64
np.bool = np.bool_
from flask import Flask, render_template, send_from_directory
from routes import init_routes
from dotenv import load_dotenv
import os
from models import db
from flasgger import Swagger

load_dotenv(override=True)

app = Flask(__name__)
app.secret_key = 'secret_key'
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(app.config['UPLOAD_FOLDER']): os.makedirs(app.config['UPLOAD_FOLDER'])
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 # 50MB

# Swagger setup
swagger = Swagger(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

init_routes(app)
from API.routes import init_api_routes
init_api_routes(app)

@app.route('/')
def index(): return render_template('index.html')



@app.route('/profile/<string:identifier>')
def view_profile(identifier):
    from flask import session, redirect, url_for, render_template
    from models import User, Skill, Achievement, Experience, Topic, Notification, Batch, Group, GroupMember
    from datetime import datetime
    
    user_id = session.get('user_id')
    role = session.get('role')
    if not user_id: return redirect(url_for('auth.login'))
    
    current_user = User.query.get(user_id)
    current_time = datetime.utcnow()
    current_year = session.get('academic_year', '2025-2026')
    active_batch = Batch.query.filter_by(academic_year=current_year, status='active').first()
    
    context = {
        'current_user': current_user,
        'current_time': current_time,
        'active_batch': active_batch,
    }
    
    if role == 'student':
        context['notifications'] = Notification.query.filter_by(user_id=user_id).order_by(Notification.is_read.asc(), Notification.created_at.desc()).all()
        context['global_my_groups_count'] = Group.query.join(GroupMember).join(Batch).filter(GroupMember.student_id == user_id, Batch.status == 'active').count()
        context['all_students'] = User.query.filter(User.role.ilike('student')).all()
    elif role == 'lecturer':
        context['global_pending_topics_count'] = Topic.query.filter_by(mentor_id=user_id, status='pending').count()
        context['global_my_groups_count'] = Topic.query.filter(Topic.mentor_id == user_id, Topic.status == 'approved', Topic.group_id.isnot(None)).count()
    elif role == 'faculty':
        context['global_topic_count'] = Topic.query.join(Batch).filter(Batch.academic_year == current_year, Batch.status != 'hidden').count()
        context['notifications'] = Notification.query.filter_by(user_id=user_id).order_by(Notification.is_read.asc(), Notification.created_at.desc()).all()
    
    # Try to find by student_id first, then by username, then by ID as string
    user = User.query.filter((User.student_id == identifier) | (User.username == identifier) | (User.id == identifier)).first_or_404()
    
    # Get portfolio data if student
    skills = Skill.query.filter_by(student_id=user.id).all() if user.role == 'student' else []
    achievements = Achievement.query.filter_by(student_id=user.id).all() if user.role == 'student' else []
    experiences = Experience.query.filter_by(student_id=user.id).all() if user.role == 'student' else []
    
    return render_template('profile.html', profile_user=user, skills=skills, achievements=achievements, experiences=experiences, **context)

@app.route('/<path:filename>')


def serve_static(filename): return send_from_directory('Models', filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
