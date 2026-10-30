from flask import Blueprint, request, jsonify
from models import db, Batch
from datetime import datetime

batches_bp = Blueprint('batches', __name__, url_prefix='/api/batches')

@batches_bp.route('', methods=['POST'])
def create_batch():
    """
    Create a new batch
    ---
    tags:
      - Batches
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              example: Đợt 1 NCKH 2026
            start_date:
              type: string
              example: 2026-09-01
            end_date:
              type: string
              example: 2026-12-31
    responses:
      201:
        description: Batch created successfully
      400:
        description: Invalid input
    """
    if request.is_json:
        data = request.get_json() or {}
    else:
        data = request.form or {}
    
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'Thiếu trường bắt buộc: Tên đợt (name)'}), 400

    academic_year = (data.get('academic_year') or '2025-2026').strip()
    # Ràng buộc nghiệp vụ: Mỗi năm học chỉ được triển khai duy nhất 1 đợt NCKH
    existing_batch = Batch.query.filter(Batch.academic_year == academic_year, Batch.status == 'active').first()
    
    if existing_batch:
        msg = f"Năm học {academic_year} đã có đợt NCKH '{existing_batch.name}' đang có hiệu lực. Theo quy định, mỗi năm học chỉ được triển khai 1 đợt NCKH duy nhất. Vui lòng xóa hoặc kết thúc đợt hiện tại trước khi triển khai đợt mới cho năm học này."
        return jsonify({'error': msg}), 400
        
    import os
    from werkzeug.utils import secure_filename
    
    try:
        batch_name = (data.get('name') or '').strip()
        if not batch_name or len(batch_name) < 3:
            return jsonify({'error': 'Tên Đợt NCKH phải có ít nhất 3 ký tự!'}), 400

        if not data.get('start_date'):
            return jsonify({'error': 'Vui lòng chọn Ngày bắt đầu đợt NCKH!'}), 400
        if not data.get('end_date'):
            return jsonify({'error': 'Vui lòng chọn Ngày kết thúc đợt NCKH!'}), 400

        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Định dạng Ngày bắt đầu không hợp lệ (YYYY-MM-DD)'}), 400

        try:
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Định dạng Ngày kết thúc không hợp lệ (YYYY-MM-DD)'}), 400

        if start_date > end_date:
            return jsonify({'error': 'Ngày bắt đầu không được lớn hơn ngày kết thúc đợt!'}), 400

        if data.get('submission_deadline'):
            try:
                submission_deadline = datetime.strptime(data['submission_deadline'], '%Y-%m-%d')
            except ValueError:
                return jsonify({'error': 'Định dạng Hạn nộp báo cáo không hợp lệ (YYYY-MM-DD)'}), 400
            if submission_deadline < start_date or submission_deadline > end_date:
                return jsonify({'error': 'Hạn nộp báo cáo phải nằm trong khoảng từ Ngày bắt đầu đến Ngày kết thúc đợt!'}), 400
        else:
            submission_deadline = end_date
            
        doc_filenames = []
        doc_paths = []
        files = request.files.getlist('guidance_doc')
        is_serverless = bool(os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME') or os.getenv('LAMBDA_TASK_ROOT'))
        if is_serverless:
            upload_dir = '/tmp/uploads/batches'
        else:
            upload_dir = os.path.join(request.environ.get('FLASK_APP_DIR', '.'), 'static', 'uploads', 'batches')
        try:
            os.makedirs(upload_dir, exist_ok=True)
        except Exception:
            pass
        
        for file in files:
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                doc_path = os.path.join(upload_dir, filename)
                file.save(doc_path)
                doc_filenames.append(filename)
                doc_paths.append(doc_path)
                
        doc_filename_str = '|'.join(doc_filenames) if doc_filenames else ''
        
        new_batch = Batch(
            name=data['name'],
            type=data.get('type', 'NCKH Standard'),
            start_date=start_date,
            end_date=end_date,
            submission_deadline=submission_deadline,
            status=data.get('status', 'active'),
            academic_year=data.get('academic_year', '2025-2026'),
            description=data.get('description'),
            guidance_doc=doc_filename_str
        )
        db.session.add(new_batch)
        db.session.commit()
        
        from models import User, Notification
        from email_utils import send_notification_email
        from sqlalchemy import func
        users = User.query.filter(func.lower(User.role).in_(['student', 'lecturer'])).all()
        
        b_start_str = start_date.strftime('%d/%m/%Y') if start_date else 'Chưa công bố'
        b_submit_str = submission_deadline.strftime('%d/%m/%Y') if submission_deadline else 'Chưa công bố'
        b_end_str = end_date.strftime('%d/%m/%Y') if end_date else 'Chưa công bố'
        
        # Build compact timeline HTML for system notification
        notif_content = f"""
        <h5 style='color: #4f46e5; margin-bottom: 8px;'>Đợt NCKH: {new_batch.name}</h5>
        <div style='background: #f8f9fa; padding: 10px; border-radius: 6px; font-size: 13px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center;'>
            <span class='badge bg-primary'>{new_batch.type}</span>
            <span class='badge bg-secondary'>{new_batch.academic_year}</span>
            <span class='text-muted'><i class='fa-regular fa-calendar me-1'></i>{b_start_str}</span>
            <span class='text-muted'><i class='fa-solid fa-arrow-right'></i></span>
            <span class='text-danger fw-bold'><i class='fa-regular fa-calendar-xmark me-1'></i>{b_submit_str}</span>
        </div>
        """
        if new_batch.description:
            notif_content += f"<div style='margin-top: 15px;'><strong>Mô tả chi tiết:</strong><br>{new_batch.description}</div>"

        if doc_filename_str:
            # Join filenames with ||| for frontend parsing
            notif_content += "|||" + "|||".join(doc_filename_str.split('|'))
            
        for u in users:
            # Add to system notification
            notif = Notification(user_id=u.id, content=notif_content)
            db.session.add(notif)
            
        from flask import current_app
        import threading

        def send_emails_in_background(app, users_data, b_name, b_year, b_start, b_submit, b_end, b_desc, doc_paths):
            with app.app_context():
                for u_email, u_full_name in users_data:
                    if u_email:
                        html_body = f"""
                        <div style="font-family: Arial, sans-serif; padding: 20px;">
                            <h2 style="color: #4f46e5;">Thông báo Đợt NCKH Mới</h2>
                            <p>Xin chào {u_full_name},</p>
                            <p>Trường/Khoa vừa ban hành một đợt Nghiên cứu Khoa học mới trên hệ thống <strong>HOU S-RIMS</strong>. Chi tiết như sau:</p>
                            <table style="width: 100%; max-width: 600px; border-collapse: collapse; margin-top: 15px; margin-bottom: 20px;">
                                <tr>
                                    <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold; width: 35%;">Tên đợt:</td>
                                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{b_name}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Năm học áp dụng:</td>
                                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{b_year}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Ngày bắt đầu:</td>
                                    <td style="padding: 10px; border-bottom: 1px solid #eee; color: #0d6efd;">{b_start}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Hạn nộp đề tài:</td>
                                    <td style="padding: 10px; border-bottom: 1px solid #eee; color: #dc3545;">{b_submit}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Ngày kết thúc đợt:</td>
                                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{b_end}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold; vertical-align: top;">Mô tả chi tiết:</td>
                                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{b_desc}</td>
                                </tr>
                            </table>
                            <p>Vui lòng đăng nhập vào hệ thống HOU S-RIMS để xem chi tiết và đăng ký tham gia.</p>
                            <p style="color: #6c757d; font-size: 12px; margin-top: 30px;">Đây là email tự động từ hệ thống quản lý NCKH HOU S-RIMS. Vui lòng không trả lời email này.</p>
                        </div>
                        """
                        try:
                            send_notification_email(u_email, f"Thông báo: Mở {b_name}", f"Đợt {b_name} đã được mở.", html_body, doc_paths)
                        except Exception as e:
                            print(f"Failed to send email to {u_email}: {e}")

        # Prepare data for background thread
        users_data = [(u.email, u.full_name) for u in users if u.email]
        app = current_app._get_current_object()
        
        email_thread = threading.Thread(target=send_emails_in_background, args=(app, users_data, new_batch.name, new_batch.academic_year, b_start_str, b_submit_str, b_end_str, new_batch.description or '', doc_paths))
        email_thread.start()
                    
        db.session.commit()
        
        return jsonify({
            'message': 'Batch created successfully',
            'batch': {
                'id': new_batch.id,
                'name': new_batch.name,
                'type': new_batch.type,
                'status': new_batch.status
            }
        }), 201
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@batches_bp.route('', methods=['GET'])
def get_batches():
    """
    Get all batches
    ---
    tags:
      - Batches
    responses:
      200:
        description: List of all batches
    """
    batches = Batch.query.all()
    result = []
    for batch in batches:
        result.append({
            'id': batch.id,
            'name': batch.name,
            'start_date': batch.start_date.strftime('%Y-%m-%d'),
            'end_date': batch.end_date.strftime('%Y-%m-%d'),
            'status': batch.status
        })
    return jsonify(result), 200

@batches_bp.route('/<int:batch_id>', methods=['PUT'])
def update_batch(batch_id):
    batch = Batch.query.get_or_404(batch_id)
    data = request.form
    
    import os
    from werkzeug.utils import secure_filename
    
    if 'name' in data:
        name = (data.get('name') or '').strip()
        if not name or len(name) < 3:
            return jsonify({'error': 'Tên Đợt NCKH phải có ít nhất 3 ký tự!'}), 400
        batch.name = name

    new_start = batch.start_date
    new_end = batch.end_date
    new_sub = batch.submission_deadline

    if data.get('start_date'):
        try:
            new_start = datetime.strptime(data['start_date'], '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Định dạng Ngày bắt đầu không hợp lệ!'}), 400

    if data.get('end_date'):
        try:
            new_end = datetime.strptime(data['end_date'], '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Định dạng Ngày kết thúc không hợp lệ!'}), 400

    if data.get('submission_deadline'):
        try:
            new_sub = datetime.strptime(data['submission_deadline'], '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Định dạng Hạn nộp không hợp lệ!'}), 400

    if new_start and new_end and new_start > new_end:
        return jsonify({'error': 'Ngày bắt đầu không được lớn hơn ngày kết thúc đợt!'}), 400

    if new_sub and new_start and new_end and (new_sub < new_start or new_sub > new_end):
        return jsonify({'error': 'Hạn nộp báo cáo phải nằm trong khoảng từ Ngày bắt đầu đến Ngày kết thúc!'}), 400

    batch.start_date = new_start
    batch.end_date = new_end
    batch.submission_deadline = new_sub
    if data.get('status'):
        batch.status = data['status']
    if 'description' in data:
        batch.description = data['description']
    if data.get('academic_year'):
        batch.academic_year = data['academic_year']
    if data.get('type'):
        batch.type = data['type']
        
    files = request.files.getlist('guidance_doc')
    if files and any(f.filename for f in files):
        doc_filenames = []
        is_serverless = bool(os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME') or os.getenv('LAMBDA_TASK_ROOT'))
        if is_serverless:
            upload_dir = '/tmp/uploads/batches'
        else:
            upload_dir = os.path.join(request.environ.get('FLASK_APP_DIR', '.'), 'static', 'uploads', 'batches')
        try:
            os.makedirs(upload_dir, exist_ok=True)
        except Exception:
            pass
        for file in files:
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                doc_path = os.path.join(upload_dir, filename)
                file.save(doc_path)
                doc_filenames.append(filename)
        if doc_filenames:
            # Append or overwrite? Usually overwrite if they upload new files
            batch.guidance_doc = '|'.join(doc_filenames)
            
    db.session.commit()
    return jsonify({'message': 'Batch updated successfully'}), 200

def cascade_delete_batch_data(batch_id):
    """
    Xóa triệt để toàn bộ dữ liệu thuộc đợt NCKH:
    - Đề tài (Topic), bài nộp (Submission), cột mốc (Milestone), tiến trình (Progress), lịch họp (Meeting)
    - Nhóm nghiên cứu (Group), thành viên nhóm (GroupMember), tin nhắn nội bộ (Message), lời mời (invitations)
    - Hội đồng chấm điểm (Council), thành viên HĐ (CouncilMember), điểm đánh giá (Evaluation)
    - Giải phóng các slot lịch hẹn (AvailabilitySlot)
    """
    from models import (
        Council, CouncilMember, Topic, Group, GroupMember,
        Message, Submission, Milestone, Progress, Meeting,
        TopicRegistration, Evaluation, AvailabilitySlot
    )
    
    # 1. Lấy danh sách đề tài và nhóm thuộc đợt
    topics = Topic.query.filter_by(batch_id=batch_id).all()
    topic_ids = [t.id for t in topics]
    
    groups = Group.query.filter_by(batch_id=batch_id).all()
    group_ids = [g.id for g in groups]
    for t in topics:
        if t.group_id and t.group_id not in group_ids:
            group_ids.append(t.group_id)

    # 2. Xóa các Hội đồng và điểm đánh giá
    councils = Council.query.filter_by(batch_id=batch_id).all()
    council_ids = [c.id for c in councils]
    
    if topic_ids:
        Evaluation.query.filter(Evaluation.topic_id.in_(topic_ids)).delete(synchronize_session=False)
    if council_ids:
        Evaluation.query.filter(Evaluation.council_id.in_(council_ids)).delete(synchronize_session=False)
        CouncilMember.query.filter(CouncilMember.council_id.in_(council_ids)).delete(synchronize_session=False)
        for c in councils:
            db.session.delete(c)

    # 3. Xóa dữ liệu của các đề tài: bài nộp, cột mốc, tiến trình, lịch họp, đăng ký
    if topic_ids:
        Submission.query.filter(Submission.topic_id.in_(topic_ids)).delete(synchronize_session=False)
        
        milestones = Milestone.query.filter(Milestone.topic_id.in_(topic_ids)).all()
        milestone_ids = [m.id for m in milestones]
        if milestone_ids:
            Progress.query.filter(Progress.milestone_id.in_(milestone_ids)).delete(synchronize_session=False)
            Milestone.query.filter(Milestone.id.in_(milestone_ids)).delete(synchronize_session=False)
            
        meetings = Meeting.query.filter(Meeting.topic_id.in_(topic_ids)).all()
        meeting_ids = [m.id for m in meetings]
        if meeting_ids:
            AvailabilitySlot.query.filter(AvailabilitySlot.meeting_id.in_(meeting_ids)).update({
                'meeting_id': None,
                'status': 'open',
                'group_id': None,
                'booked_by_id': None,
                'booked_at': None
            }, synchronize_session=False)
            Meeting.query.filter(Meeting.id.in_(meeting_ids)).delete(synchronize_session=False)
            
        TopicRegistration.query.filter(TopicRegistration.topic_id.in_(topic_ids)).delete(synchronize_session=False)

    if group_ids:
        TopicRegistration.query.filter(TopicRegistration.group_id.in_(group_ids)).delete(synchronize_session=False)

    # 4. Xóa đề tài trước (vì bảng topics có foreign key constraint topics_group_id_fkey trỏ vào groups)
    if topic_ids:
        Topic.query.filter(Topic.id.in_(topic_ids)).delete(synchronize_session=False)

    # 5. Xóa dữ liệu của các nhóm: slot hẹn, tin nhắn, lời mời, thành viên, nhóm
    if group_ids:
        AvailabilitySlot.query.filter(AvailabilitySlot.group_id.in_(group_ids)).update({
            'status': 'open',
            'group_id': None,
            'booked_by_id': None,
            'booked_at': None,
            'meeting_id': None
        }, synchronize_session=False)
        
        Message.query.filter(Message.group_id.in_(group_ids)).delete(synchronize_session=False)
        
        for g_id in group_ids:
            invitations = Message.query.filter(
                Message.message_type == 'invitation',
                Message.meta_data.isnot(None)
            ).all()
            for inv in invitations:
                if f'"group_id": {g_id}' in inv.meta_data or f'"group_id":{g_id}' in inv.meta_data:
                    db.session.delete(inv)
                    
        GroupMember.query.filter(GroupMember.group_id.in_(group_ids)).delete(synchronize_session=False)
        Group.query.filter(Group.id.in_(group_ids)).delete(synchronize_session=False)


@batches_bp.route('/<int:batch_id>', methods=['DELETE'])
def delete_batch(batch_id):
    batch = Batch.query.get_or_404(batch_id)
    try:
        batch_name = batch.name
        # Soft delete: Chỉ ẩn đợt đi, không xóa dữ liệu trong CSDL để lưu trữ và truy xuất khi cần
        batch.status = 'hidden'
        db.session.commit()
        return jsonify({'message': f'Đã ẩn đợt NCKH "{batch_name}" thành công! Dữ liệu được bảo lưu an toàn trong hệ thống.', 'deleted_id': batch_id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Không thể ẩn đợt NCKH này do có lỗi: {str(e)}'}), 500
