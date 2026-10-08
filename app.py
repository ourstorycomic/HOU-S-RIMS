
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
    from models import User, Skill, Achievement, Experience, Topic
    if not session.get('user_id'): return redirect(url_for('auth.login'))
    
    # Try to find by student_id first, then by username, then by ID as string
    user = User.query.filter((User.student_id == identifier) | (User.username == identifier) | (User.id == identifier)).first_or_404()
    
    # Get portfolio data if student
    skills = Skill.query.filter_by(student_id=user.id).all() if user.role == 'student' else []
    achievements = Achievement.query.filter_by(student_id=user.id).all() if user.role == 'student' else []
    experiences = Experience.query.filter_by(student_id=user.id).all() if user.role == 'student' else []
    
    return render_template('profile.html', profile_user=user, skills=skills, achievements=achievements, experiences=experiences)

@app.route('/<path:filename>')


def serve_static(filename): return send_from_directory('Models', filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
