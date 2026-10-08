from app import app
from models import db, Group, Message, Topic

with app.app_context():
    groups = Group.query.all()
    valid_group_ids = []
    
    for group in groups:
        valid_group_ids.append(group.id)
        topic = Topic.query.filter_by(group_id=group.id).first()
        if topic:
            # Any message from before this group was supposedly created is an orphaned message from a reused ID
            old_msgs = Message.query.filter(Message.group_id == group.id, Message.timestamp < topic.created_at).all()
            for m in old_msgs:
                db.session.delete(m)
                
    # Delete messages pointing to non-existent groups
    if valid_group_ids:
        orphaned = Message.query.filter(Message.group_id.isnot(None), Message.group_id.notin_(valid_group_ids)).all()
        for m in orphaned:
            db.session.delete(m)
            
    db.session.commit()
    print("Cleaned up orphaned messages successfully.")
