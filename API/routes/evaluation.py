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
                notif_content = f"Nhóm của bạn đã được sắp xếp báo cáo trước {new_council.name}. Thời gian: {time_str} ngày {date_str}, Địa điểm: {location_str}"
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
    
    return jsonify({
        'message': 'Đã tải lên biên bản cứng thành công!',
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
