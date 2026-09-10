from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='student')
    name = db.Column(db.String(100))
    bio = db.Column(db.String(500))
    phone = db.Column(db.String(20))

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'name': self.name,
            'bio': self.bio,
            'phone': self.phone
        }

class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_time = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.String(500))

    def to_dict(self):
        return {
            'id': self.id,
            'date_time': self.date_time,
            'notes': self.notes
        }

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'text': self.text,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
