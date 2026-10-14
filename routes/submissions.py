import os
from flask import Blueprint, request, jsonify, send_file, session
from werkzeug.utils import secure_filename
from datetime import datetime

submissions_bp = Blueprint('submissions', __name__)

BASE_DIR = os.getcwd()
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'data', 'uploads', 'submissions')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'zip', 'rar', 'xlsx'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@submissions_bp.route('/api/submissions/upload', methods=['POST'])
def upload_submission_file():
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "Không tìm thấy file gửi lên."}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"success": False, "message": "Tên file rỗng. Vui lòng chọn file."}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        try:
            file.save(file_path)
            return jsonify({
                "success": True,
                "message": "Upload file thành công.",
                "data": {
                    "filename": filename,
                    "file_path": f"data/uploads/submissions/{filename}"
                }
            }), 201
        except Exception as e:
            return jsonify({"success": False, "message": f"Lỗi hệ thống khi lưu file: {str(e)}"}), 500

    return jsonify({"success": False, "message": "Định dạng file không được hỗ trợ."}), 400


@submissions_bp.route('/api/submissions/<int:sub_id>/feedback', methods=['POST'])
def add_submission_feedback(sub_id):
    """Lecturer adds feedback/note to a student submission"""
    role = session.get('role')
    if role not in ['lecturer', 'admin']:
        return jsonify({"success": False, "message": "Không có quyền thực hiện."}), 403

    from models import db, Submission, Notification, User, Topic
    from email_utils import send_notification_email

    sub = Submission.query.get(sub_id)
    if not sub:
        return jsonify({"success": False, "message": "Không tìm thấy bài nộp."}), 404

    data = request.get_json()
    new_note = data.get('feedback', '').strip()
    if not new_note:
        return jsonify({"success": False, "message": "Nội dung ghi chú không được để trống."}), 400

    from datetime import datetime, timedelta
    now = datetime.utcnow()
    vn_now = now + timedelta(hours=7)
    now_str = vn_now.strftime('%H:%M:%S %d/%m/%Y')
    
    appended_note = sub.feedback + f'\n\n--- {now_str} ---\n' + new_note if sub.feedback else f'[{now_str}] ' + new_note

    sub.feedback = appended_note
    sub.feedback_at = now
    db.session.commit()
    
    feedback_text = new_note

    # Notify the student
    uploader = User.query.get(sub.uploader_id)
    topic = Topic.query.get(sub.topic_id)
    if uploader and topic:
        notif_content = f"Giảng viên đã ghi chú cho bài nộp của bạn trong đề tài '{topic.title}': {feedback_text}"
        notif = Notification(user_id=uploader.id, content=notif_content)
        db.session.add(notif)
        db.session.commit()

        # Email
        try:
            send_notification_email(
                to_email=uploader.email,
                subject=f"[HOU S-RIMS] Giảng viên ghi chú cho bài nộp - {topic.title}",
                content=f"""Xin chào {uploader.full_name},

Giảng viên hướng dẫn vừa ghi chú cho bài báo cáo bạn đã nộp trong đề tài "{topic.title}":

📝 Ghi chú: {feedback_text}

Vui lòng xem lại và nộp lại nếu cần thiết tại: http://127.0.0.1:5000/student/submit

Trân trọng,
HOU S-RIMS"""
            )
        except Exception as e:
            print(f"Email error (feedback route): {e}")

    return jsonify({"success": True, "message": "Đã lưu ghi chú thành công."})


@submissions_bp.route('/api/submissions/download/<int:sub_id>', methods=['GET'])
def download_submission(sub_id):
    """Download a submission file"""
    from models import Submission
    sub = Submission.query.get(sub_id)
    if not sub:
        return jsonify({"success": False, "message": "Không tìm thấy bài nộp."}), 404

    file_path = os.path.join(BASE_DIR, sub.file_url)
    if not os.path.exists(file_path):
        return jsonify({"success": False, "message": "File không tồn tại trên server."}), 404

    return send_file(file_path, as_attachment=True)
