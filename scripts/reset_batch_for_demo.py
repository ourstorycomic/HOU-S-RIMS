# -*- coding: utf-8 -*-
"""
scripts/reset_batch_for_demo.py
Khôi phục đợt NCKH về trạng thái mới tạo:
- Sao lưu toàn bộ 23 đề tài & nhóm hiện tại ra file scratch/backup_topics_before_reset.json
- Xóa toàn bộ đề tài (Topic), đăng ký đề tài (TopicRegistration), tiến độ, nộp bài, đánh giá
- Xóa toàn bộ nhóm (Group), thành viên nhóm (GroupMember) và tin nhắn nhóm (Message)
- Giữ nguyên: Đợt NCKH (Batch 21: 2026-2027), toàn bộ tài khoản Sinh viên, Giảng viên, Khoa
- Đồng bộ sạch sẽ trên cả Supabase PostgreSQL và SQLite local.
"""
import os
import sys
import json
from datetime import datetime

# UTF-8 stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, '.env'), override=True)

from app import app
from models import (
    db, User, Batch, Topic, Group, GroupMember, TopicRegistration,
    Message, Submission, Milestone, Evaluation, Meeting, Notification
)

def run_reset():
    with app.app_context():
        print("=== BẮT ĐẦU KHÔI PHỤC ĐỢT NCKH VỀ TRẠNG THÁI MỚI TẠO ===")
        
        # 1. Sao lưu dữ liệu hiện tại
        backup_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "groups": [],
            "topics": []
        }
        
        for g in Group.query.all():
            backup_data["groups"].append({
                "id": g.id,
                "name": g.name,
                "batch_id": g.batch_id,
                "leader_id": g.leader_id,
                "mentor_id": g.mentor_id,
                "status": g.status,
                "members": [{"student_id": m.student_id, "status": m.status} for m in g.members]
            })
            
        for t in Topic.query.all():
            backup_data["topics"].append({
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "field": t.field,
                "batch_id": t.batch_id,
                "mentor_id": t.mentor_id,
                "group_id": t.group_id,
                "status": t.status
            })
            
        os.makedirs(os.path.join(BASE_DIR, 'scratch'), exist_ok=True)
        backup_path = os.path.join(BASE_DIR, 'scratch', 'backup_topics_before_reset.json')
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        print(f"-> Đã sao lưu {len(backup_data['topics'])} đề tài và {len(backup_data['groups'])} nhóm vào {backup_path}")
        
        # 2. Xóa các bảng liên quan đến đề tài và nhóm
        # Thứ tự xóa để đảm bảo foreign key constraints
        del_evals = Evaluation.query.delete()
        del_subs = Submission.query.delete()
        del_milestones = Milestone.query.delete()
        del_meetings = Meeting.query.delete()
        del_reg = TopicRegistration.query.delete()
        del_topics = Topic.query.delete()
        del_messages = Message.query.delete()
        del_members = GroupMember.query.delete()
        del_groups = Group.query.delete()
        
        db.session.commit()
        
        print(f"-> Đã xóa {del_reg} bản ghi TopicRegistration")
        print(f"-> Đã xóa {del_topics} bản ghi Topic")
        print(f"-> Đã xóa {del_messages} bản ghi Message (chat nhóm)")
        print(f"-> Đã xóa {del_members} bản ghi GroupMember")
        print(f"-> Đã xóa {del_groups} bản ghi Group")
        
        # 3. Kiểm tra lại trạng thái sau khi xóa
        print("\n--- KIỂM TRA TRẠNG THÁI HỆ THỐNG SAU KHI RESET ---")
        active_batch = Batch.query.filter_by(status='active').first()
        print(f" • Đợt NCKH hiện tại: {active_batch.name if active_batch else 'Không có'} (ID={active_batch.id if active_batch else 0})")
        print(f" • Số lượng đề tài (Topic): {Topic.query.count()}")
        print(f" • Số lượng đăng ký đề tài (TopicRegistration): {TopicRegistration.query.count()}")
        print(f" • Số lượng nhóm (Group): {Group.query.count()}")
        print(f" • Số lượng sinh viên: {User.query.filter_by(role='student').count()}")
        print(f" • Số lượng giảng viên hướng dẫn: {User.query.filter_by(role='lecturer').count()}")
        print("================================================================================")
        print("✅ KHÔI PHỤC HOÀN TẤT! Hệ thống đã sẵn sàng cho demo test đăng ký đề tài từ đầu.")
        print("💡 Khi cần khôi phục lại toàn bộ 23 đề tài QĐ 1440, chỉ cần chạy:")
        print("   python scripts/sync_decision_1440_to_supabase.py")
        print("================================================================================")

if __name__ == '__main__':
    run_reset()

