import os
from flask import Blueprint, request, jsonify, send_file, session
from werkzeug.utils import secure_filename
from models import db, Submission
from datetime import datetime

submissions_bp = Blueprint('submissions_api', __name__, url_prefix='/api/submissions')

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar', '7z', 'ppt', 'pptx', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@submissions_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    Upload a submission file
    ---
    tags:
      - Submissions
    """
    from app import app
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if not request.form.get('topic_id') or not request.form.get('uploader_id') or not request.form.get('type'):
        return jsonify({'error': 'Missing metadata (topic_id, uploader_id, type)'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        try:
            milestone_id = request.form.get('milestone_id')
            new_submission = Submission(
                topic_id=int(request.form['topic_id']),
                uploader_id=int(request.form['uploader_id']),
                file_url=file_path,
                type=request.form['type'],
                milestone_id=int(milestone_id) if milestone_id else None
            )
            db.session.add(new_submission)
            db.session.commit()
            return jsonify({'message': 'File uploaded successfully', 'file_url': file_path}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'File type not allowed'}), 400


@submissions_bp.route('/download/<int:sub_id>', methods=['GET'])
def download_file(sub_id):
    sub = Submission.query.get_or_404(sub_id)
    return send_file(sub.file_url, as_attachment=True)


@submissions_bp.route('/<int:sub_id>/feedback', methods=['POST'])
def add_feedback(sub_id):
    """Lecturer adds feedback/note to a student submission"""
    role = session.get('role')
    if role not in ['lecturer', 'admin']:
        return jsonify({"success": False, "message": "Không có quyền thực hiện."}), 403

    from models import Notification, User, Topic
    from email_utils import send_notification_email

    sub = Submission.query.get(sub_id)
    if not sub:
        return jsonify({"success": False, "message": "Không tìm thấy bài nộp."}), 404

    data = request.get_json()
    feedback_text = (data.get('feedback') or '').strip()
    if not feedback_text:
        return jsonify({"success": False, "message": "Nội dung ghi chú không được để trống."}), 400

    sub.feedback = feedback_text
    sub.feedback_at = datetime.utcnow()
    db.session.commit()

    uploader = User.query.get(sub.uploader_id)
    topic = Topic.query.get(sub.topic_id)
    lecturer = User.query.get(session.get('user_id'))

    if uploader and topic:
        lecturer_name = lecturer.full_name if lecturer else "Giảng viên"
        notif_content = f"📝 {lecturer_name} đã ghi chú cho bài nộp của bạn trong đề tài '{topic.title}': {feedback_text}"
        notif = Notification(user_id=uploader.id, content=notif_content)
        db.session.add(notif)
        db.session.commit()

        try:
            send_notification_email(
                to_email=uploader.email,
                subject=f"[HOU S-RIMS] Giảng viên ghi chú cho bài nộp - {topic.title}",
                body=f"""Xin chào {uploader.full_name},

Giảng viên {lecturer_name} vừa ghi chú cho bài báo cáo bạn đã nộp trong đề tài "{topic.title}":

📝 Ghi chú: {feedback_text}

Vui lòng xem lại và nộp lại nếu cần thiết tại:
http://127.0.0.1:5000/student/submit

Trân trọng,
HOU S-RIMS"""
            )
        except Exception:
            pass

    return jsonify({"success": True, "message": "Đã lưu ghi chú thành công."})
