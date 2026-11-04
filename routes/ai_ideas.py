# routes/ai_ideas.py
from flask import Blueprint, request, jsonify, session
from models import db, Topic, User, Batch
from API.InsightEngine import chat_groq_ideas

ai_ideas_bp = Blueprint('ai_ideas', __name__)

@ai_ideas_bp.route('/api/ai/explore-data', methods=['GET'])
def get_explore_data():
    """Lấy dữ liệu động từ DB cho tab Khám phá ý tưởng."""
    try:
        # 1. Các lĩnh vực nghiên cứu thực tế trong DB
        field_records = db.session.query(Topic.field).distinct().filter(Topic.field.isnot(None)).all()
        fields = [f[0] for f in field_records if f[0] and f[0].strip()]

        # 2. Danh sách đề tài tiêu biểu đã phê duyệt
        topics = Topic.query.filter_by(status='approved').order_by(Topic.id.asc()).limit(9).all()
        topics_data = []
        for t in topics:
            topics_data.append({
                "id": t.id,
                "title": t.title,
                "field": t.field or "Công nghệ thông tin",
                "mentor_name": t.mentor.full_name if t.mentor else "Chưa phân công",
                "description": t.description or ""
            })

        # 3. Danh sách Giảng viên hướng dẫn Khoa CNTT
        mentors = User.query.filter_by(role='lecturer').order_by(User.id.asc()).all()
        mentors_data = []
        for m in mentors:
            mentors_data.append({
                "id": m.id,
                "name": m.full_name,
                "email": m.email,
                "bio": m.bio or "Giảng viên Khoa Công nghệ thông tin",
                "faculty": m.faculty or "Khoa Công nghệ thông tin"
            })

        return jsonify({
            "success": True,
            "fields": fields,
            "topics": topics_data,
            "mentors": mentors_data
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@ai_ideas_bp.route('/api/ai/chat-ideas', methods=['POST'])
def chat_ideas():
    """Chatbot AI gợi ý ý tưởng NCKH sử dụng Groq API đọc dữ liệu thực tế từ Database."""
    try:
        data = request.get_json() or {}
        user_message = data.get('message', '').strip()
        history = data.get('history', [])

        if not user_message:
            return jsonify({"success": False, "error": "Vui lòng nhập nội dung câu hỏi hoặc yêu cầu ý tưởng."}), 400

        # 1. Đọc dữ liệu thực tế từ Database để làm Context cho AI
        all_topics = Topic.query.all()
        all_mentors = User.query.filter_by(role='lecturer').all()
        active_batch = Batch.query.filter_by(status='active').first()

        # Tổng hợp danh sách đề tài
        topics_summary_lines = []
        for idx, t in enumerate(all_topics[:30], 1):
            m_name = t.mentor.full_name if t.mentor else "Chưa phân công"
            field_name = t.field or "CNTT"
            topics_summary_lines.append(f"- #{idx}: {t.title} (Lĩnh vực: {field_name} | GVHD: {m_name})")
        topics_summary = "\n".join(topics_summary_lines)

        # Tổng hợp danh sách giảng viên & chuyên môn
        mentors_summary_lines = []
        for m in all_mentors:
            bio_info = m.bio or "Công nghệ phần mềm, Hệ thống thông tin"
            mentors_summary_lines.append(f"- {m.full_name} (Email: {m.email}) - Chuyên môn: {bio_info}")
        mentors_summary = "\n".join(mentors_summary_lines)

        batch_name = active_batch.name if active_batch else "NCKH Sinh viên năm học 2026 - 2027"

        # 2. Xây dựng System Prompt với dữ liệu thật từ DB
        system_prompt = f"""Bạn là "Cố vấn AI Nghiên cứu Khoa học Sinh viên Khoa Công nghệ Thông tin - Trường Đại học Mở Hà Nội (HOU S-RIMS)".
Nhiệm vụ của bạn là đồng hành, tư vấn và gợi ý các ý tưởng đề tài NCKH sinh viên sáng tạo, khả thi và bám sát thực tiễn nghiên cứu tại Trường Đại học Mở Hà Nội (Niên khóa: {batch_name}).

[CƠ SỞ TRI THỨC THỰC TẾ TRONG DATABASE KHOA CNTT - HOU]:
--- DANH MỤC CÁC ĐỀ TÀI ĐÃ VÀ ĐANG THỰC HIỆN TRONG KHOA ---
{topics_summary}

--- DANH SÁCH GIẢNG VIÊN HƯỚNG DẪN KHOA CNTT & HƯỚNG NGHIÊN CỨU ---
{mentors_summary}

[QUY TẮC PHẢN HỒI]:
1. Khi sinh viên hỏi về ý tưởng đề tài (theo hướng bất kỳ như AI, Thị giác máy tính, NLP, An toàn thông tin, IoT, Web/App, Chuyển đổi số, v.v.):
   - Đưa ra 2 đến 3 ý tưởng đề tài cụ thể, có tính mới và phù hợp năng lực sinh viên đại học.
   - Với mỗi ý tưởng, trình bày rõ:
     • **Tên đề tài dự kiến**: Đặt tên chuẩn mực NCKH.
     • **Mục tiêu & Đóng góp**: Giải quyết bài toán gì, tính mới là gì.
     • **Công nghệ / Kỹ thuật đề xuất**: (VD: Python, PyTorch, YOLOv8, Transformers, FastAPI, React, OpenCV, v.v.).
     • **Giảng viên hướng dẫn phù hợp trong Khoa**: Nêu ĐÍCH DANH Thầy/Cô từ danh sách GV của Khoa ở trên và giải thích lý do vì sao Thầy/Cô đó phù hợp.
2. Trả lời bằng tiếng Việt chuyên nghiệp, súc tích, cấu trúc Markdown rõ ràng (h3, h4, gạch đầu dòng, in đậm).
3. Hạn chế tối đa việc lạm dụng emoji và icon hoạt hình (như 🤖, 🚀, 💡, ✨, 🌟, 🔥, 👋) để giữ văn phong học thuật, chỉn chu và hiện đại.
3. Luôn giữ phong thái chuyên gia nghiên cứu sư phạm, ân cần và mang tính định hướng cao.
"""

        # 3. Chuẩn bị lịch sử hội thoại
        messages = []
        for h in history[-6:]: # Giữ tối đa 6 lượt trao đổi gần nhất
            messages.append({
                "role": h.get("role", "user"),
                "content": h.get("content", "")
            })
        messages.append({
            "role": "user",
            "content": user_message
        })

        # 4. Gọi Groq AI qua InsightEngine
        reply = chat_groq_ideas(messages, system_prompt=system_prompt)

        return jsonify({
            "success": True,
            "reply": reply
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Lỗi xử lý yêu cầu AI: {str(e)}"
        }), 500

