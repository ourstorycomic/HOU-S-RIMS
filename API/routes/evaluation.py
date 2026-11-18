from flask import Blueprint, request, jsonify, session
from models import db, Council, Rubric, Evaluation, Topic, User, Notification, GroupMember, CouncilMember, Batch
import json
import os
from datetime import datetime
from werkzeug.utils import secure_filename

evaluation_bp = Blueprint('evaluation_api', __name__, url_prefix='/api')

@evaluation_bp.route('/councils', methods=['POST'])
def create_council():
    """
    Create a new council with strict validations
    """
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'Vui lòng nhập Tên Hội đồng!'}), 400
    if len(name) < 5:
        return jsonify({'error': 'Tên Hội đồng phải có ít nhất 5 ký tự!'}), 400
        
    batch_id = data.get('batch_id')
    if not batch_id:
        return jsonify({'error': 'Vui lòng chọn đợt NCKH hợp lệ!'}), 400
        
    batch = Batch.query.get(batch_id)
    if not batch:
        return jsonify({'error': 'Đợt NCKH không tồn tại!'}), 404

    # 1. Validate Ngày họp & Giờ họp
    meeting_date_str = data.get('meeting_date')
    if not meeting_date_str:
        return jsonify({'error': 'Vui lòng chọn ngày họp của Hội đồng!'}), 400
    try:
        meeting_date = datetime.strptime(meeting_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Định dạng ngày họp không hợp lệ (YYYY-MM-DD)!'}), 400

    meeting_time = None
    if data.get('meeting_time'):
        try:
            meeting_time = datetime.strptime(data['meeting_time'], '%H:%M').time()
        except ValueError:
            return jsonify({'error': 'Định dạng giờ họp không hợp lệ (HH:MM)!'}), 400

    # 2. Validate Gom nhóm đề tài (BẮT BUỘC PHẢI CÓ ÍT NHẤT 1 NHÓM)
    raw_topics = data.get('topics') or []
    if not raw_topics or len(raw_topics) == 0:
        return jsonify({'error': 'Hội đồng nghiệm thu bắt buộc phải có ít nhất 1 nhóm đề tài báo cáo! Vui lòng chọn nhóm đề tài.'}), 400

    topic_ids = [t.get('id') if isinstance(t, dict) else t for t in raw_topics]
    valid_topics = Topic.query.filter(Topic.id.in_(topic_ids)).all()
    if len(valid_topics) == 0:
        return jsonify({'error': 'Không tìm thấy đề tài hợp lệ nào trong danh sách được chọn!'}), 400

    # 3. Validate Thành phần Hội đồng
    presidents = [int(x) for x in (data.get('president') or []) if str(x).isdigit()]
    secretaries = [int(x) for x in (data.get('secretary') or []) if str(x).isdigit()]
    members = [int(x) for x in (data.get('members') or []) if str(x).isdigit()]

    if len(presidents) == 0:
        return jsonify({'error': 'Hội đồng bắt buộc phải có 1 Chủ tịch Hội đồng!'}), 400
    if len(presidents) > 1:
        return jsonify({'error': 'Hội đồng chỉ được có duy nhất 1 Chủ tịch!'}), 400

    if len(secretaries) == 0:
        return jsonify({'error': 'Hội đồng bắt buộc phải có 1 Thư ký Hội đồng!'}), 400
    if len(secretaries) > 1:
        return jsonify({'error': 'Hội đồng chỉ được có duy nhất 1 Thư ký!'}), 400

    # Kiểm tra trùng lặp giảng viên trong hội đồng (1 GV không được giữ 2 vai trò)
    all_lecturer_ids = presidents + secretaries + members
    if len(all_lecturer_ids) != len(set(all_lecturer_ids)):
        seen = set()
        duplicates = set()
        for lid in all_lecturer_ids:
            if lid in seen:
                duplicates.add(lid)
            seen.add(lid)
        dup_names = [u.full_name for u in User.query.filter(User.id.in_(duplicates)).all()]
        return jsonify({'error': f'Mỗi giảng viên chỉ được đảm nhiệm một vai trò trong Hội đồng! Giảng viên sau đang bị gán trùng: {", ".join(dup_names)}'}), 400

    # 4. Kiểm tra Giảng viên hướng dẫn không được ngồi Hội đồng nghiệm thu đề tài của mình
    mentor_conflicts = []
    for topic in valid_topics:
        if topic.mentor_id and topic.mentor_id in all_lecturer_ids:
            mentor_user = User.query.get(topic.mentor_id)
            m_name = mentor_user.full_name if mentor_user else f"ID {topic.mentor_id}"
            mentor_conflicts.append(f"{m_name} (là GVHD của đề tài '{topic.title}')")
    if mentor_conflicts:
        return jsonify({'error': f'Theo quy chế NCKH, Giảng viên hướng dẫn không được tham gia Hội đồng nghiệm thu đề tài do chính mình hướng dẫn: {"; ".join(mentor_conflicts)}'}), 400

    # 5. Check if lecturers are already in another council for this batch
    existing_members = CouncilMember.query.join(Council).filter(
        Council.batch_id == batch_id,
        CouncilMember.mentor_id.in_(all_lecturer_ids)
    ).all()
    if existing_members:
        conflict_users = list(set([User.query.get(m.mentor_id).full_name for m in existing_members if User.query.get(m.mentor_id)]))
        return jsonify({'error': f'Các giảng viên sau đã được phân công vào hội đồng khác trong đợt này: {", ".join(conflict_users)}'}), 400

    try:
        new_council = Council(
            name=name,
            decision_number=data.get('decision_number'),
            meeting_date=meeting_date,
            meeting_time=meeting_time,
            location=data.get('location'),
            batch_id=batch_id
        )
        db.session.add(new_council)
        db.session.flush()

        from email_utils import send_notification_email
        lecturers_to_notify = set()

        for p_id in presidents:
            db.session.add(CouncilMember(council_id=new_council.id, mentor_id=p_id, role='president'))
            lecturers_to_notify.add(p_id)

        for s_id in secretaries:
            db.session.add(CouncilMember(council_id=new_council.id, mentor_id=s_id, role='secretary'))
            lecturers_to_notify.add(s_id)

        for m_id in members:
            db.session.add(CouncilMember(council_id=new_council.id, mentor_id=m_id, role='member'))
            lecturers_to_notify.add(m_id)

        # Assign topics
        students_to_notify = set()
        for t_item in raw_topics:
            t_id = t_item.get('id') if isinstance(t_item, dict) else t_item
            t_time = t_item.get('time') if isinstance(t_item, dict) else None
            topic = Topic.query.get(t_id)
            if topic:
                topic.council_id = new_council.id
                topic.presentation_time = t_time
                if topic.group_id:
                    group_members = GroupMember.query.filter_by(group_id=topic.group_id, status='accepted').all()
                    for gm in group_members:
                        students_to_notify.add(gm.student_id)

        db.session.commit()

        # Notifications logic
        date_str = meeting_date.strftime('%d/%m/%Y') if meeting_date else 'chưa xác định'
        time_str = meeting_time.strftime('%H:%M') if meeting_time else 'chưa xác định'
        location_str = data.get('location') or 'chưa xác định'

        for l_id in lecturers_to_notify:
            lecturer = User.query.get(l_id)
            if lecturer:
                notif_content = f"Bạn đã được thêm vào {new_council.name}. Thời gian: {time_str} ngày {date_str}, Địa điểm: {location_str}"
                db.session.add(Notification(user_id=lecturer.id, content=notif_content))
                try:
                    send_notification_email(
                        to_email=lecturer.email,
                        subject="[HOU S-RIMS] Lời mời tham gia Hội đồng",
                        content=f"Xin chào {lecturer.full_name},\n\n{notif_content}\n\nTrân trọng,\nHOU S-RIMS"
                    )
                except Exception as e: print(e)

        for s_id in students_to_notify:
            student = User.query.get(s_id)
            if student:
                # Task 2.5: Ẩn giờ báo cáo chi tiết đối với sinh viên nếu chưa công bố chính thức
                notif_content = f"Nhóm của bạn đã được sắp xếp báo cáo trước {new_council.name}. Hạn báo cáo: ngày {date_str}, Địa điểm: {location_str}. (Lịch giờ cụ thể sẽ được cập nhật trước phiên họp)."
                db.session.add(Notification(user_id=student.id, content=notif_content))
                try:
                    send_notification_email(
                        to_email=student.email,
                        subject="[HOU S-RIMS] Lịch báo cáo Hội đồng",
                        content=f"Xin chào {student.full_name},\n\n{notif_content}\n\nTrân trọng,\nHOU S-RIMS"
                    )
                except Exception as e: print(e)

        db.session.commit()
        return jsonify({'message': 'Council created', 'id': new_council.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@evaluation_bp.route('/councils/<int:council_id>', methods=['DELETE'])
def delete_council(council_id):
    try:
        council = Council.query.get_or_404(council_id)
        
        # Free topics
        Topic.query.filter_by(council_id=council.id).update({'council_id': None, 'presentation_time': None})
        
        # Notify lecturers before deletion
        from email_utils import send_notification_email
        members = CouncilMember.query.filter_by(council_id=council.id).all()
        for m in members:
            lecturer = User.query.get(m.mentor_id)
            if lecturer:
                msg = f"Hội đồng '{council.name}' đã bị hủy bỏ."
                db.session.add(Notification(user_id=lecturer.id, content=msg))
                try:
                    send_notification_email(lecturer.email, "[HOU S-RIMS] Hủy Hội đồng", msg)
                except:
                    pass
        
        # Delete CouncilMembers and Council
        CouncilMember.query.filter_by(council_id=council.id).delete()
        Evaluation.query.filter_by(council_id=council.id).delete()
        db.session.delete(council)
        db.session.commit()
        return jsonify({'message': 'Deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@evaluation_bp.route('/councils/<int:council_id>', methods=['PUT'])
def update_council(council_id):
    from email_utils import send_notification_email
    
    data = request.json or {}
    try:
        council = Council.query.get_or_404(council_id)
        
        if 'name' in data:
            name = (data.get('name') or '').strip()
            if not name or len(name) < 5:
                return jsonify({'error': 'Tên Hội đồng phải có ít nhất 5 ký tự!'}), 400
            council.name = name

        if 'decision_number' in data:
            council.decision_number = data.get('decision_number')
        if 'location' in data:
            council.location = data.get('location')
        
        if data.get('meeting_date'):
            try:
                council.meeting_date = datetime.strptime(data['meeting_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Định dạng ngày họp không hợp lệ (YYYY-MM-DD)!'}), 400

        if data.get('meeting_time'):
            try:
                council.meeting_time = datetime.strptime(data['meeting_time'], '%H:%M').time()
            except ValueError:
                return jsonify({'error': 'Định dạng giờ họp không hợp lệ (HH:MM)!'}), 400

        # Validate topics if provided
        raw_topics = data.get('topics')
        if raw_topics is not None:
            if len(raw_topics) == 0:
                return jsonify({'error': 'Hội đồng nghiệm thu bắt buộc phải có ít nhất 1 nhóm đề tài báo cáo!'}), 400

        # Update members if provided
        if any(k in data for k in ['president', 'secretary', 'members']):
            presidents = [int(x) for x in (data.get('president') or []) if str(x).isdigit()]
            secretaries = [int(x) for x in (data.get('secretary') or []) if str(x).isdigit()]
            members = [int(x) for x in (data.get('members') or []) if str(x).isdigit()]

            if len(presidents) == 0:
                return jsonify({'error': 'Hội đồng bắt buộc phải có 1 Chủ tịch Hội đồng!'}), 400
            if len(presidents) > 1:
                return jsonify({'error': 'Hội đồng chỉ được có duy nhất 1 Chủ tịch!'}), 400

            if len(secretaries) == 0:
                return jsonify({'error': 'Hội đồng bắt buộc phải có 1 Thư ký Hội đồng!'}), 400
            if len(secretaries) > 1:
                return jsonify({'error': 'Hội đồng chỉ được có duy nhất 1 Thư ký!'}), 400

            all_lecturer_ids = presidents + secretaries + members
            if len(all_lecturer_ids) != len(set(all_lecturer_ids)):
                seen = set()
                duplicates = set()
                for lid in all_lecturer_ids:
                    if lid in seen:
                        duplicates.add(lid)
                    seen.add(lid)
                dup_names = [u.full_name for u in User.query.filter(User.id.in_(duplicates)).all()]
                return jsonify({'error': f'Mỗi giảng viên chỉ được đảm nhiệm một vai trò trong Hội đồng! Giảng viên sau đang bị gán trùng: {", ".join(dup_names)}'}), 400

            # Check mentor conflict
            assigned_topics = Topic.query.filter_by(council_id=council.id).all() if raw_topics is None else [Topic.query.get(t.get('id') if isinstance(t, dict) else t) for t in raw_topics if Topic.query.get(t.get('id') if isinstance(t, dict) else t)]
            mentor_conflicts = []
            for t in assigned_topics:
                if t and t.mentor_id and t.mentor_id in all_lecturer_ids:
                    mentor_user = User.query.get(t.mentor_id)
                    m_name = mentor_user.full_name if mentor_user else f"ID {t.mentor_id}"
                    mentor_conflicts.append(f"{m_name} (là GVHD của đề tài: {t.title})")
            if mentor_conflicts:
                return jsonify({'error': f'Theo quy chế NCKH, Giảng viên hướng dẫn không được tham gia Hội đồng nghiệm thu đề tài do chính mình hướng dẫn: {"; ".join(mentor_conflicts)}'}), 400

            # Check conflict with other councils in same batch
            existing_members = CouncilMember.query.join(Council).filter(
                Council.batch_id == council.batch_id,
                Council.id != council.id,
                CouncilMember.mentor_id.in_(all_lecturer_ids)
            ).all()
            if existing_members:
                conflict_users = list(set([User.query.get(m.mentor_id).full_name for m in existing_members if User.query.get(m.mentor_id)]))
                return jsonify({'error': f'Các giảng viên sau đã được phân công vào hội đồng khác trong đợt này: {", ".join(conflict_users)}'}), 400

            CouncilMember.query.filter_by(council_id=council.id).delete()
            for p_id in presidents:
                db.session.add(CouncilMember(council_id=council.id, mentor_id=p_id, role='president'))
            for s_id in secretaries:
                db.session.add(CouncilMember(council_id=council.id, mentor_id=s_id, role='secretary'))
            for m_id in members:
                db.session.add(CouncilMember(council_id=council.id, mentor_id=m_id, role='member'))

        # Update topics
        if raw_topics is not None:
            Topic.query.filter_by(council_id=council.id).update({'council_id': None, 'presentation_time': None})
            for t_item in raw_topics:
                t_id = t_item.get('id') if isinstance(t_item, dict) else t_item
                t_time = t_item.get('time') if isinstance(t_item, dict) else None
                topic = Topic.query.get(t_id)
                if topic:
                    topic.council_id = council.id
                    topic.presentation_time = t_time

        # Notify lecturers
        members = CouncilMember.query.filter_by(council_id=council.id).all()
        for m in members:
            lecturer = User.query.get(m.mentor_id)
            if lecturer:
                msg = f"Thông tin hội đồng '{council.name}' đã được cập nhật."
                db.session.add(Notification(user_id=lecturer.id, content=msg))
                try:
                    send_notification_email(lecturer.email, "[HOU S-RIMS] Cập nhật Hội đồng", msg)
                except:
                    pass

        db.session.commit()
        return jsonify({'message': 'Updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# =========================================================================
# CHỨC NĂNG UPLOAD BIÊN BẢN CỨNG (PDF/JPG) CHO TỪNG HỘI ĐỒNG
# =========================================================================
@evaluation_bp.route('/councils/<int:council_id>/upload-minutes', methods=['POST'])
def upload_council_minutes(council_id):
    """
    Xây dựng API upload file scan biên bản (PDF/JPG/PNG) lưu vào từng hội đồng
    """
    council = Council.query.get_or_404(council_id)
    if 'file' not in request.files:
        return jsonify({'error': 'Không tìm thấy file tải lên!'}), 400
        
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'Tên file không hợp lệ!'}), 400
        
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ['.pdf', '.jpg', '.jpeg', '.png']:
        return jsonify({'error': 'Chỉ chấp nhận file scan định dạng PDF, JPG hoặc PNG!'}), 400
        
    is_serverless = bool(os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME') or os.getenv('LAMBDA_TASK_ROOT'))
    if is_serverless:
        upload_dir = '/tmp/uploads/councils/minutes'
    else:
        upload_dir = os.path.join(request.environ.get('FLASK_APP_DIR', '.'), 'static', 'uploads', 'councils', 'minutes')
    try:
        os.makedirs(upload_dir, exist_ok=True)
    except Exception:
        pass
    
    unique_name = f"bienban_hd_{council.id}_{int(datetime.utcnow().timestamp())}{ext}"
    save_path = os.path.join(upload_dir, unique_name)
    file.save(save_path)
    
    relative_path = f"uploads/councils/minutes/{unique_name}"
    council.minute_file_url = relative_path
    db.session.commit()

    # Task 2.6: Gửi file kết quả sau khi họp Hội đồng (Tự động kèm link tải vào thông báo/email cho SV & GV)
    try:
        from email_utils import send_notification_email
        minute_full_link = f"/static/{relative_path}"
        base_host = request.host_url.rstrip('/')
        
        # 1. Gửi cho các thành viên trong Hội đồng (Giảng viên)
        council_members = CouncilMember.query.filter_by(council_id=council.id).all()
        for cm in council_members:
            lecturer = User.query.get(cm.mentor_id)
            if lecturer:
                notif_msg = (
                    f"Biên bản nghiệm thu Hội đồng <strong>{council.name}</strong> đã được tải lên thành công. "
                    f"<a href='{minute_full_link}' target='_blank' class='btn btn-xs btn-outline-primary ms-1'>Xem/Tải file</a>"
                )
                db.session.add(Notification(user_id=lecturer.id, content=notif_msg))
                if lecturer.email:
                    send_notification_email(
                        to_email=lecturer.email,
                        subject=f"[HOU S-RIMS] Biên bản nghiệm thu {council.name}",
                        content=f"Xin chào Thầy/Cô {lecturer.full_name},\n\nBiên bản họp Hội đồng '{council.name}' đã được tải lên chính thức.\nBạn có thể xem và tải file biên bản tại liên kết:\n{base_host}{minute_full_link}\n\nTrân trọng,\nHOU S-RIMS"
                    )

        # 2. Gửi cho sinh viên các nhóm đề tài và GVHD của đề tài
        c_topics = Topic.query.filter_by(council_id=council.id).all()
        notified_student_ids = set()
        for top in c_topics:
            if top.mentor_id:
                mentor_user = User.query.get(top.mentor_id)
                if mentor_user and mentor_user.id not in [cm.mentor_id for cm in council_members]:
                    notif_msg = (
                        f"Hội đồng <strong>{council.name}</strong> đã tải lên biên bản nghiệm thu cho đề tài <em>'{top.title}'</em>. "
                        f"<a href='{minute_full_link}' target='_blank' class='btn btn-xs btn-outline-primary ms-1'>Xem/Tải file</a>"
                    )
                    db.session.add(Notification(user_id=mentor_user.id, content=notif_msg))
            
            if top.group_id:
                gms = GroupMember.query.filter_by(group_id=top.group_id).all()
                for gm in gms:
                    if gm.student_id not in notified_student_ids:
                        notified_student_ids.add(gm.student_id)
                        st_user = User.query.get(gm.student_id)
                        if st_user:
                            notif_msg = (
                                f"Hội đồng <strong>{council.name}</strong> đã tải lên Biên bản nghiệm thu đề tài NCKH. "
                                f"<a href='{minute_full_link}' target='_blank' class='btn btn-xs btn-outline-success ms-1'>Xem/Tải biên bản</a>"
                            )
                            db.session.add(Notification(user_id=st_user.id, content=notif_msg))
                            if st_user.email:
                                send_notification_email(
                                    to_email=st_user.email,
                                    subject=f"[HOU S-RIMS] Biên bản họp Hội đồng - Đề tài: {top.title}",
                                    content=f"Xin chào {st_user.full_name},\n\nHội đồng '{council.name}' đã tải lên Biên bản nghiệm thu cho đề tài '{top.title}'.\nBạn có thể xem và tải file tại:\n{base_host}{minute_full_link}\n\nTrân trọng,\nHOU S-RIMS"
                                )
        db.session.commit()
    except Exception as notif_err:
        print(f"Error sending minute notifications: {notif_err}")
    
    return jsonify({
        'message': 'Đã tải lên biên bản cứng và gửi thông báo kết quả thành công!',
        'minute_file_url': relative_path,
        'filename': unique_name
    }), 200

# =========================================================================
# CHỨC NĂNG CẬP NHẬT TRẠNG THÁI ĐẠT/KHÔNG ĐẠT CHO ĐỀ TÀI TRONG HỘI ĐỒNG
# =========================================================================
@evaluation_bp.route('/councils/<int:council_id>/topics/<int:topic_id>/result', methods=['POST'])
def update_topic_result(council_id, topic_id):
    """
    Cập nhật trạng thái Đạt / Không đạt và điểm tổng kết của đề tài sau khi bảo vệ
    """
    council = Council.query.get_or_404(council_id)
    topic = Topic.query.get_or_404(topic_id)
    
    if topic.council_id != council.id:
        return jsonify({'error': 'Đề tài không thuộc hội đồng này!'}), 400
        
    data = request.get_json() or {}
    status = data.get('defense_status') # 'passed', 'failed', 'pending'
    if status not in ['passed', 'failed', 'pending']:
        return jsonify({'error': 'Trạng thái kết quả không hợp lệ (phải là Đạt hoặc Không đạt)!'}), 400
        
    topic.defense_status = status
    if 'defense_score' in data and data['defense_score'] is not None and data['defense_score'] != '':
        try:
            topic.defense_score = round(float(data['defense_score']), 2)
        except ValueError:
            pass
            
    # Thông báo tới sinh viên trong nhóm
    if topic.group_id:
        group_members = GroupMember.query.filter_by(group_id=topic.group_id).all()
        status_vi = "ĐẠT" if status == 'passed' else ("KHÔNG ĐẠT" if status == 'failed' else "Đang cập nhật")
        msg = f"Hội đồng '{council.name}' đã công bố kết quả nghiệm thu đề tài '{topic.title}': {status_vi} (Điểm: {topic.defense_score or 'N/A'})."
        for gm in group_members:
            db.session.add(Notification(user_id=gm.student_id, content=msg))
            
    db.session.commit()
    return jsonify({
        'message': f'Đã cập nhật kết quả: {"ĐẠT" if status=="passed" else "KHÔNG ĐẠT"} thành công!',
        'defense_status': topic.defense_status,
        'defense_score': topic.defense_score
    }), 200

# =========================================================================
# QUẢN LÝ RUBRIC CHẤM ĐIỂM
# =========================================================================
@evaluation_bp.route('/rubrics', methods=['GET'])
def get_rubrics():
    """Lấy danh sách các cấu hình rubric"""
    rubrics = Rubric.query.all()
    results = []
    for r in rubrics:
        try:
            crit = json.loads(r.criteria_json) if isinstance(r.criteria_json, str) else r.criteria_json
        except:
            crit = []
        results.append({
            'id': r.id,
            'name': r.name,
            'total_score': r.total_score,
            'criteria': crit
        })
    return jsonify({'rubrics': results}), 200

@evaluation_bp.route('/rubrics', methods=['POST', 'PUT'])
def manage_rubrics():
    data = request.get_json() or {}
    if not data or 'name' not in data or 'criteria_json' not in data or 'total_score' not in data:
        return jsonify({'error': 'Thiếu các trường thông tin bắt buộc!'}), 400
        
    try:
        rubric_id = data.get('id')
        rubric = Rubric.query.get(rubric_id) if rubric_id else None
        
        crit_str = json.dumps(data['criteria_json'], ensure_ascii=False) if not isinstance(data['criteria_json'], str) else data['criteria_json']
        
        if rubric:
            rubric.name = data['name']
            rubric.criteria_json = crit_str
            rubric.total_score = float(data['total_score'])
            msg = 'Đã cập nhật Rubric thành công!'
        else:
            rubric = Rubric(
                name=data['name'],
                criteria_json=crit_str,
                total_score=float(data['total_score'])
            )
            db.session.add(rubric)
            msg = 'Đã tạo Rubric tiêu chí mới thành công!'
            
        db.session.commit()
        return jsonify({'message': msg, 'id': rubric.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# =========================================================================
# FORM NHẬP ĐIỂM ĐỘC LẬP CHO TỪNG THÀNH VIÊN HỘI ĐỒNG (RUBRIC GRADING)
# =========================================================================
@evaluation_bp.route('/councils/<int:council_id>/topics/<int:topic_id>/grade', methods=['POST'])
def grade_topic(council_id, topic_id):
    """
    Thành viên hội đồng nhập điểm độc lập theo từng tiêu chí trong Rubric
    """
    current_user_id = session.get('user_id')
    if not current_user_id:
        return jsonify({'error': 'Vui lòng đăng nhập để chấm điểm!'}), 401
        
    council = Council.query.get_or_404(council_id)
    topic = Topic.query.get_or_404(topic_id)
    
    # Kiểm tra giảng viên có thuộc hội đồng này không
    membership = CouncilMember.query.filter_by(council_id=council.id, mentor_id=current_user_id).first()
    if not membership and session.get('role') != 'faculty':
        return jsonify({'error': 'Bạn không phải là thành viên của Hội đồng này!'}), 403
        
    data = request.get_json() or {}
    rubric_id = data.get('rubric_id') or 1
    rubric = Rubric.query.get(rubric_id)
    if not rubric:
        rubric = Rubric.query.first()
        if not rubric:
            return jsonify({'error': 'Chưa cấu hình Rubric chấm điểm trong hệ thống!'}), 400
            
    criteria_scores = data.get('criteria_scores') or {} # dict: { "1": 1.8, "2": 2.7, ... }
    total_score = data.get('total_score')
    
    if total_score is None:
        try:
            total_score = sum(float(v) for v in criteria_scores.values())
        except:
            total_score = 0.0
            
    comments = data.get('comments', '')
    
    # Tìm xem giảng viên đã chấm đề tài này chưa, nếu có thì update, chưa thì tạo mới
    evaluation = Evaluation.query.filter_by(
        council_id=council.id,
        topic_id=topic.id,
        evaluator_id=current_user_id
    ).first()
    
    if evaluation:
        evaluation.rubric_id = rubric.id
        evaluation.score = round(float(total_score), 2)
        evaluation.criteria_scores = json.dumps(criteria_scores, ensure_ascii=False)
        evaluation.comments = comments
    else:
        evaluation = Evaluation(
            council_id=council.id,
            topic_id=topic.id,
            evaluator_id=current_user_id,
            rubric_id=rubric.id,
            score=round(float(total_score), 2),
            criteria_scores=json.dumps(criteria_scores, ensure_ascii=False),
            comments=comments
        )
        db.session.add(evaluation)
        
    db.session.commit()
    
    # Tự động tính điểm trung bình của tất cả thành viên đã chấm trong hội đồng
    all_evals = Evaluation.query.filter_by(council_id=council.id, topic_id=topic.id).all()
    if all_evals:
        avg_score = round(sum(e.score for e in all_evals) / len(all_evals), 2)
        topic.defense_score = avg_score
        # Nếu đạt từ 5.0 trở lên thì mặc định đạt, có thể để Chủ tịch chốt
        if avg_score >= 5.0 and topic.defense_status == 'pending':
            topic.defense_status = 'passed'
        db.session.commit()
        
    return jsonify({
        'message': 'Đã lưu phiếu chấm điểm độc lập thành công!',
        'score': evaluation.score,
        'avg_score': topic.defense_score,
        'defense_status': topic.defense_status
    }), 200

@evaluation_bp.route('/councils/<int:council_id>/topics/<int:topic_id>/evaluations', methods=['GET'])
def get_topic_evaluations(council_id, topic_id):
    """
    Lấy danh sách tất cả các phiếu chấm của các thành viên trong Hội đồng cho đề tài
    """
    evals = Evaluation.query.filter_by(council_id=council_id, topic_id=topic_id).all()
    results = []
    for e in evals:
        evaluator = User.query.get(e.evaluator_id) if e.evaluator_id else None
        crit_scores = {}
        try:
            crit_scores = json.loads(e.criteria_scores) if e.criteria_scores else {}
        except:
            pass
        results.append({
            'id': e.id,
            'evaluator_id': e.evaluator_id,
            'evaluator_name': evaluator.full_name if evaluator else 'Thành viên HĐ',
            'score': e.score,
            'criteria_scores': crit_scores,
            'comments': e.comments or ''
        })
    return jsonify({'evaluations': results}), 200


# =========================================================================
# TASK 2.4: UPLOAD QUYẾT ĐỊNH THÀNH LẬP HỘI ĐỒNG
# =========================================================================
@evaluation_bp.route('/councils/<int:council_id>/upload-decision', methods=['POST'])
def upload_council_decision(council_id):
    """
    API upload file Quyết định thành lập Hội đồng (PDF/JPG/PNG) lưu trữ và cập nhật decision_file_url
    """
    council = Council.query.get_or_404(council_id)
    if 'file' not in request.files:
        return jsonify({'error': 'Không tìm thấy file tải lên!'}), 400
        
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'Tên file không hợp lệ!'}), 400
        
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ['.pdf', '.jpg', '.jpeg', '.png']:
        return jsonify({'error': 'Chỉ chấp nhận file scan định dạng PDF, JPG hoặc PNG!'}), 400
        
    is_serverless = bool(os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME') or os.getenv('LAMBDA_TASK_ROOT'))
    if is_serverless:
        upload_dir = '/tmp/uploads/councils/decisions'
    else:
        upload_dir = os.path.join(request.environ.get('FLASK_APP_DIR', '.'), 'static', 'uploads', 'councils', 'decisions')
    try:
        os.makedirs(upload_dir, exist_ok=True)
    except Exception:
        pass
    
    unique_name = f"quyetdinh_hd_{council.id}_{int(datetime.utcnow().timestamp())}{ext}"
    save_path = os.path.join(upload_dir, unique_name)
    file.save(save_path)
    
    relative_path = f"uploads/councils/decisions/{unique_name}"
    council.decision_file_url = relative_path
    db.session.commit()
    
    return jsonify({
        'message': 'Đã tải lên Quyết định thành lập Hội đồng thành công!',
        'decision_file_url': relative_path,
        'filename': unique_name
    }), 200


# =========================================================================
# TASK 2.1: THUẬT TOÁN TỰ ĐỘNG TÍNH & CHIA ĐỀ TÀI VÀO HỘI ĐỒNG
# =========================================================================
@evaluation_bp.route('/councils/auto-group-topics', methods=['POST'])
def auto_group_topics():
    """
    Thuật toán tự động tính toán và chia đề tài vào các Hội đồng:
    1. Gom nhóm đề tài theo Hướng nghiên cứu / Chuyên môn
    2. Tối đa X đề tài/Hội đồng (cân đối thời lượng báo cáo)
    3. Loại trừ hoàn toàn GVHD của các đề tài khỏi Hội đồng đó
    4. Ưu tiên chọn Giảng viên có chuyên môn phù hợp với đề tài
    5. Cân bằng tải trọng giữa các giảng viên trong khoa
    """
    from sqlalchemy import func
    data = request.get_json(silent=True) or {}
    batch_id = data.get('batch_id')
    max_per_council = int(data.get('max_topics_per_council') or 5)
    max_per_council = max(2, min(max_per_council, 10))
    apply_changes = bool(data.get('apply', False))
    meeting_date_str = data.get('meeting_date')

    if not batch_id:
        active_batch = Batch.query.filter_by(status='active').order_by(Batch.id.desc()).first()
        if not active_batch:
            active_batch = Batch.query.order_by(Batch.id.desc()).first()
        batch_id = active_batch.id if active_batch else None

    if not batch_id:
        return jsonify({'error': 'Không tìm thấy đợt NCKH phù hợp!'}), 400

    # Lấy các đề tài trong đợt chưa được phân vào Hội đồng
    unassigned_topics = Topic.query.filter(
        Topic.batch_id == batch_id,
        Topic.council_id.is_(None)
    ).all()

    if not unassigned_topics:
        return jsonify({'error': 'Tất cả các đề tài trong đợt này đã được phân công vào Hội đồng!'}), 400

    all_lecturers = User.query.filter(func.lower(User.role) == 'lecturer').all()
    if len(all_lecturers) < 3:
        return jsonify({'error': 'Cần ít nhất 3 giảng viên trong hệ thống để thành lập Hội đồng!'}), 400

    # Gom nhóm đề tài theo Hướng nghiên cứu (field)
    field_groups = {}
    for t in unassigned_topics:
        f = (t.field or 'Công nghệ thông tin & Ứng dụng').strip()
        field_groups.setdefault(f, []).append(t)

    suggested_councils = []
    council_counter = Council.query.filter_by(batch_id=batch_id).count() + 1

    leftover_topics = []
    for field_name, topics_in_field in field_groups.items():
        if len(topics_in_field) <= 1:
            leftover_topics.extend(topics_in_field)
            continue
        
        for i in range(0, len(topics_in_field), max_per_council):
            chunk = topics_in_field[i:i + max_per_council]
            if len(chunk) == 1 and i > 0:
                leftover_topics.extend(chunk)
                continue
            suggested_councils.append({
                'name': f"Hội đồng Nghiệm thu NCKH - Tiểu ban {field_name} (HĐ {council_counter})",
                'field': field_name,
                'topics': chunk
            })
            council_counter += 1

    if leftover_topics:
        for i in range(0, len(leftover_topics), max_per_council):
            chunk = leftover_topics[i:i + max_per_council]
            suggested_councils.append({
                'name': f"Hội đồng Nghiệm thu NCKH - Tiểu ban Liên ngành CNTT (HĐ {council_counter})",
                'field': 'Liên ngành CNTT',
                'topics': chunk
            })
            council_counter += 1

    # Phân bổ Giảng viên cho từng Hội đồng
    # Lấy số lượng HĐ mà mỗi GV đã tham gia trong đợt này
    existing_assignments = CouncilMember.query.join(Council).filter(Council.batch_id == batch_id).all()
    lecturer_council_counts = {l.id: 0 for l in all_lecturers}
    for ea in existing_assignments:
        lecturer_council_counts[ea.mentor_id] = lecturer_council_counts.get(ea.mentor_id, 0) + 1

    councils_result = []
    for c_info in suggested_councils:
        topics_list = c_info['topics']
        field_key = c_info['field'].lower()
        
        # Rule 2.2: Chặn GVHD tham gia Hội đồng
        excluded_mentor_ids = set()
        for t in topics_list:
            if t.mentor_id:
                excluded_mentor_ids.add(t.mentor_id)

        candidates = [l for l in all_lecturers if l.id not in excluded_mentor_ids]
        
        # Rule 2.3: Ưu tiên gợi ý GV theo Hướng nghiên cứu
        def lecturer_score(lec):
            score = 0
            text = ((lec.bio or '') + ' ' + (lec.faculty or '')).lower()
            words = [w for w in field_key.split() if len(w) > 2]
            for w in words:
                if w in text:
                    score += 3
            # Cân bằng tải trọng
            score -= lecturer_council_counts.get(lec.id, 0) * 1.5
            return score

        candidates.sort(key=lecturer_score, reverse=True)

        if len(candidates) < 2:
            president = candidates[0] if len(candidates) > 0 else all_lecturers[0]
            secretary = candidates[1] if len(candidates) > 1 else (all_lecturers[1] if all_lecturers[1].id != president.id else all_lecturers[2])
            members = []
        else:
            president = candidates[0]
            secretary = candidates[1]
            members = candidates[2:4] if len(candidates) >= 4 else (candidates[2:3] if len(candidates) >= 3 else [])

        lecturer_council_counts[president.id] += 1
        lecturer_council_counts[secretary.id] += 1
        for m in members:
            lecturer_council_counts[m.id] += 1

        councils_result.append({
            'name': c_info['name'],
            'field': c_info['field'],
            'topics': [{'id': t.id, 'title': t.title, 'mentor_name': t.mentor.full_name if t.mentor else 'Chưa có', 'mentor_id': t.mentor_id, 'field': t.field} for t in topics_list],
            'president': {'id': president.id, 'full_name': president.full_name, 'email': president.email},
            'secretary': {'id': secretary.id, 'full_name': secretary.full_name, 'email': secretary.email},
            'members': [{'id': m.id, 'full_name': m.full_name, 'email': m.email} for m in members]
        })

    # Nếu apply=True: lưu trực tiếp vào DB
    created_councils = []
    if apply_changes:
        default_date = datetime.strptime(meeting_date_str, '%Y-%m-%d').date() if meeting_date_str else datetime.utcnow().date()
        for plan in councils_result:
            new_c = Council(
                name=plan['name'],
                batch_id=batch_id,
                meeting_date=default_date,
                location="Phòng Hội thảo Khoa CNTT"
            )
            db.session.add(new_c)
            db.session.flush()

            db.session.add(CouncilMember(council_id=new_c.id, mentor_id=plan['president']['id'], role='president'))
            db.session.add(CouncilMember(council_id=new_c.id, mentor_id=plan['secretary']['id'], role='secretary'))
            for m in plan['members']:
                db.session.add(CouncilMember(council_id=new_c.id, mentor_id=m['id'], role='member'))

            for t_item in plan['topics']:
                top = Topic.query.get(t_item['id'])
                if top:
                    top.council_id = new_c.id

            created_councils.append(new_c.id)
        db.session.commit()
        return jsonify({
            'message': f'Đã tự động tính toán và thành lập thành công {len(created_councils)} Hội đồng nghiệm thu!',
            'council_ids': created_councils,
            'councils': councils_result
        }), 201

    return jsonify({
        'message': f'Đã tính toán phương án phân bổ {len(unassigned_topics)} đề tài vào {len(councils_result)} Hội đồng!',
        'total_topics': len(unassigned_topics),
        'total_councils': len(councils_result),
        'councils': councils_result
    }), 200
