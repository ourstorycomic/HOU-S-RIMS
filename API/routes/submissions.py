import os
import time
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, send_file, session
from werkzeug.utils import secure_filename
from models import db, Submission, Topic, User, Notification, GroupMember, Group, Message, Milestone
from email_utils import send_email_async

submissions_bp = Blueprint('submissions_api', __name__, url_prefix='/api/submissions')

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar', '7z', 'ppt', 'pptx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

is_serverless = bool(os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME') or os.getenv('LAMBDA_TASK_ROOT'))
if is_serverless:
    SUBMISSIONS_UPLOAD_DIR = os.path.join('/tmp', 'uploads', 'submissions')
else:
    SUBMISSIONS_UPLOAD_DIR = os.path.join('static', 'uploads', 'submissions')
try:
    os.makedirs(SUBMISSIONS_UPLOAD_DIR, exist_ok=True)
except Exception:
    pass

TYPE_LABELS = {
    'outline': 'Đề cương nghiên cứu chi tiết',
    'progress': 'Báo cáo tiến độ',
    'final': 'Báo cáo tổng kết đề tài',
    'slide': 'Slide thuyết trình bảo vệ'
}

@submissions_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    Upload a submission file (outline, progress report, final report, slide)
    """
    try:
        user_id = session.get('user_id')
        topic_id = request.form.get('topic_id')
        uploader_id = request.form.get('uploader_id') or user_id
        sub_type = request.form.get('type') or 'outline'
        milestone_id = request.form.get('milestone_id')
        external_link = (request.form.get('external_link') or '').strip()
        notes = (request.form.get('notes') or '').strip()

        if not topic_id:
            return jsonify({'success': False, 'message': 'Thiếu thông tin Đề tài (topic_id).'}), 400
        
        topic = Topic.query.get(int(topic_id))
        if not topic:
            return jsonify({'success': False, 'message': 'Không tìm thấy đề tài.'}), 404

        file = request.files.get('file')
        if not file or file.filename == '':
            return jsonify({'success': False, 'message': 'Vui lòng đính kèm file báo cáo/đề cương.'}), 400

        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'Định dạng file không được hỗ trợ (chỉ nhận PDF, DOC, DOCX, PPTX, XLS, XLSX, ZIP).'}), 400

        original_filename = file.filename
        safe_name = secure_filename(original_filename)
        timestamp_prefix = int(time.time())
        saved_filename = f"{timestamp_prefix}_{safe_name}"
        save_path = os.path.join(SUBMISSIONS_UPLOAD_DIR, saved_filename)
        
        file.save(save_path)
        web_file_url = f"/{SUBMISSIONS_UPLOAD_DIR.replace(os.sep, '/')}/{saved_filename}"

        # Calculate version
        latest_prev = Submission.query.filter_by(topic_id=topic.id, type=sub_type).order_by(Submission.version.desc()).first()
        version = (latest_prev.version + 1) if latest_prev and latest_prev.version else 1

        # Xử lý an toàn cột mốc tiến độ (Milestone)
        assigned_milestone_id = None
        if sub_type == 'progress':
            actual_milestone = None
            if milestone_id and str(milestone_id).strip() not in ('', 'null', 'none', '0'):
                try:
                    ms_int = int(milestone_id)
                    actual_milestone = Milestone.query.filter_by(id=ms_int, topic_id=topic.id).first()
                    if not actual_milestone:
                        topic_milestones = Milestone.query.filter_by(topic_id=topic.id).order_by(Milestone.id.asc()).all()
                        if 1 <= ms_int <= len(topic_milestones):
                            actual_milestone = topic_milestones[ms_int - 1]
                except (ValueError, TypeError):
                    actual_milestone = None

            # Nếu đề tài chưa có mốc nào trong DB, tự động khởi tạo 4 mốc chuẩn
            existing_count = Milestone.query.filter_by(topic_id=topic.id).count()
            if existing_count == 0:
                default_names = [
                    "Đợt 1: Khảo sát tài liệu & Đề cương sơ bộ",
                    "Đợt 2: Thiết kế hệ thống & Thực nghiệm bước đầu",
                    "Đợt 3: Thu thập dữ liệu & Đánh giá kết quả",
                    "Đợt 4: Hoàn thiện bản thảo báo cáo toàn văn"
                ]
                created_ms = []
                for idx, m_name in enumerate(default_names):
                    dl = datetime.utcnow() + timedelta(days=30 * (idx + 1))
                    m_item = Milestone(
                        topic_id=topic.id,
                        name=m_name,
                        deadline=dl,
                        status='completed' if idx == 0 else ('in_progress' if idx == 1 else 'pending')
                    )
                    db.session.add(m_item)
                    created_ms.append(m_item)
                db.session.commit()

                # Gán milestone theo lựa chọn
                try:
                    c_idx = int(milestone_id) - 1 if milestone_id else 0
                    if 0 <= c_idx < len(created_ms):
                        actual_milestone = created_ms[c_idx]
                    else:
                        actual_milestone = created_ms[0]
                except Exception:
                    actual_milestone = created_ms[0]

            if actual_milestone:
                assigned_milestone_id = actual_milestone.id

        new_submission = Submission(
            topic_id=topic.id,
            uploader_id=int(uploader_id) if uploader_id else user_id,
            file_url=web_file_url,
            file_name=original_filename,
            type=sub_type,
            milestone_id=assigned_milestone_id,
            external_link=external_link if external_link else None,
            notes=notes if notes else None,
            status='submitted',
            version=version,
            submitted_at=datetime.utcnow()
        )
        db.session.add(new_submission)
        db.session.commit()

        # Send notification & email to mentor if assigned
        if topic.mentor_id:
            mentor = User.query.get(topic.mentor_id)
            if mentor:
                type_name = TYPE_LABELS.get(sub_type, 'Báo cáo/Tài liệu')
                notif_content = f"""
                <p><strong>Bài nộp mới từ nhóm nghiên cứu</strong></p>
                <p>Nhóm đề tài <strong>{topic.title}</strong> vừa nộp <strong>{type_name} (Phiên bản v{version})</strong>.</p>
                <a href="/lecturer/progress" class="btn btn-primary rounded-pill btn-sm mt-1">Xem & Nhận xét</a>
                """
                db.session.add(Notification(user_id=mentor.id, content=notif_content))
                db.session.commit()

                if mentor.email:
                    base_url = request.host_url.rstrip('/')
                    email_html_mentor = f"""
                    <div style='font-family: Arial, sans-serif; padding: 24px; color: #1e293b; background-color: #f8fafc; border-radius: 12px; max-width: 650px; margin: 0 auto; border: 1px solid #e2e8f0;'>
                        <div style='text-align: center; margin-bottom: 20px; border-bottom: 2px solid #2563eb; padding-bottom: 12px;'>
                            <h2 style='color: #1e40af; margin: 0; font-size: 22px;'>HỆ THỐNG QUẢN LÝ NCKH - HOU S-RIMS</h2>
                            <p style='color: #64748b; font-size: 13px; margin-top: 4px;'>Khoa Công nghệ Thông tin - Trường Đại học Mở Hà Nội</p>
                        </div>
                        <p>Kính gửi Thầy/Cô <strong>{mentor.full_name}</strong>,</p>
                        <p>Nhóm sinh viên thực hiện đề tài NCKH do Thầy/Cô hướng dẫn vừa nộp một bản báo cáo mới lên Hệ thống:</p>
                        <div style='background: white; border-radius: 8px; padding: 16px; margin: 16px 0; border: 1px solid #cbd5e1; box-shadow: 0 1px 3px rgba(0,0,0,0.05);'>
                            <p style='margin: 6px 0;'><strong>Tên đề tài:</strong> <span style='color: #0f172a;'>{topic.title}</span></p>
                            <p style='margin: 6px 0;'><strong>Loại tài liệu:</strong> <span style='color: #2563eb;'>{type_name}</span> (Phiên bản v{version})</p>
                            <p style='margin: 6px 0;'><strong>Tên tệp:</strong> {original_filename}</p>
                            {f"<p style='margin: 6px 0;'><strong>Ghi chú của SV:</strong> {notes}</p>" if notes else ""}
                            {f"<p style='margin: 6px 0;'><strong>Link bổ trợ:</strong> <a href='{external_link}' target='_blank'>{external_link}</a></p>" if external_link else ""}
                        </div>
                        <div style='text-align: center; margin: 24px 0;'>
                            <a href='{base_url}/lecturer/progress' style='display: inline-block; padding: 12px 28px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 30px; font-weight: bold; font-size: 14px;'>
                                Xem & Đánh giá Bài nộp
                            </a>
                        </div>
                        <hr style='border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;'>
                        <p style='color: #94a3b8; font-size: 12px; margin: 0; text-align: center;'>Email tự động từ Hệ thống Quản lý Nghiên cứu Khoa học Sinh viên HOU S-RIMS.</p>
                    </div>
                    """
                    try:
                        send_email_async(
                            mentor.email,
                            f"[HOU S-RIMS] Bài nộp mới {type_name} (v{version}) - Đề tài: {topic.title}",
                            f"Nhóm sinh viên vừa nộp {type_name} phiên bản {version} cho đề tài {topic.title}.",
                            email_html_mentor
                        )
                    except Exception as ex:
                        print(f"Error sending upload notification email: {ex}")

        return jsonify({
            'success': True,
            'message': f'Nộp {TYPE_LABELS.get(sub_type, "tài liệu")} thành công (Phiên bản {version})!',
            'submission': new_submission.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Lỗi hệ thống khi nộp tài liệu: {str(e)}'}), 500


@submissions_bp.route('/topic/<int:topic_id>', methods=['GET'])
def get_topic_submissions(topic_id):
    """
    Get all submissions for a given topic
    """
    topic = Topic.query.get_or_404(topic_id)
    sub_type = request.args.get('type')
    status = request.args.get('status')
    
    query = Submission.query.filter_by(topic_id=topic.id)
    if sub_type:
        query = query.filter_by(type=sub_type)
    if status:
        query = query.filter_by(status=status)
    
    submissions = query.order_by(Submission.submitted_at.desc()).all()
    return jsonify({
        'success': True,
        'topic_id': topic.id,
        'topic_title': topic.title,
        'submissions': [s.to_dict() for s in submissions]
    }), 200


@submissions_bp.route('/download/<int:sub_id>', methods=['GET'])
def download_file(sub_id):
    sub = Submission.query.get_or_404(sub_id)
    raw_path = sub.file_url.lstrip('/')
    if not os.path.exists(raw_path):
        # Fallback to app upload folder if saved under older path
        from flask import current_app
        raw_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), os.path.basename(sub.file_url))
    
    download_name = sub.file_name or os.path.basename(sub.file_url)
    return send_file(os.path.abspath(raw_path), as_attachment=True, download_name=download_name)


@submissions_bp.route('/<int:sub_id>/review', methods=['POST'])
def review_submission(sub_id):
    """
    Lecturer/Faculty reviews a submission (approves or requires revision, with feedback)
    """
    role = session.get('role')
    user_id = session.get('user_id')
    if role not in ['lecturer', 'faculty', 'admin']:
        return jsonify({"success": False, "message": "Không có quyền thực hiện."}), 403

    sub = Submission.query.get_or_404(sub_id)

    # Kiểm tra nếu sinh viên đã nộp bản mới hơn thì không cho phép chỉnh sửa/đánh giá bản cũ
    newer_sub = Submission.query.filter(
        Submission.topic_id == sub.topic_id,
        Submission.type == sub.type,
        Submission.milestone_id == sub.milestone_id,
        Submission.id != sub.id,
        (Submission.version > (sub.version or 1)) | (Submission.submitted_at > sub.submitted_at)
    ).first()
    if newer_sub:
        return jsonify({
            "success": False,
            "message": f"Không thể chỉnh sửa đánh giá bản nộp cũ (v{sub.version or 1}). Sinh viên đã nộp lại bản mới hơn (v{newer_sub.version or 'mới'}). Vui lòng nhận xét và đánh giá trên bản nộp mới nhất."
        }), 400

    if request.is_json:
        data = request.get_json() or {}
    else:
        data = request.form or {}
    
    new_status = data.get('status') # 'approved', 'revision_required'
    feedback_text = (data.get('feedback') or '').strip()
    
    # Xử lý đính kèm file nhận xét / bài sửa của Giảng viên nếu có
    feedback_file = request.files.get('feedback_file') or request.files.get('file')
    if feedback_file and feedback_file.filename != '':
        from werkzeug.utils import secure_filename
        filename = secure_filename(feedback_file.filename)
        if is_serverless:
            upload_dir = os.path.join('/tmp', 'uploads', 'submissions', 'feedback')
        else:
            upload_dir = os.path.join(request.environ.get('FLASK_APP_DIR', '.'), 'static', 'uploads', 'submissions', 'feedback')
        try:
            os.makedirs(upload_dir, exist_ok=True)
        except Exception:
            pass
        ts = int(datetime.utcnow().timestamp())
        unique_name = f"feedback_{sub.id}_{ts}_{filename}"
        save_path = os.path.join(upload_dir, unique_name)
        feedback_file.save(save_path)
        sub.feedback_file_url = f"uploads/submissions/feedback/{unique_name}"
        sub.feedback_file_name = filename
    
    if new_status not in ['approved', 'revision_required', 'submitted']:
        return jsonify({"success": False, "message": "Trạng thái đánh giá không hợp lệ."}), 400

    sub.status = new_status
    sub.reviewer_id = user_id
    
    if feedback_text:
        now = datetime.utcnow()
        vn_now = now + timedelta(hours=7)
        now_str = vn_now.strftime('%H:%M:%S %d/%m/%Y')
        appended_note = sub.feedback + f'\n\n--- {now_str} ---\n' + feedback_text if sub.feedback else f'[{now_str}] ' + feedback_text
        sub.feedback = appended_note
        sub.feedback_at = now
    
    db.session.commit()

    # Notify student team
    topic = Topic.query.get(sub.topic_id)
    reviewer = User.query.get(user_id)
    reviewer_name = reviewer.full_name if reviewer else "Giảng viên hướng dẫn"
    type_name = TYPE_LABELS.get(sub.type, 'Báo cáo/Tài liệu')
    
    if new_status == 'approved':
        status_label = "GVHD ĐÃ PHÊ DUYỆT (ĐẠT)"
        status_color = "success"
        notif_header = f"🎉 {reviewer_name} đã phê duyệt {type_name}"
    else:
        status_label = "GVHD YÊU CẦU CHỈNH SỬA"
        status_color = "warning"
        notif_header = f"⚠️ {reviewer_name} yêu cầu chỉnh sửa {type_name}"
    
    if topic and topic.group_id:
        group = Group.query.get(topic.group_id)
        member_ids = set()
        if group:
            if group.leader_id:
                member_ids.add(group.leader_id)
            for m in group.members:
                if m.status in ['accepted', 'joined'] or not m.status:
                    member_ids.add(m.student_id)
        if sub.uploader_id:
            member_ids.add(sub.uploader_id)

        for s_id in member_ids:
            notif_content = f"""
            <p><strong>{notif_header}</strong></p>
            <p>Đề tài: <strong>{topic.title}</strong> (v{sub.version} - {sub.file_name})</p>
            <p>Kết quả: <span class="badge bg-{status_color}">{status_label}</span></p>
            {f'<p class="small text-muted">Ghi chú: {feedback_text}</p>' if feedback_text else ''}
            {f'<p class="small text-primary"><i class="fa-solid fa-paperclip me-1"></i><strong>Giảng viên đã đính kèm tài liệu góp ý:</strong> <a href="/static/{sub.feedback_file_url}" target="_blank">{sub.feedback_file_name}</a></p>' if sub.feedback_file_url else ''}
            <a href="/student#s-submit" class="btn btn-outline-primary btn-sm rounded-pill mt-1">Xem Chi tiết</a>
            """
            db.session.add(Notification(user_id=s_id, content=notif_content))
        db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Đã cập nhật đánh giá bài nộp: {status_label}",
        "submission": sub.to_dict()
    }), 200


@submissions_bp.route('/<int:sub_id>/feedback', methods=['POST'])
def add_feedback(sub_id):
    """
    Backward compatibility for feedback note addition
    """
    role = session.get('role')
    user_id = session.get('user_id')
    if role not in ['lecturer', 'faculty', 'admin']:
        return jsonify({"success": False, "message": "Không có quyền thực hiện."}), 403

    sub = Submission.query.get_or_404(sub_id)

    # Kiểm tra nếu sinh viên đã nộp bản mới hơn thì khóa chỉnh sửa bản cũ
    newer_sub = Submission.query.filter(
        Submission.topic_id == sub.topic_id,
        Submission.type == sub.type,
        Submission.milestone_id == sub.milestone_id,
        Submission.id != sub.id,
        (Submission.version > (sub.version or 1)) | (Submission.submitted_at > sub.submitted_at)
    ).first()
    if newer_sub:
        return jsonify({
            "success": False,
            "message": f"Không thể chỉnh sửa ghi chú bản nộp cũ (v{sub.version or 1}). Sinh viên đã nộp lại bản mới hơn (v{newer_sub.version or 'mới'}). Vui lòng nhận xét trên bản nộp mới nhất."
        }), 400

    data = request.get_json() or {}
    new_note = (data.get('feedback') or '').strip()
    status_update = data.get('status')
    
    if not new_note and not status_update:
        return jsonify({"success": False, "message": "Nội dung ghi chú không được để trống."}), 400

    now = datetime.utcnow()
    vn_now = now + timedelta(hours=7)
    now_str = vn_now.strftime('%H:%M:%S %d/%m/%Y')
    
    if new_note:
        appended_note = sub.feedback + f'\n\n--- {now_str} ---\n' + new_note if sub.feedback else f'[{now_str}] ' + new_note
        sub.feedback = appended_note
        sub.feedback_at = now
        
    if status_update in ['approved', 'revision_required', 'submitted']:
        sub.status = status_update
        
    sub.reviewer_id = user_id
    db.session.commit()

    # Notify uploader
    uploader = User.query.get(sub.uploader_id)
    topic = Topic.query.get(sub.topic_id)
    lecturer = User.query.get(user_id)

    if uploader and topic:
        lecturer_name = lecturer.full_name if lecturer else "Giảng viên"
        notif_content = f"📝 {lecturer_name} đã ghi chú bài nộp '{sub.file_name or sub.type}' trong đề tài '{topic.title}': {new_note}"
        db.session.add(Notification(user_id=uploader.id, content=notif_content))
        db.session.commit()

    return jsonify({"success": True, "message": "Đã lưu ghi chú thành công.", "submission": sub.to_dict()})


@submissions_bp.route('/<int:sub_id>/faculty-review', methods=['POST'])
def faculty_review_submission(sub_id):
    """
    Faculty approves or requests revision on an approved submission with official faculty comments
    """
    role = session.get('role')
    user_id = session.get('user_id')
    if role not in ['faculty', 'admin']:
        return jsonify({"success": False, "message": "Chỉ Quản trị Khoa mới có quyền phê duyệt cấp Khoa."}), 403

    sub = Submission.query.get_or_404(sub_id)
    data = request.get_json() or {}
    
    new_status = data.get('faculty_status') or 'approved' # 'approved', 'revision_required'
    feedback_text = (data.get('faculty_feedback') or '').strip()
    approve_topic_flag = data.get('approve_topic', True)

    sub.faculty_status = new_status
    sub.faculty_reviewer_id = user_id
    sub.faculty_reviewed_at = datetime.utcnow()
    
    now = datetime.utcnow()
    vn_now = now + timedelta(hours=7)
    now_str = vn_now.strftime('%H:%M:%S %d/%m/%Y')
    
    if feedback_text:
        appended_note = sub.faculty_feedback + f'\n\n--- {now_str} ---\n' + feedback_text if sub.faculty_feedback else f'[{now_str}] ' + feedback_text
        sub.faculty_feedback = appended_note
    elif new_status == 'approved' and not sub.faculty_feedback:
        sub.faculty_feedback = f'[{now_str}] Khoa CNTT đã phê duyệt thông qua bản báo cáo/đề cương này.'

    topic = Topic.query.get(sub.topic_id)
    # If approving outline, also ensure topic status is approved
    if new_status == 'approved' and approve_topic_flag and topic and topic.status != 'approved':
        topic.status = 'approved'

    db.session.commit()

    faculty_user = User.query.get(user_id)
    faculty_name = faculty_user.full_name if faculty_user else "Ban Chủ nhiệm Khoa"
    type_name = TYPE_LABELS.get(sub.type, 'Báo cáo/Tài liệu')
    base_url = request.host_url.rstrip('/')

    if new_status == 'approved':
        status_label = "KHOA ĐÃ PHÊ DUYỆT ĐẠT YÊU CẦU"
        status_color = "success"
        status_bg = "#ecfdf5"
        status_fg = "#065f46"
        status_badge_text = "✔ ĐẠT YÊU CẦU (Khoa đã phê duyệt)"
        feedback_bg = "#eff6ff"
        feedback_border = "#3b82f6"
        feedback_header = "#1e40af"
        notif_header = f"🎉 Khoa CNTT đã phê duyệt {type_name}"
    else:
        status_label = "KHOA YÊU CẦU CHỈNH SỬA / HOÀN THIỆN"
        status_color = "danger"
        status_bg = "#fef2f2"
        status_fg = "#991b1b"
        status_badge_text = "⚠ CẦN CHỈNH SỬA LẠI (Cấp Khoa yêu cầu)"
        feedback_bg = "#fffbeb"
        feedback_border = "#f59e0b"
        feedback_header = "#b45309"
        notif_header = f"⚠️ Khoa CNTT yêu cầu chỉnh sửa {type_name}"

    # 1. Notify & Email Mentor
    mentor = User.query.get(topic.mentor_id) if (topic and topic.mentor_id) else None
    if mentor:
        mentor_notif = f"""
        <p><strong>{notif_header}</strong></p>
        <p>Đề tài: <strong>{topic.title}</strong> (v{sub.version} - {sub.file_name})</p>
        <p>Quyết định cấp Khoa: <span class="badge bg-{status_color}">{status_label}</span></p>
        {f'<p class="small text-muted"><strong>Ý kiến chỉ đạo từ Khoa:</strong> {feedback_text}</p>' if feedback_text else ''}
        <a href="/lecturer/progress" class="btn btn-primary btn-sm rounded-pill mt-1">Xem Tiến độ Đề tài</a>
        """
        db.session.add(Notification(user_id=mentor.id, content=mentor_notif))

        if mentor.email:
            email_html_mentor = f"""
            <div style='font-family: Arial, sans-serif; padding: 24px; color: #1e293b; background-color: #f8fafc; border-radius: 12px; max-width: 650px; margin: 0 auto; border: 1px solid #e2e8f0;'>
                <div style='text-align: center; margin-bottom: 20px; border-bottom: 2px solid #2563eb; padding-bottom: 12px;'>
                    <h2 style='color: #1e40af; margin: 0; font-size: 22px;'>HỆ THỐNG QUẢN LÝ NCKH - HOU S-RIMS</h2>
                    <p style='color: #64748b; font-size: 13px; margin-top: 4px;'>Khoa Công nghệ Thông tin - Trường Đại học Mở Hà Nội</p>
                </div>
                <p>Kính gửi Thầy/Cô <strong>{mentor.full_name}</strong>,</p>
                <p>Ban Chủ nhiệm Khoa đã đánh giá và cập nhật phê duyệt cho bài nộp/báo cáo của đề tài NCKH do Thầy/Cô hướng dẫn:</p>
                <div style='background: white; border-radius: 8px; padding: 16px; margin: 16px 0; border: 1px solid #cbd5e1; box-shadow: 0 1px 3px rgba(0,0,0,0.05);'>
                    <p style='margin: 6px 0;'><strong>Tên đề tài:</strong> <span style='color: #0f172a;'>{topic.title}</span></p>
                    <p style='margin: 6px 0;'><strong>Loại tài liệu:</strong> <span style='color: #2563eb;'>{type_name}</span> (Phiên bản v{sub.version})</p>
                    <p style='margin: 6px 0;'><strong>Tệp đính kèm:</strong> {sub.file_name}</p>
                    <p style='margin: 6px 0;'><strong>Quyết định của Khoa:</strong> <span style='display: inline-block; padding: 4px 12px; background-color: {status_bg}; color: {status_fg}; border-radius: 20px; font-weight: bold; font-size: 13px;'>{status_badge_text}</span></p>
                    {f"<div style='margin-top: 12px; padding: 12px; background: {feedback_bg}; border-left: 4px solid {feedback_border}; border-radius: 4px;'><strong style='color: {feedback_header};'>Ý kiến / Chỉ đạo của Khoa:</strong><p style='margin: 6px 0 0 0; white-space: pre-wrap; font-size: 13px; color: #334155;'>{feedback_text}</p></div>" if feedback_text else ""}
                </div>
                <div style='text-align: center; margin: 24px 0;'>
                    <a href='{base_url}/lecturer/progress' style='display: inline-block; padding: 12px 28px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 30px; font-weight: bold; font-size: 14px; text-decoration: none;'>
                        Xem Tiến độ & Báo cáo Đề tài
                    </a>
                </div>
                <hr style='border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;'>
                <p style='color: #94a3b8; font-size: 12px; margin: 0; text-align: center;'>Email tự động từ Hệ thống Quản lý Nghiên cứu Khoa học Sinh viên HOU S-RIMS.</p>
            </div>
            """
            try:
                send_email_async(
                    mentor.email,
                    f"[HOU S-RIMS] Khoa đã phê duyệt {type_name} - Đề tài: {topic.title}",
                    f"Khoa đã cập nhật phê duyệt {type_name} cho đề tài {topic.title}: {status_label}",
                    email_html_mentor
                )
            except Exception as ex:
                print(f"Error triggering mentor email: {ex}")

    # 2. Notify & Email All Students in Group & Uploader
    student_ids = set()
    if sub.uploader_id:
        student_ids.add(sub.uploader_id)
    group = Group.query.get(topic.group_id) if (topic and topic.group_id) else (topic.group if topic else None)
    if group:
        if group.leader_id:
            student_ids.add(group.leader_id)
        for m in group.members:
            if m.status in ['accepted', 'joined'] or not m.status:
                student_ids.add(m.student_id)

    for s_id in student_ids:
        stu = User.query.get(s_id)
        if stu:
            student_notif = f"""
            <p><strong>{notif_header}</strong></p>
            <p>Đề tài: <strong>{topic.title}</strong> (v{sub.version} - {sub.file_name})</p>
            <p>Kết quả cấp Khoa: <span class="badge bg-{status_color}">{status_label}</span></p>
            {f'<p class="small text-muted"><strong>Ý kiến chỉ đạo của Khoa:</strong> {feedback_text}</p>' if feedback_text else ''}
            <a href="/student#s-submit" class="btn btn-outline-primary btn-sm rounded-pill mt-1">Xem Hồ sơ Bài nộp</a>
            """
            db.session.add(Notification(user_id=stu.id, content=student_notif))

            if stu.email:
                email_html_stu = f"""
                <div style='font-family: Arial, sans-serif; padding: 24px; color: #1e293b; background-color: #f8fafc; border-radius: 12px; max-width: 650px; margin: 0 auto; border: 1px solid #e2e8f0;'>
                    <div style='text-align: center; margin-bottom: 20px; border-bottom: 2px solid #059669; padding-bottom: 12px;'>
                        <h2 style='color: #047857; margin: 0; font-size: 22px;'>HỆ THỐNG QUẢN LÝ NCKH - HOU S-RIMS</h2>
                        <p style='color: #64748b; font-size: 13px; margin-top: 4px;'>Khoa Công nghệ Thông tin - Trường Đại học Mở Hà Nội</p>
                    </div>
                    <p>Xin chào <strong>{stu.full_name}</strong>,</p>
                    <p>Ban Chủ nhiệm Khoa đã đánh giá và cập nhật phê duyệt cho bài nộp/báo cáo NCKH của nhóm bạn:</p>
                    <div style='background: white; border-radius: 8px; padding: 16px; margin: 16px 0; border: 1px solid #cbd5e1; box-shadow: 0 1px 3px rgba(0,0,0,0.05);'>
                        <p style='margin: 6px 0;'><strong>Tên đề tài:</strong> <span style='color: #0f172a;'>{topic.title}</span></p>
                        <p style='margin: 6px 0;'><strong>Loại tài liệu:</strong> <span style='color: #2563eb;'>{type_name}</span> (Phiên bản v{sub.version})</p>
                        <p style='margin: 6px 0;'><strong>Tệp báo cáo:</strong> {sub.file_name}</p>
                        <p style='margin: 6px 0;'><strong>Giảng viên hướng dẫn:</strong> {mentor.full_name if mentor else 'Khoa CNTT'}</p>
                        <p style='margin: 6px 0;'><strong>Kết quả phê duyệt từ Khoa:</strong> <span style='display: inline-block; padding: 4px 12px; background-color: {status_bg}; color: {status_fg}; border-radius: 20px; font-weight: bold; font-size: 13px;'>{status_badge_text}</span></p>
                        {f"<div style='margin-top: 12px; padding: 12px; background: {feedback_bg}; border-left: 4px solid {feedback_border}; border-radius: 4px;'><strong style='color: {feedback_header};'>Ý kiến / Chỉ đạo của Khoa:</strong><p style='margin: 6px 0 0 0; white-space: pre-wrap; font-size: 13px; color: #334155;'>{feedback_text}</p></div>" if feedback_text else ""}
                    </div>
                    <div style='text-align: center; margin: 24px 0;'>
                        <a href='{base_url}/student/submit' style='display: inline-block; padding: 12px 28px; background-color: #059669; color: white; text-decoration: none; border-radius: 30px; font-weight: bold; font-size: 14px;'>
                            Xem Chi tiết Hồ sơ Bài nộp
                        </a>
                    </div>
                    <hr style='border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;'>
                    <p style='color: #94a3b8; font-size: 12px; margin: 0; text-align: center;'>Email tự động từ Hệ thống Quản lý Nghiên cứu Khoa học Sinh viên HOU S-RIMS.</p>
                </div>
                """
                try:
                    send_email_async(
                        stu.email,
                        f"[HOU S-RIMS] Khoa đã phê duyệt {type_name} - Đề tài: {topic.title}",
                        f"Khoa đã cập nhật phê duyệt {type_name} cho đề tài {topic.title}: {status_label}",
                        email_html_stu
                    )
                except Exception as ex:
                    print(f"Error triggering student email: {ex}")

    # 3. Add Announcement Message to Group Chat
    if topic and topic.group_id:
        try:
            chat_msg = Message(
                group_id=topic.group_id,
                sender_id=user_id,
                receiver_id=None,
                content=f"📢 **THÔNG BÁO TỪ KHOA CNTT**\nKhoa đã cập nhật phê duyệt cho **{type_name}** (v{sub.version} - {sub.file_name}): **{status_label}**.\n" + (f"👉 **Ý kiến chỉ đạo của Khoa:**\n{feedback_text}" if feedback_text else ""),
                message_type='text'
            )
            db.session.add(chat_msg)
        except Exception as ex:
            print(f"Error adding group chat announcement: {ex}")

    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Khoa đã cập nhật phê duyệt: {status_label}",
        "submission": sub.to_dict()
    }), 200

@submissions_bp.route('/<int:sub_id>/feedback-file', methods=['GET'])
def download_feedback_file(sub_id):
    sub = Submission.query.get_or_404(sub_id)
    if not sub.feedback_file_url:
        return jsonify({"error": "Không có file đính kèm phản hồi"}), 404
    file_path = os.path.join('static', sub.feedback_file_url)
    if not os.path.exists(file_path):
        return jsonify({"error": "File không tồn tại trên hệ thống"}), 404
    return send_file(os.path.abspath(file_path), as_attachment=True, download_name=sub.feedback_file_name or os.path.basename(file_path))
