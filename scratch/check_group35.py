import sys, os
sys.path.insert(0, os.path.abspath('.'))
from app import app, db
from models import Topic, Group, GroupMember, User

with app.app_context():
    print("=== TOPIC 34 ===")
    t = Topic.query.get(34)
    print("Topic 34:", t.id, t.title, t.status, "group_id:", t.group_id, "mentor_id:", t.mentor_id, "batch_id:", t.batch_id)

    g = Group.query.get(34) or Group.query.get(35)
    print("Group 35:", g.id if g else None, g.name if g else None, g.status if g else None, g.mentor_id if g else None)

    members = GroupMember.query.filter_by(group_id=35).all()
    for m in members:
        u = User.query.get(m.student_id)
        print("  Member:", m.id, "student_id:", m.student_id, "status:", m.status, "User:", u.full_name if u else None, u.username if u else None)

    m19 = User.query.get(19)
    print("Mentor 19:", m19.id if m19 else None, m19.full_name if m19 else None, m19.role if m19 else None)
