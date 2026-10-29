# scratch/fix_existing_notifs.py
import sys, os
sys.path.insert(0, os.path.abspath('.'))
from app import app
from models import db, Notification

with app.app_context():
    notifs = Notification.query.all()
    count = 0
    for n in notifs:
        changed = False
        content = n.content
        
        # If it has faculty approval with "đã đánh giá"
        if "KHOA ĐÃ PHÊ DUYỆT" in content:
            if "đã đánh giá Đề cương" in content:
                content = content.replace("đã đánh giá Đề cương", "đã phê duyệt Đề cương")
                changed = True
            if "đã đánh giá Báo cáo" in content:
                content = content.replace("đã đánh giá Báo cáo", "đã phê duyệt Báo cáo")
                changed = True
            if "đã đánh giá Slide" in content:
                content = content.replace("đã đánh giá Slide", "đã phê duyệt Slide")
                changed = True
            if "badge bg-primary" in content:
                content = content.replace("badge bg-primary", "badge bg-success")
                changed = True
            if "<p><strong>PGS.TS Khoa CNTT đã phê duyệt" in content and "🎉" not in content:
                content = content.replace("<p><strong>PGS.TS Khoa CNTT đã phê duyệt", "<p><strong>🎉 PGS.TS Khoa CNTT đã phê duyệt")
                changed = True

        if changed:
            n.content = content
            count += 1
            print(f"Updated Notification ID {n.id} for user {n.user_id}")

    db.session.commit()
    print(f"Total updated notifications: {count}")
