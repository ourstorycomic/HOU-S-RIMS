from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    role = db.Column(db.String(20), nullable=False) # Admin, Lecturer, Student
    student_id = db.Column(db.String(20), nullable=True)   # MSSV for students
    faculty = db.Column(db.String(100), nullable=True)      # faculty / department
    
    # Relationships
    topics_mentored = db.relationship('Topic', backref='mentor', lazy=True)
    group_memberships = db.relationship('GroupMember', backref='student', lazy=True)

    @property
    def password(self):
        return self.password_hash

    @password.setter
    def password(self, val):
        self.password_hash = val

    @property
    def name(self):
        return self.full_name

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'name': self.full_name,
            'full_name': self.full_name,
            'email': self.email,
            'bio': self.bio,
            'phone': self.phone,
            'student_id': self.student_id,
            'faculty': self.faculty
        }

class Batch(db.Model):
    __tablename__ = 'batches'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=True, default='NCKH')
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    submission_deadline = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='active') # active, completed
    academic_year = db.Column(db.String(20), default='2025-2026')
    guidance_doc = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    topics = db.relationship('Topic', backref='batch', lazy=True)
    groups = db.relationship('Group', backref='batch', lazy=True)

class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True, default='Nhóm NCKH')
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=True)
    leader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(30), default='draft') # 'draft', 'pending_mentor', 'approved', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    leader = db.relationship('User', foreign_keys=[leader_id], backref='led_groups', lazy=True)
    mentor = db.relationship('User', foreign_keys=[mentor_id], backref='mentored_groups', lazy=True)
    members = db.relationship('GroupMember', backref='group', cascade='all, delete-orphan', lazy=True)
    topics = db.relationship('Topic', backref='group', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'batch_id': self.batch_id,
            'leader_id': self.leader_id,
            'leader_name': self.leader.full_name if self.leader else None,
            'leader_student_id': self.leader.student_id if self.leader else (self.leader.username if self.leader else None),
            'mentor_id': self.mentor_id,
            'mentor_name': self.mentor.full_name if self.mentor else None,
            'mentor_faculty': self.mentor.faculty if self.mentor else None,
            'status': self.status,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else None,
            'members': [m.to_dict() for m in self.members] if self.members else []
        }

class GroupMember(db.Model):
    __tablename__ = 'group_members'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='invited') # 'invited', 'joined', 'declined', 'accepted', 'pending'

    def to_dict(self):
        return {
            'id': self.id,
            'group_id': self.group_id,
            'user_id': self.student_id,
            'student_id': self.student.student_id if self.student and self.student.student_id else (self.student.username if self.student else str(self.student_id)),
            'full_name': self.student.full_name if self.student else '',
            'email': self.student.email if self.student else '',
            'faculty': self.student.faculty if self.student else '',
            'status': self.status
        }

class Topic(db.Model):
    __tablename__ = 'topics'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)   # renamed from 'name'
    description = db.Column(db.Text, nullable=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=True)
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True)
    council_id = db.Column(db.Integer, db.ForeignKey('councils.id'), nullable=True)
    presentation_time = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(20), default='pending') # pending, faculty_pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    meetings = db.relationship('Meeting', backref='topic', lazy=True)
    milestones = db.relationship('Milestone', backref='topic', lazy=True)

class TopicRegistration(db.Model):
    __tablename__ = 'topic_registrations'
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# For Bui Minh Thuan (Tasks 8-13)
class Meeting(db.Model):
    __tablename__ = 'meetings'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S') if self.start_time else None,
            'end_time': self.end_time.strftime('%Y-%m-%d %H:%M:%S') if self.end_time else None,
            'organizer_id': self.organizer_id,
            'topic_id': self.topic_id,
            'status': self.status
        }

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='text') # text, image, file, emoji, invitation
    file_url = db.Column(db.String(255), nullable=True)
    file_name = db.Column(db.String(255), nullable=True)
    meta_data = db.Column(db.String(500), nullable=True)  # JSON string for extra data (group_id for invitations)
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id])

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.sender_id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'group_id': self.group_id,
            'text': self.content,
            'content': self.content,
            'message_type': self.message_type,
            'file_url': self.file_url,
            'file_name': self.file_name,
            'is_read': self.is_read,
            'created_at': self.timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.timestamp else None
        }

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# For Le Van Dat (Tasks 14-20)
class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestones.id'), nullable=True)
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_url = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    feedback = db.Column(db.Text, nullable=True)
    feedback_at = db.Column(db.DateTime, nullable=True)
    milestone = db.relationship('Milestone', backref='submissions')

    @property
    def feedback_list(self):
        import json
        if not self.feedback: return []
        try:
            data = json.loads(self.feedback)
            if isinstance(data, list):
                return data
        except:
            pass
        notes = []
        blocks = self.feedback.split('\n\n--- ')
        for block in blocks:
            if ' ---\n' in block:
                time_part, text_part = block.split(' ---\n', 1)
                notes.append({'time': time_part, 'text': text_part.strip()})
            elif block.startswith('[') and '] ' in block:
                time_part = block[1:block.find('] ')]
                text_part = block[block.find('] ')+2:]
                notes.append({'time': time_part, 'text': text_part.strip()})
            else:
                time_part = self.feedback_at.strftime('%d/%m/%Y %H:%M') if self.feedback_at else ""
                notes.append({'time': time_part, 'text': block.strip()})
        return notes

class DocumentTemplate(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    file_url = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=True)

class Council(db.Model):
    __tablename__ = 'councils'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    decision_number = db.Column(db.String(100), nullable=True)
    meeting_date = db.Column(db.Date, nullable=True)
    meeting_time = db.Column(db.Time, nullable=True)
    location = db.Column(db.String(255), nullable=True)
    decision_file_url = db.Column(db.String(255), nullable=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=False)
    established_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    topics = db.relationship('Topic', backref='council', lazy=True)
    members = db.relationship('CouncilMember', backref='council', lazy=True)

class CouncilMember(db.Model):
    __tablename__ = 'council_members'
    id = db.Column(db.Integer, primary_key=True)
    council_id = db.Column(db.Integer, db.ForeignKey('councils.id'), nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(50), default='member') # president, secretary, member
    
    mentor = db.relationship('User', foreign_keys=[mentor_id])

class Rubric(db.Model):
    __tablename__ = 'rubrics'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    criteria_json = db.Column(db.Text, nullable=False)
    total_score = db.Column(db.Float, nullable=False)

class Evaluation(db.Model):
    __tablename__ = 'evaluations'
    id = db.Column(db.Integer, primary_key=True)
    council_id = db.Column(db.Integer, db.ForeignKey('councils.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    rubric_id = db.Column(db.Integer, db.ForeignKey('rubrics.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    comments = db.Column(db.Text, nullable=True)

class Milestone(db.Model):
    __tablename__ = 'milestones'
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')

# Portfolio Models
class Skill(db.Model):
    __tablename__ = 'skills'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)

class Achievement(db.Model):
    __tablename__ = 'achievements'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    year = db.Column(db.String(20), nullable=True)
    description = db.Column(db.Text, nullable=True)

class Experience(db.Model):
    __tablename__ = 'experiences'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    project_name = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(100), nullable=True)
    duration = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)

class Progress(db.Model):
    __tablename__ = 'progresses'
    id = db.Column(db.Integer, primary_key=True)
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestones.id'), nullable=False)
    percentage = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
