import sys, os
sys.path.insert(0, os.path.abspath('.'))
from app import app, db
from models import Topic, Group, GroupMember, TopicRegistration, User

with app.app_context():
    print("=== TOPICS ===")
    topics = Topic.query.all()
    for t in topics:
        print(f"ID={t.id}, title='{t.title}', status='{t.status}', group_id={t.group_id}, mentor_id={t.mentor_id}, batch_id={t.batch_id}")
        
    print("\n=== GROUPS ===")
    groups = Group.query.all()
    for g in groups:
        members = GroupMember.query.filter_by(group_id=g.id).all()
        m_info = [(m.student_id, m.status) for m in members]
        print(f"ID={g.id}, name='{g.name}', status='{g.status}', mentor_id={g.mentor_id}, leader_id={getattr(g, 'leader_id', None)}, members={m_info}")

    print("\n=== USERS (Students) ===")
    students = User.query.filter_by(role='student').all()
    for s in students:
        print(f"ID={s.id}, name='{s.full_name}', username='{s.username}', student_id='{s.student_id}'")
