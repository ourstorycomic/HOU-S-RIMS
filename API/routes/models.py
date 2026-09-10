from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Topic(db.Model):
    __tablename__ = 'topics'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    student_name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default='Đang thực hiện')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    progresses = db.relationship('Progress', backref='topic', lazy=True, cascade="all, delete-orphan")
    submissions = db.relationship('Submission', backref='topic', lazy=True)

class Progress(db.Model):
    __tablename__ = 'progress'
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    title = db.Column(db.String(255), default='Cập nhật tiến độ')
    percentage = db.Column(db.Integer, default=0)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

class Council(db.Model):
    __tablename__ = 'councils'
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(255), nullable=False, default='Hội đồng chưa đặt tên')
    members = db.Column(db.Text, nullable=False) 

class Rubric(db.Model):
    __tablename__ = 'rubrics'
    id = db.Column(db.String(50), primary_key=True)
    criteria = db.Column(db.Text, nullable=False) 
class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.now)