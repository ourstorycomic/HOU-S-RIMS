from flask import Blueprint, jsonify, request
from models import Topic, User, Batch, db

topics_bp = Blueprint('topics', __name__, url_prefix='/api/topics')

@topics_bp.route('', methods=['GET'])
def get_topics():
    """
    Get list of topics (with optional filtering)
    ---
    tags:
      - Topics
    parameters:
      - in: query
        name: mentor_id
        type: integer
        description: Filter by mentor ID
      - in: query
        name: status
        type: string
        description: Filter by status (e.g., pending, approved)
      - in: query
        name: group_id
        type: string
        description: Filter by group ID (use 'null' or '0' for topics without a group)
    responses:
      200:
        description: List of topics
    """
    query = Topic.query.join(Batch).filter(Batch.status != 'hidden')
    
    # Filter by mentor
    mentor_id = request.args.get('mentor_id')
    if mentor_id:
        query = query.filter(Topic.mentor_id == mentor_id)
        
    # Filter by status (e.g. pending)
    status = request.args.get('status')
    if status:
        query = query.filter(Topic.status == status)
        
    # Filter by group_id
    group_id = request.args.get('group_id')
    if group_id:
        if group_id.lower() == 'null' or group_id == '0':
            query = query.filter(Topic.group_id.is_(None))
        else:
            query = query.filter(Topic.group_id == group_id)
            
    topics = query.all()
    result = []
    for topic in topics:
        result.append({
            'id': topic.id,
            'name': topic.name,
            'description': topic.description,
            'batch_id': topic.batch_id,
            'mentor_id': topic.mentor_id,
            'group_id': topic.group_id,
            'status': topic.status,
            'created_at': topic.created_at.strftime('%Y-%m-%d %H:%M:%S') if topic.created_at else None
        })
    return jsonify(result), 200

@topics_bp.route('/my-topic', methods=['GET'])
def get_my_topic():
    from flask import session
    from models import Group, GroupMember, Topic, User, Batch
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Chỉ lấy các nhóm mà sinh viên là Trưởng nhóm hoặc ĐÃ CHẤP NHẬN tham gia
    member_group_ids = [m.group_id for m in GroupMember.query.filter(
        GroupMember.student_id == user_id,
        GroupMember.status.in_(['accepted', 'joined'])
    ).all()]
    
    my_led_groups = Group.query.filter_by(leader_id=user_id).all()
    groups = Group.query.filter(
        (Group.leader_id == user_id) | (Group.id.in_(member_group_ids))
    ).all() if (member_group_ids or my_led_groups) else []
    
    topic = None
    if groups:
        group_ids = [g.id for g in groups]
        topic = Topic.query.filter(Topic.group_id.in_(group_ids)).order_by(Topic.id.desc()).first()
    else:
        topic = Topic.query.join(Group).filter(Group.leader_id == user_id).order_by(Topic.id.desc()).first()
        
    if not topic:
        return jsonify({'has_topic': False, 'topic': None}), 200
        
    status_map = {'waiting_for_members': 0, 'pending': 1, 'faculty_pending': 2, 'approved': 3, 'rejected': 0}
    step = status_map.get(topic.status, 1)
    pct = 100 if topic.status == 'approved' else (50 if topic.status == 'faculty_pending' else 0)
    
    status_labels = {
        'approved': 'ĐÃ PHÊ DUYỆT CHÍNH THỨC',
        'faculty_pending': 'GV ĐÃ DUYỆT • CHỜ KHOA DUYỆT',
        'waiting_for_members': 'CHỜ THÀNH VIÊN XÁC NHẬN',
        'rejected': 'TỪ CHỐI PHÊ DUYỆT',
        'pending': 'ĐANG CHỜ GV DUYỆT'
    }
    status_label = status_labels.get(topic.status, 'ĐANG CHỜ GV DUYỆT')
    
    is_leader = bool(topic.group and topic.group.leader_id == user_id)

    members_data = []
    has_rejected_members = False
    has_pending_members = False
    rejected_names = []
    if topic.group:
        for m in topic.group.members:
            st = m.student
            if st:
                is_mem_leader = (st.id == topic.group.leader_id)
                st_code = getattr(st, 'student_id', '') or ''
                m_info = {
                    'id': m.id,
                    'student_id': st.id,
                    'student_code': st_code,
                    'full_name': st.full_name or '',
                    'avatar': getattr(st, 'avatar', None),
                    'status': m.status,
                    'is_leader': is_mem_leader
                }
                members_data.append(m_info)
                if m.status in ['rejected', 'declined']:
                    has_rejected_members = True
                    rejected_names.append(st.full_name or f"SV {st_code}")
                elif m.status in ['pending', 'invited']:
                    has_pending_members = True
    
    return jsonify({
        'has_topic': True,
        'topic': {
            'id': topic.id,
            'title': topic.title,
            'description': topic.description or '',
            'status': topic.status,
            'status_label': status_label,
            'batch_id': topic.batch_id,
            'batch_name': topic.batch.name if topic.batch else 'Đợt 1 NCKH Sinh viên 2025 - 2026',
            'created_at': topic.created_at.strftime('%d/%m/%Y %H:%M') if topic.created_at else '',
            'mentor_id': topic.mentor_id,
            'mentor_name': topic.mentor.full_name if topic.mentor else 'Chưa có',
            'group_id': topic.group_id,
            'group_name': topic.group.name if topic.group else f"Nhóm ID: {topic.group_id}",
            'is_leader': is_leader,
            'step': step,
            'pct': pct,
            'members': members_data,
            'has_rejected_members': has_rejected_members,
            'has_pending_members': has_pending_members,
            'rejected_names': rejected_names
        }
    }), 200

# Task 3: Lấy danh sách mentor
mentors_bp = Blueprint('mentors', __name__, url_prefix='/api/mentors')

@mentors_bp.route('', methods=['GET'])
def get_mentors():
    """
    Get list of mentors
    ---
    tags:
      - Mentors
    responses:
      200:
        description: List of mentors
    """
    mentors = User.query.filter_by(role='Lecturer').all()
    result = []
    for mentor in mentors:
        result.append({
            'id': mentor.id,
            'username': mentor.username,
            'full_name': mentor.full_name,
            'email': mentor.email,
            'phone': mentor.phone,
            'bio': mentor.bio
        })
    return jsonify(result), 200

@topics_bp.route('/register', methods=['POST'])
def register_topic():
    """
    Register a new topic
    ---
    tags:
      - Topics
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
            description:
              type: string
            batch_id:
              type: integer
            mentor_id:
              type: integer
            group_id:
              type: integer
    responses:
      201:
        description: Topic registered successfully
      400:
        description: Invalid request
    """
    data = request.get_json()
    if not data or 'mentor_id' not in data:
        return jsonify({'error': 'Vui lòng chọn Giảng viên hướng dẫn'}), 400
        
    try:
        from flask import session
        from models import Group, GroupMember, Batch
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401
            
        batch_id = data.get('batch_id')
        if not batch_id:
            active_b = Batch.query.filter_by(status='active').order_by(Batch.id.desc()).first()
            batch_id = active_b.id if active_b else 1
            
        group_id = data.get('group_id', 0)
        members_list = data.get('members', [])
        topic_title = data.get('name', '').strip() or 'Đề tài NCKH (Chưa đặt tên)'
        # 1. Xác định group_id và tạo/cập nhật nhóm
        if group_id == 0:
            # Auto-create group
            group_name = f"Nhóm {topic_title}" if topic_title != 'Đề tài NCKH (Chưa đặt tên)' else f"Nhóm NCKH - SV{user_id}"
            new_group = Group(
                name=group_name,
                batch_id=batch_id,
                leader_id=user_id,
                mentor_id=data['mentor_id'],
                status='pending_mentor'
            )
            db.session.add(new_group)
            db.session.flush() # To get new_group.id
            group_id = new_group.id
            
            # Add leader as accepted member
            new_member = GroupMember(group_id=group_id, student_id=user_id, status='accepted')
            db.session.add(new_member)
        else:
            # Check if group already has a topic in this batch
            existing_topic = Topic.query.filter_by(group_id=group_id, batch_id=batch_id).first()
            if existing_topic:
                return jsonify({'error': 'Nhóm đã đăng ký một đề tài trong đợt này rồi'}), 400
            
            # Update group mentor and name
            target_group = Group.query.get(group_id)
            if target_group:
                target_group.mentor_id = data['mentor_id']
                target_group.status = 'pending_mentor'
                if topic_title != 'Đề tài NCKH (Chưa đặt tên)':
                    target_group.name = f"Nhóm {topic_title}"

        # 2. Xử lý thành viên nhóm khác user_id (dù là tạo mới hay nhóm có sẵn)
        other_member_ids = set()
        for mid in members_list:
            if mid and str(mid) != str(user_id):
                try:
                    other_member_ids.add(int(mid))
                except (ValueError, TypeError):
                    pass

        # Nếu group có các thành viên khác từ trước, cũng thêm vào danh sách cần xác nhận
        existing_other_gms = GroupMember.query.filter(
            GroupMember.group_id == group_id,
            GroupMember.student_id != user_id
        ).all()
        for gm in existing_other_gms:
            other_member_ids.add(gm.student_id)

        # Với mỗi thành viên khác: Đặt status = 'pending' và gửi lời mời
        for mid in other_member_ids:
            gm = GroupMember.query.filter_by(group_id=group_id, student_id=mid).first()
            if not gm:
                gm = GroupMember(group_id=group_id, student_id=mid, status='pending')
                db.session.add(gm)
            else:
                gm.status = 'pending'

            # Gửi lời mời qua tin nhắn chat riêng
            from models import Message as Msg
            import json
            inviter = User.query.get(user_id)
            invite_msg = Msg(
                sender_id=user_id,
                receiver_id=mid,
                group_id=None,
                content=f"📩 Mời bạn tham gia nhóm NCKH cho đề tài **{topic_title}**. Nhấn Đồng ý để xác nhận.",
                message_type='invitation',
                meta_data=json.dumps({'invite_group_id': group_id, 'topic_name': topic_title})
            )
            db.session.add(invite_msg)

            # Gửi notification in-app cho thành viên
            from models import Notification
            invited_user = User.query.get(mid)
            if invited_user:
                link = f"/student#s-explore"
                html_content = (
                    f"<p>Xin chào <strong>{invited_user.full_name}</strong>,</p>"
                    f"<p>Bạn vừa nhận được lời mời tham gia nhóm NCKH cho đề tài: <strong>{topic_title}</strong>.</p>"
                    f"<a href='{link}' class='btn btn-primary rounded-pill btn-sm mt-2'>Xem lời mời</a>"
                )
                new_notif = Notification(user_id=mid, content=html_content)
                db.session.add(new_notif)

                # Gửi email cho thành viên
                if invited_user.email:
                    from email_utils import send_email_async
                    email_link = f"http://127.0.0.1:5000/student/chat"
                    email_html = (
                        f"<div style='font-family: Arial, sans-serif; padding: 20px; color: #333;'>"
                        f"<h2 style='color: #4f46e5;'>Lời mời tham gia nhóm NCKH</h2>"
                        f"<p>Xin chào <strong>{invited_user.full_name}</strong>,</p>"
                        f"<p>Bạn vừa nhận được lời mời tham gia nhóm NCKH cho đề tài: <strong>{topic_title}</strong> từ sinh viên {inviter.full_name if inviter else ''}.</p>"
                        f"<p>Vui lòng đăng nhập hệ thống và vào mục Chat Cá nhân để Đồng ý hoặc Từ chối lời mời này.</p>"
                        f"<a href='{email_link}' style='display: inline-block; padding: 10px 20px; background-color: #4f46e5; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px;'>Xem lời mời</a>"
                        f"<br><br><p style='color: #666; font-size: 12px;'>Trân trọng,<br>Hệ thống HOU S-RIMS</p>"
                        f"</div>"
                    )
                    send_email_async(invited_user.email, f"[HOU S-RIMS] Lời mời tham gia nhóm NCKH", f"Bạn được mời tham gia đề tài {topic_title}", email_html)

        has_pending_members = len(other_member_ids) > 0
        topic_status = 'waiting_for_members' if has_pending_members else 'pending'

        faculty = data.get('faculty', '') or 'Khoa Công nghệ Thông tin'
        major = data.get('major', '')
        domain = data.get('domain', '') or 'Kỹ thuật & Công nghệ'
        user_desc = (data.get('raw_description') or '').strip()
        raw_desc = (data.get('description') or '').strip()
        
        if not user_desc and raw_desc and 'Chờ nhóm và GVHD thảo luận' not in raw_desc:
            user_desc = raw_desc

        if user_desc:
            meta_badges = []
            if major: meta_badges.append(f"<span class='badge bg-light text-dark border me-1'>Chuyên ngành: {major}</span>")
            if domain: meta_badges.append(f"<span class='badge bg-light text-dark border'>Lĩnh vực: {domain}</span>")
            meta_html = f"<div class='mt-2 pt-2 border-top'>{' '.join(meta_badges)}</div>" if meta_badges else ""
            final_desc = f"{user_desc}{meta_html}"
        else:
            desc_parts = []
            if raw_desc and not any(tag in raw_desc for tag in ['Khoa:', 'Chuyên ngành:', 'Lĩnh vực:']):
                desc_parts.append(raw_desc)
            if major: desc_parts.append(f"Chuyên ngành: {major}")
            if domain: desc_parts.append(f"Lĩnh vực: {domain}")
            final_desc = " | ".join(desc_parts) if desc_parts else (raw_desc or 'Chờ nhóm và GVHD thảo luận thống nhất tên đề tài.')

        new_topic = Topic(
            title=topic_title,
            description=final_desc,
            batch_id=batch_id,
            mentor_id=data['mentor_id'],
            group_id=group_id,
            status=topic_status
        )
        db.session.add(new_topic)
        db.session.flush() # To get new_topic.id
        
        from models import TopicRegistration
        registration = TopicRegistration(
            topic_id=new_topic.id,
            group_id=new_topic.group_id,
            mentor_id=new_topic.mentor_id,
            status=topic_status
        )
        db.session.add(registration)
        db.session.commit() # Transaction completed
        
        # TUYỆT ĐỐI CHỈ GỬI THÔNG BÁO CHO GIẢNG VIÊN KHI ĐÂY LÀ ĐĂNG KÝ CÁ NHÂN (1 người)
        if topic_status == 'pending' and not has_pending_members:
            from models import Notification
            mentor = User.query.get(data['mentor_id'])
            link = f"/lecturer/approve"
            
            desc_html = (
                f"<div style='background: #f8fafc; border-left: 4px solid #4f46e5; padding: 12px 16px; margin: 12px 0; border-radius: 6px; border: 1px solid #e2e8f0;'>"
                f"<strong style='color: #4338ca; display: block; margin-bottom: 6px;'><i class='fa-solid fa-align-left me-1'></i> Mô tả đề tài / Ý tưởng từ sinh viên:</strong>"
                f"<div class='rich-content-display' style='margin: 0; font-size: 13px; color: #334155; line-height: 1.6;'>{user_desc}</div>"
                f"</div>"
            ) if user_desc else ""

            html_content = (
                f"<p>Xin chào <strong>{mentor.full_name}</strong>,</p>"
                f"<p>Sinh viên vừa gửi yêu cầu nhờ bạn hướng dẫn đề tài NCKH: <strong>{topic_title}</strong>.</p>"
                f"{desc_html}"
                f"<a href='{link}' class='btn btn-primary rounded-pill btn-sm mt-2'>Phê duyệt Đề tài</a>"
            )
            new_notif = Notification(user_id=mentor.id, content=html_content)
            db.session.add(new_notif)
            db.session.commit()
            
            from email_utils import send_email_async
            if mentor and mentor.email:
                email_link = f"http://127.0.0.1:5000/lecturer/approve"
                email_desc_html = (
                    f"<div style='background: #f1f5f9; border-left: 4px solid #4f46e5; padding: 14px 18px; margin: 14px 0; border-radius: 6px;'>"
                    f"<strong style='color: #312e81; display: block; margin-bottom: 8px;'>Mô tả đề tài / Ý tưởng nghiên cứu từ sinh viên:</strong>"
                    f"<div class='rich-content-display' style='margin: 0; font-size: 14px; color: #1e293b; line-height: 1.6;'>{user_desc}</div>"
                    f"</div>"
                ) if user_desc else ""

                email_html = (
                    f"<div style='font-family: Arial, sans-serif; padding: 20px; color: #333;'>"
                    f"<h2 style='color: #4f46e5;'>Yêu cầu Hướng dẫn Đề tài NCKH</h2>"
                    f"<p>Xin chào <strong>{mentor.full_name}</strong>,</p>"
                    f"<p>Sinh viên vừa gửi yêu cầu nhờ bạn hướng dẫn đề tài NCKH: <strong>{topic_title}</strong>.</p>"
                    f"{email_desc_html}"
                    f"<p>Vui lòng đăng nhập hệ thống để xem chi tiết và Quyết định Phê duyệt / Từ chối.</p>"
                    f"<a href='{email_link}' style='display: inline-block; padding: 10px 20px; background-color: #4f46e5; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px;'>Phê duyệt Đề tài</a>"
                    f"<br><br><p style='color: #666; font-size: 12px;'>Trân trọng,<br>Hệ thống HOU S-RIMS</p>"
                    f"</div>"
                )
                send_email_async(mentor.email, f"[HOU S-RIMS] Yêu cầu Hướng dẫn Đề tài NCKH", f"Yêu cầu hướng dẫn đề tài {topic_title}", email_html)
        else:
            # ĐỀ TÀI THEO NHÓM: TUYỆT ĐỐI KHÔNG GỬI GÌ CHO GIẢNG VIÊN
            # CHỈ thông báo cho trưởng nhóm về việc chờ các thành viên nhóm xác nhận
            from models import Notification
            leader_notif = Notification(
                user_id=user_id,
                content=(
                    f"<p>Đề tài <strong>{topic_title}</strong> đã được đăng ký thành công!</p>"
                    f"<p>Hệ thống đã gửi lời mời tới các thành viên nhóm. Đề tài đang ở trạng thái <em>Chờ thành viên xác nhận</em> trước khi gửi tới Giảng viên hướng dẫn.</p>"
                )
            )
            db.session.add(leader_notif)
            db.session.commit()
                
        return jsonify({'message': 'Topic registered successfully', 'topic_id': new_topic.id, 'status': topic_status}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@topics_bp.route('/invitation', methods=['POST'])
def handle_invitation():
    from flask import session
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json() or {}
    raw_group_id = data.get('group_id')
    action = data.get('action') # 'accepted' or 'rejected'
    msg_id = data.get('msg_id')
    
    if not raw_group_id or not action:
        return jsonify({'error': 'Missing parameters'}), 400
        
    try:
        group_id = int(raw_group_id)
        from models import GroupMember, Topic, Message, User, Notification
        import json
        
        # Update message metadata if msg_id provided
        if msg_id:
            msg = Message.query.get(msg_id)
            if msg and msg.receiver_id == user_id:
                try:
                    meta = json.loads(msg.meta_data or '{}')
                    meta['invite_status'] = action
                    msg.meta_data = json.dumps(meta)
                except:
                    pass
                    
        member = GroupMember.query.filter(
            GroupMember.group_id == group_id,
            GroupMember.student_id == user_id,
            GroupMember.status.in_(['pending', 'invited'])
        ).first()
        
        if not member:
            # Check if already accepted/rejected or wrong account
            existing = GroupMember.query.filter_by(group_id=group_id, student_id=user_id).first()
            curr_user = User.query.get(user_id)
            user_label = curr_user.full_name if curr_user else f"ID {user_id}"
            if existing:
                if existing.status in ['accepted', 'joined']:
                    return jsonify({'error': f'Tài khoản {user_label} đã tham gia nhóm này rồi!'}), 400
                elif existing.status in ['rejected', 'declined']:
                    return jsonify({'error': f'Tài khoản {user_label} đã từ chối lời mời này.'}), 400
            return jsonify({'error': f'Không tìm thấy lời mời nhóm #{group_id} cho tài khoản {user_label}. Vui lòng kiểm tra lại tài khoản sinh viên đang đăng nhập!'}), 404
            
        if action == 'rejected':
            member.status = 'rejected'
        else:
            member.status = 'accepted'
            
        # Update any chat messages of type invitation for this group and user
        try:
            from models import Message as Msg
            invite_msgs = Msg.query.filter_by(receiver_id=user_id, message_type='invitation').all()
            for im in invite_msgs:
                if im.meta_data:
                    m_meta = json.loads(im.meta_data)
                    if m_meta.get('invite_group_id') == group_id:
                        m_meta['invite_status'] = action
                        im.meta_data = json.dumps(m_meta)
        except Exception:
            pass

        # Mark any previous invitation notifications for this user as read
        try:
            user_notifs = Notification.query.filter_by(user_id=user_id, is_read=False).all()
            for un in user_notifs:
                if 'lời mời tham gia nhóm' in (un.content or '').lower():
                    un.is_read = True
        except Exception:
            pass

        # Gửi thông báo phản hồi tới trưởng nhóm (người gửi lời mời)
        from models import Group
        group = member.group or Group.query.get(group_id)
        topic = Topic.query.filter_by(group_id=group_id).first()
        topic_title = topic.title if topic and topic.title else "NCKH"
        responder = User.query.get(user_id)
        responder_name = responder.full_name if responder else f"Sinh viên {user_id}"
        group_name = group.name if group else f"Nhóm #{group_id}"

        if group and group.leader_id and group.leader_id != user_id:
            leader_id = group.leader_id
            leader_user = User.query.get(leader_id)
            
            if action == 'accepted':
                notif_html = (
                    f"<p>Sinh viên <strong>{responder_name}</strong> đã <span class='text-success fw-bold'>đồng ý</span> "
                    f"tham gia nhóm <strong>{group_name}</strong> (Đề tài: <em>{topic_title}</em>).</p>"
                    f"<button type='button' onclick='event.stopPropagation(); showGroupMembersModal({group_id})' class='btn btn-success btn-sm rounded-pill mt-2 px-3 fw-bold shadow-sm'>"
                    f"<i class='fa-solid fa-users me-1'></i> Xem thành viên nhóm</button>"
                )
            else:
                notif_html = (
                    f"<p>⚠️ Sinh viên <strong>{responder_name}</strong> đã <span class='text-danger fw-bold'>từ chối</span> "
                    f"tham gia nhóm <strong>{group_name}</strong> (Đề tài: <em>{topic_title}</em>).</p>"
                    f"<p class='small text-muted mb-2'>Hệ thống đã <strong>tạm ngưng không gửi đề tài tới Giảng viên hướng dẫn</strong>. Bạn có thể hủy đăng ký để mời thành viên khác hoặc tiếp tục gửi đề tài với số người hiện tại.</p>"
                    f"<a href='/student#s-register' class='btn btn-danger btn-sm rounded-pill mt-1 px-3 fw-bold shadow-xs'>"
                    f"<i class='fa-solid fa-sliders me-1'></i> Xử lý đề tài ngay</a>"
                )
            leader_notif = Notification(user_id=leader_id, content=notif_html)
            db.session.add(leader_notif)

            # Gửi tin nhắn chat phản hồi vào hộp thoại riêng với trưởng nhóm
            try:
                from models import Message as Msg
                chat_text = f"✅ Tôi đã đồng ý tham gia nhóm **{group_name}**." if action == 'accepted' else f"❌ Tôi xin phép từ chối tham gia nhóm **{group_name}**."
                fb_msg = Msg(
                    sender_id=user_id,
                    receiver_id=leader_id,
                    group_id=None,
                    content=chat_text,
                    message_type='text'
                )
                db.session.add(fb_msg)
            except Exception:
                pass

            # Gửi email phản hồi cho trưởng nhóm
            if leader_user and leader_user.email:
                try:
                    from email_utils import send_email_async
                    if action == 'accepted':
                        email_html = (
                            f"<div style='font-family: Arial, sans-serif; padding: 20px; color: #333;'>"
                            f"<h2 style='color: #10b981;'>Phản hồi lời mời tham gia nhóm NCKH</h2>"
                            f"<p>Xin chào <strong>{leader_user.full_name}</strong>,</p>"
                            f"<p>Sinh viên <strong>{responder_name}</strong> đã <strong style='color: #10b981;'>đồng ý</strong> tham gia nhóm <strong>{group_name}</strong> (Đề tài: {topic_title}).</p>"
                            f"<p>Bạn có thể vào hệ thống để kiểm tra danh sách thành viên nhóm và tiến độ đề tài.</p>"
                            f"<a href='http://127.0.0.1:5000/student#s-register' style='display: inline-block; padding: 10px 20px; background-color: #10b981; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px;'>Xem nhóm NCKH</a>"
                            f"<br><br><p style='color: #666; font-size: 12px;'>Trân trọng,<br>Hệ thống HOU S-RIMS</p>"
                            f"</div>"
                        )
                        send_email_async(
                            leader_user.email,
                            f"[HOU S-RIMS] {responder_name} đã chấp nhận tham gia nhóm {group_name}",
                            f"{responder_name} đã chấp nhận tham gia nhóm {group_name}",
                            email_html
                        )
                    else:
                        email_html = (
                            f"<div style='font-family: Arial, sans-serif; padding: 20px; color: #333; line-height: 1.6;'>"
                            f"<h2 style='color: #ef4444; border-bottom: 2px solid #ef4444; padding-bottom: 8px;'>Thông báo: Thành viên từ chối tham gia nhóm NCKH</h2>"
                            f"<p>Xin chào <strong>{leader_user.full_name}</strong> (Trưởng nhóm),</p>"
                            f"<p>Sinh viên <strong>{responder_name}</strong> đã <strong style='color: #ef4444;'>từ chối</strong> lời mời tham gia nhóm <strong>{group_name}</strong> cho đề tài: <em>{topic_title}</em>.</p>"
                            f"<div style='background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 12px 16px; margin: 15px 0; border-radius: 4px;'>"
                            f"<strong style='color: #991b1b;'>LƯU Ý QUAN TRỌNG:</strong>"
                            f"<p style='margin: 6px 0 0 0; color: #7f1d1d;'>Hệ thống đã <strong>TẠM NGƯNG GỬI HỒ SƠ ĐỀ TÀI LÊN GIẢNG VIÊN HƯỚNG DẪN</strong> để chờ quyết định của bạn.</p>"
                            f"</div>"
                            f"<p>Bạn có 2 sự lựa chọn trên hệ thống:</p>"
                            f"<ul>"
                            f"<li><strong>Lựa chọn 1:</strong> Hủy đăng ký đề tài hiện tại để đăng ký mới và mời thành viên khác thay thế.</li>"
                            f"<li><strong>Lựa chọn 2:</strong> Tiếp tục gửi hồ sơ đề tài lên Giảng viên hướng dẫn / Khoa với số lượng thành viên hiện tại (sau khi đã loại bỏ người từ chối ra khỏi nhóm).</li>"
                            f"</ul>"
                            f"<a href='http://127.0.0.1:5000/student#s-register' style='display: inline-block; padding: 10px 22px; background-color: #ef4444; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; margin-top: 10px;'>Vào hệ thống xử lý đề tài</a>"
                            f"<br><br><p style='color: #666; font-size: 12px;'>Trân trọng,<br>Hệ thống Quản lý Nghiên cứu Khoa học Sinh viên HOU S-RIMS</p>"
                            f"</div>"
                        )
                        send_email_async(
                            leader_user.email,
                            f"[HOU S-RIMS] Thành viên {responder_name} từ chối tham gia nhóm {group_name}",
                            f"{responder_name} đã từ chối tham gia nhóm {group_name}. Đề tài tạm ngưng gửi GVHD.",
                            email_html
                        )
                except Exception:
                    pass

        # Check if all members accepted
        db.session.flush()
        pending_count = GroupMember.query.filter(
            GroupMember.group_id == group_id,
            GroupMember.status.in_(['pending', 'invited'])
        ).count()
        rejected_count = GroupMember.query.filter(
            GroupMember.group_id == group_id,
            GroupMember.status.in_(['rejected', 'declined'])
        ).count()
        
        if topic and topic.status == 'waiting_for_members':
            if rejected_count > 0:
                pass # TH2: Có thành viên từ chối, tạm ngưng không gửi lên GVHD, chờ quyết định trưởng nhóm
            elif pending_count == 0:
                # TH1: TẤT CẢ THÀNH VIÊN ĐỀU ĐỒNG Ý -> TỰ ĐỘNG GỬI LÊN GIẢNG VIÊN HƯỚNG DẪN
                topic.status = 'pending' # Now waiting for lecturer
                
                from models import TopicRegistration
                registration = TopicRegistration.query.filter_by(topic_id=topic.id).first()
                if registration:
                    registration.status = 'pending'
                    
                mentor = User.query.get(topic.mentor_id)
                if mentor:
                    link = f"/lecturer/approve"
                    html_content = (
                        f"<p>Xin chào <strong>{mentor.full_name}</strong>,</p>"
                        f"<p>Nhóm sinh viên vừa gửi yêu cầu nhờ bạn hướng dẫn đề tài NCKH: <strong>{topic.title}</strong> (Tất cả thành viên trong nhóm đã đồng ý tham gia).</p>"
                        f"<a href='{link}' class='btn btn-primary rounded-pill btn-sm mt-2'>Phê duyệt Đề tài</a>"
                    )
                    new_notif = Notification(user_id=mentor.id, content=html_content)
                    db.session.add(new_notif)
                
                from email_utils import send_email_async
                if mentor and mentor.email:
                    email_link = f"http://127.0.0.1:5000/lecturer/approve"
                    email_html = (
                        f"<div style='font-family: Arial, sans-serif; padding: 20px; color: #333;'>"
                        f"<h2 style='color: #4f46e5;'>Yêu cầu Hướng dẫn Đề tài NCKH</h2>"
                        f"<p>Xin chào <strong>{mentor.full_name}</strong>,</p>"
                        f"<p>Nhóm sinh viên vừa gửi yêu cầu nhờ bạn hướng dẫn đề tài NCKH: <strong>{topic.title}</strong>.</p>"
                        f"<p>Tất cả các thành viên trong nhóm đã xác nhận đồng ý tham gia.</p>"
                        f"<p>Vui lòng đăng nhập hệ thống để xem chi tiết và Quyết định Phê duyệt / Từ chối.</p>"
                        f"<a href='{email_link}' style='display: inline-block; padding: 10px 20px; background-color: #4f46e5; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px;'>Phê duyệt Đề tài</a>"
                        f"<br><br><p style='color: #666; font-size: 12px;'>Trân trọng,<br>Hệ thống HOU S-RIMS</p>"
                        f"</div>"
                    )
                    send_email_async(mentor.email, f"[HOU S-RIMS] Yêu cầu hướng dẫn đề tài", f"Yêu cầu hướng dẫn đề tài {topic.title}", email_html)

                # Thông báo cho Trưởng nhóm biết đề tài đã chuyển tới GVHD
                if group and group.leader_id:
                    leader_user = User.query.get(group.leader_id)
                    all_accepted_notif = Notification(
                        user_id=group.leader_id,
                        content=(
                            f"<p>🎉 <strong>Tất cả thành viên trong nhóm đã đồng ý tham gia!</strong></p>"
                            f"<p>Hồ sơ đề tài <strong>{topic.title}</strong> đã được tự động chuyển tới Giảng viên hướng dẫn "
                            f"<strong>{mentor.full_name if mentor else ''}</strong> để xem xét phê duyệt.</p>"
                        )
                    )
                    db.session.add(all_accepted_notif)
                    if leader_user and leader_user.email:
                        from email_utils import send_email_async
                        send_email_async(
                            leader_user.email,
                            f"[HOU S-RIMS] Tất cả thành viên đã đồng ý - Đề tài {topic.title} đã gửi tới GVHD",
                            f"Tất cả thành viên nhóm đã đồng ý. Đề tài {topic.title} đã được gửi tới GVHD.",
                            (
                                f"<div style='font-family: Arial, sans-serif; padding: 20px; color: #333;'>"
                                f"<h2 style='color: #10b981;'>Tất cả thành viên đã xác nhận tham gia nhóm</h2>"
                                f"<p>Xin chào <strong>{leader_user.full_name}</strong>,</p>"
                                f"<p>Tất cả các thành viên bạn mời đã đồng ý tham gia nhóm <strong>{group_name}</strong>.</p>"
                                f"<p>Hồ sơ đề tài <strong>{topic.title}</strong> đã chính thức được chuyển tới Giảng viên hướng dẫn <strong>{mentor.full_name if mentor else ''}</strong> để phê duyệt.</p>"
                                f"<a href='http://127.0.0.1:5000/student#s-register' style='display: inline-block; padding: 10px 20px; background-color: #10b981; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px;'>Xem tiến độ đề tài</a>"
                                f"<br><br><p style='color: #666; font-size: 12px;'>Trân trọng,<br>Hệ thống HOU S-RIMS</p>"
                                f"</div>"
                            )
                        )
            
        db.session.commit()
        return jsonify({'message': 'Successfully processed invitation'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@topics_bp.route('/<int:topic_id>/proceed-without-declined', methods=['POST'])
def proceed_without_declined(topic_id):
    from flask import session
    from models import Topic, TopicRegistration, Group, GroupMember, User, Notification
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        topic = Topic.query.get(topic_id)
        if not topic:
            return jsonify({'error': 'Không tìm thấy đề tài'}), 404

        group = Group.query.get(topic.group_id)
        if not group or group.leader_id != user_id:
            return jsonify({'error': 'Chỉ trưởng nhóm mới có quyền quyết định luồng gửi đề tài này!'}), 403

        # Xóa toàn bộ các thành viên đã từ chối ra khỏi nhóm
        declined_members = GroupMember.query.filter(
            GroupMember.group_id == group.id,
            GroupMember.status.in_(['rejected', 'declined'])
        ).all()
        
        declined_count = len(declined_members)
        for m in declined_members:
            db.session.delete(m)
        db.session.flush()

        # Kiểm tra xem còn ai đang pending không
        pending_members = GroupMember.query.filter(
            GroupMember.group_id == group.id,
            GroupMember.student_id != user_id,
            GroupMember.status.in_(['pending', 'invited'])
        ).all()

        mentor = User.query.get(topic.mentor_id)
        mentor_name = mentor.full_name if mentor else "Giảng viên hướng dẫn"

        if len(pending_members) > 0:
            # Vẫn còn thành viên chưa trả lời lời mời
            db.session.commit()
            return jsonify({
                'success': True,
                'topic_status': topic.status,
                'message': f"Đã loại bỏ {declined_count} thành viên từ chối. Nhóm vẫn đang chờ {len(pending_members)} thành viên còn lại xác nhận lời mời."
            }), 200
        else:
            # Không còn ai pending (chỉ còn những người đã accept hoặc chỉ còn trưởng nhóm) -> Gửi thẳng cho GVHD!
            topic.status = 'pending'
            registration = TopicRegistration.query.filter_by(topic_id=topic.id).first()
            if registration:
                registration.status = 'pending'

            # Gửi thông báo & email cho GVHD
            if mentor:
                link = f"/lecturer/approve"
                html_content = (
                    f"<p>Xin chào <strong>{mentor.full_name}</strong>,</p>"
                    f"<p>Nhóm sinh viên vừa gửi yêu cầu nhờ bạn hướng dẫn đề tài NCKH: <strong>{topic.title}</strong>.</p>"
                    f"<p>Danh sách thành viên chính thức đã được Trưởng nhóm xác nhận.</p>"
                    f"<a href='{link}' class='btn btn-primary rounded-pill btn-sm mt-2'>Phê duyệt Đề tài</a>"
                )
                new_notif = Notification(user_id=mentor.id, content=html_content)
                db.session.add(new_notif)

                if mentor.email:
                    from email_utils import send_email_async
                    email_link = f"http://127.0.0.1:5000/lecturer/approve"
                    email_html = (
                        f"<div style='font-family: Arial, sans-serif; padding: 20px; color: #333;'>"
                        f"<h2 style='color: #4f46e5;'>Yêu cầu Hướng dẫn Đề tài NCKH</h2>"
                        f"<p>Xin chào <strong>{mentor.full_name}</strong>,</p>"
                        f"<p>Nhóm sinh viên vừa gửi yêu cầu nhờ bạn hướng dẫn đề tài NCKH: <strong>{topic.title}</strong>.</p>"
                        f"<p>Danh sách thành viên chính thức đã được Trưởng nhóm xác nhận.</p>"
                        f"<a href='{email_link}' style='display: inline-block; padding: 10px 20px; background-color: #4f46e5; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px;'>Phê duyệt Đề tài</a>"
                        f"<br><br><p style='color: #666; font-size: 12px;'>Trân trọng,<br>Hệ thống HOU S-RIMS</p>"
                        f"</div>"
                    )
                    send_email_async(mentor.email, f"[HOU S-RIMS] Yêu cầu hướng dẫn đề tài", f"Yêu cầu hướng dẫn đề tài {topic.title}", email_html)

            # Gửi thông báo xác nhận cho Trưởng nhóm
            leader_confirm_notif = Notification(
                user_id=user_id,
                content=(
                    f"<p>✅ Đã loại bỏ thành viên từ chối và gửi hồ sơ đề tài <strong>{topic.title}</strong> "
                    f"tới Giảng viên hướng dẫn <strong>{mentor_name}</strong> thành công!</p>"
                )
            )
            db.session.add(leader_confirm_notif)
            db.session.commit()

            return jsonify({
                'success': True,
                'topic_status': 'pending',
                'message': f"Đã loại bỏ thành viên từ chối và chuyển hồ sơ đề tài tới {mentor_name} thành công!"
            }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@topics_bp.route('/<int:topic_id>', methods=['DELETE'])
def cancel_topic(topic_id):
    from flask import session
    from models import Topic, TopicRegistration, Group, GroupMember, Evaluation, Meeting, Milestone, Submission, Message
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
        
    try:
        topic = None
        if topic_id and topic_id != 0:
            topic = Topic.query.get(topic_id)
            
        if not topic:
            # Fallback: Tìm đề tài chưa được duyệt chính thức của user_id (với vai trò Trưởng nhóm)
            user_groups = Group.query.filter_by(leader_id=user_id).order_by(Group.id.desc()).all()
            for g in user_groups:
                t = Topic.query.filter_by(group_id=g.id).filter(Topic.status != 'approved').order_by(Topic.id.desc()).first()
                if t:
                    topic = t
                    break

        if not topic:
            return jsonify({'error': 'Không tìm thấy hồ sơ đề tài cần hủy (Topic not found)'}), 404
            
        group = Group.query.get(topic.group_id) if topic.group_id else None
        if group and group.leader_id != user_id:
            return jsonify({'error': 'Chỉ trưởng nhóm mới có quyền hủy đăng ký đề tài này'}), 403
            
        if topic.status == 'approved':
            return jsonify({'error': 'Đề tài đã được Khoa phê duyệt chính thức nên không thể tự ý hủy!'}), 400
            
        # 1. Xóa các đăng ký đề tài (TopicRegistration)
        TopicRegistration.query.filter_by(topic_id=topic.id).delete()
        if group:
            TopicRegistration.query.filter_by(group_id=group.id).delete()
        
        # 2. Xóa các dữ liệu liên quan (Evaluation, Meeting, Milestone, Submission)
        try:
            Evaluation.query.filter_by(topic_id=topic.id).delete()
        except Exception:
            pass
        try:
            Meeting.query.filter_by(topic_id=topic.id).delete()
        except Exception:
            pass
        try:
            Milestone.query.filter_by(topic_id=topic.id).delete()
        except Exception:
            pass
        try:
            Submission.query.filter_by(topic_id=topic.id).delete()
        except Exception:
            pass
        
        # 3. Xóa các tin nhắn chat trong nhóm & các tin nhắn lời mời liên quan tới nhóm này
        if group:
            try:
                Message.query.filter_by(group_id=group.id).delete()
                # Xóa các lời mời liên quan group_id
                invitations = Message.query.filter(Message.message_type == 'invitation').all()
                for inv in invitations:
                    if inv.meta_data and (f'"group_id": {group.id}' in inv.meta_data or f'"group_id":{group.id}' in inv.meta_data):
                        db.session.delete(inv)
            except Exception:
                pass
            
            # 4. Xóa thành viên nhóm
            GroupMember.query.filter_by(group_id=group.id).delete()

        # 5. Xóa topic
        db.session.delete(topic)
        
        # 6. Xóa nhóm nghiên cứu (để trưởng nhóm có thể tạo nhóm/mời thành viên mới)
        if group:
            db.session.delete(group)
        
        db.session.commit()
        return jsonify({'message': 'Hủy đăng ký đề tài thành công'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@topics_bp.route('/<int:topic_id>', methods=['PUT'])
def update_topic(topic_id):
    """
    Update topic details (title, description, mentor_id)
    """
    from flask import session
    if session.get('role') not in ['faculty', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    try:
        topic = Topic.query.get(topic_id)
        if not topic:
            return jsonify({'error': 'Topic not found'}), 404
            
        if 'title' in data:
            topic.title = data['title']
        if 'description' in data:
            topic.description = data['description']
        if 'mentor_id' in data:
            topic.mentor_id = data['mentor_id'] if data['mentor_id'] else None
        if 'batch_id' in data:
            topic.batch_id = data['batch_id'] if data['batch_id'] else None
        if 'status' in data:
            topic.status = data['status']
            
        db.session.commit()
        return jsonify({'message': 'Topic updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
@topics_bp.route('/<int:topic_id>/quota-info', methods=['GET'])
def get_topic_mentor_quota_info(topic_id):
    """
    Get current mentor quota and list of available replacement mentors
    """
    try:
        topic = Topic.query.get(topic_id)
        if not topic:
            return jsonify({'error': 'Topic not found'}), 404
            
        from models import User
        mentor = User.query.get(topic.mentor_id) if topic.mentor_id else None
        
        current_count = 0
        if mentor:
            current_count = Topic.query.filter(
                Topic.mentor_id == mentor.id,
                Topic.status == 'approved'
            ).count()
            
        max_allowed = 3
        is_exceeded = (current_count >= max_allowed)
        
        from sqlalchemy import func
        all_lecturers = User.query.filter(func.lower(User.role) == 'lecturer').all()
        available_mentors = []
        for m in all_lecturers:
            m_count = Topic.query.filter(
                Topic.mentor_id == m.id,
                Topic.status == 'approved'
            ).count()
            available_mentors.append({
                'id': m.id,
                'name': m.full_name,
                'faculty': m.faculty or 'Khoa CNTT',
                'email': m.email or '',
                'active_groups': m_count,
                'max_allowed': max_allowed,
                'is_available': m_count < max_allowed
            })
            
        return jsonify({
            'current_mentor': {
                'id': mentor.id if mentor else None,
                'name': mentor.full_name if mentor else 'Chưa phân công',
                'faculty': mentor.faculty if mentor else '',
                'active_groups': current_count,
                'max_allowed': max_allowed,
                'is_exceeded': is_exceeded
            },
            'available_mentors': available_mentors
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@topics_bp.route('/<int:topic_id>/faculty-approve', methods=['POST'])
def faculty_approve_topic(topic_id):
    """
    Faculty approves a topic, optionally reassigning mentor if quota exceeded
    """
    from flask import session, request
    if session.get('role') not in ['faculty', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
        
    try:
        topic = Topic.query.get(topic_id)
        if not topic:
            return jsonify({'error': 'Topic not found'}), 404
            
        data = request.get_json(silent=True) or {}
        new_mentor_id = data.get('new_mentor_id')
        change_reason = data.get('change_reason', '').strip()
        
        from models import User, Group, GroupMember, Notification, Message
        from email_utils import send_email_async
        
        reassigned = False
        old_mentor = None
        new_mentor = None
        
        if new_mentor_id and int(new_mentor_id) != topic.mentor_id:
            old_mentor = User.query.get(topic.mentor_id)
            new_mentor = User.query.get(int(new_mentor_id))
            if new_mentor:
                topic.mentor_id = new_mentor.id
                reassigned = True
                
        topic.status = 'approved'
        if topic.group_id:
            group = Group.query.get(topic.group_id)
            if group:
                group.status = 'approved'
                group.mentor_id = topic.mentor_id
                # Đưa tất cả thành viên vào nhóm chính thức
                GroupMember.query.filter_by(group_id=group.id).update({'status': 'accepted'})
                
        db.session.commit()
        
        # 1. Send emails and notifications
        assigned_mentor = new_mentor if reassigned else User.query.get(topic.mentor_id)
        
        if reassigned and old_mentor and old_mentor.email:
            # Email to Old Mentor explaining reassignment
            html_content_old_mentor = f"""
            <div style='font-family: Arial, sans-serif; padding: 20px; color: #333;'>
                <h2 style='color: #f59e0b;'>Thông báo Điều chuyển Giảng viên Hướng dẫn NCKH</h2>
                <p>Kính gửi Thầy/Cô <strong>{old_mentor.full_name}</strong>,</p>
                <p>Khoa xin trân trọng thông báo về đề tài NCKH <strong>{topic.title}</strong> của nhóm sinh viên đăng ký trước đó.</p>
                <div style='background: #fffbeb; padding: 12px; border-left: 4px solid #f59e0b; margin: 15px 0;'>
                    <p style='margin: 0;'><strong>Lý do điều chuyển từ Khoa:</strong></p>
                    <p style='margin: 5px 0 0 0;'>Do Thầy/Cô đã đạt định mức tối đa số lượng nhóm hướng dẫn trong đợt này (tối đa 3 nhóm), Khoa đã chủ động phân công Thầy/Cô <strong>{new_mentor.full_name}</strong> tiếp nhận hướng dẫn đề tài này.</p>
                    {f"<p style='margin: 5px 0 0 0;'><em>Ghi chú thêm:</em> {change_reason}</p>" if change_reason else ""}
                </div>
                <p>Khoa trân trọng cảm ơn sự đồng hành và đóng góp của Thầy/Cô!</p>
                <br><p style='color: #666; font-size: 12px;'>Trân trọng,<br>Hội đồng Khoa/Viện - HOU S-RIMS</p>
            </div>
            """
            send_email_async(old_mentor.email, "[HOU S-RIMS] Thông báo điều chuyển Giảng viên hướng dẫn NCKH", f"Thông báo điều chuyển hướng dẫn đề tài {topic.title}", html_content_old_mentor)
            
        if assigned_mentor:
            link_mentor = f"/lecturer/progress"
            notif_content = f"""
            <p>Xin chào <strong>{assigned_mentor.full_name}</strong>,</p>
            <p>Đề tài NCKH <strong>{topic.title}</strong> đã được Khoa chính thức phê duyệt và phân công bạn hướng dẫn.</p>
            <a href='{link_mentor}' class='btn btn-success rounded-pill btn-sm mt-2'>Xem Tiến độ</a>
            """
            new_notif = Notification(user_id=assigned_mentor.id, content=notif_content)
            db.session.add(new_notif)
            
            if assigned_mentor.email:
                email_link_mentor = f"http://127.0.0.1:5000/lecturer/progress"
                html_content_mentor = f"""
                <div style='font-family: Arial, sans-serif; padding: 20px; color: #333;'>
                    <h2 style='color: #10b981;'>Khoa đã Phê duyệt & Phân công Hướng dẫn Đề tài NCKH</h2>
                    <p>Xin chào <strong>{assigned_mentor.full_name}</strong>,</p>
                    <p>Đề tài NCKH <strong>{topic.title}</strong> đã được Khoa chính thức phê duyệt và phân công bạn hướng dẫn.</p>
                    {f"<p style='color: #d97706;'><strong>Ghi chú phân công từ Khoa:</strong> {change_reason}</p>" if reassigned and change_reason else ""}
                    <p>Bạn đã có thể truy cập Hệ thống để vào phòng Chatgroup chung, thảo luận cùng sinh viên và thiết lập tiến độ nghiên cứu.</p>
                    <a href='{email_link_mentor}' style='display: inline-block; padding: 10px 20px; background-color: #10b981; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px;'>Xem Tiến độ & Chat</a>
                    <br><br><p style='color: #666; font-size: 12px;'>Trân trọng,<br>Hệ thống HOU S-RIMS</p>
                </div>
                """
                send_email_async(assigned_mentor.email, f"[HOU S-RIMS] Khoa phân công hướng dẫn đề tài", f"Đề tài {topic.title} đã được phê duyệt", html_content_mentor)

        # Notify Students
        members = GroupMember.query.filter_by(group_id=topic.group_id).all()
        for member in members:
            student = User.query.get(member.student_id)
            if student:
                link_student = f"/student#s-chat"
                reassign_note = f"<p><em>(Khoa đã phân công Thầy/Cô <strong>{assigned_mentor.full_name}</strong> làm Giảng viên hướng dẫn thay thế do GV trước đã đủ số nhóm. Lý do: {change_reason})</em></p>" if reassigned and assigned_mentor else ""
                notif_content = f"""
                <p>Xin chào <strong>{student.full_name}</strong>,</p>
                <p>Đề tài NCKH <strong>{topic.title}</strong> của nhóm bạn đã được Khoa chính thức phê duyệt!</p>
                {reassign_note}
                <a href='{link_student}' onclick='if(window.Swal) Swal.close(); window.location.href=\"{link_student}\"; window.location.reload();' class='btn btn-success rounded-pill btn-sm mt-2'>Vào phòng Chat Nhóm</a>
                """
                new_notif = Notification(user_id=student.id, content=notif_content)
                db.session.add(new_notif)
                
                if student.email:
                    email_link_student = f"http://127.0.0.1:5000/student/chat"
                    html_content_student = f"""
                    <div style='font-family: Arial, sans-serif; padding: 20px; color: #333;'>
                        <h2 style='color: #10b981;'>Đề tài NCKH của bạn đã được Khoa phê duyệt</h2>
                        <p>Xin chào <strong>{student.full_name}</strong>,</p>
                        <p>Đề tài NCKH <strong>{topic.title}</strong> của nhóm bạn đã được Khoa chính thức phê duyệt.</p>
                        <p><strong>Giảng viên Hướng dẫn:</strong> {assigned_mentor.full_name if assigned_mentor else 'Chưa phân công'}</p>
                        {f"<div style='background: #fef3c7; padding: 10px; border-left: 4px solid #f59e0b; margin: 10px 0;'><p style='margin:0;'><strong>Lưu ý điều chuyển từ Khoa:</strong> Do Giảng viên ban đầu đã đủ số lượng nhóm tối đa, Khoa đã điều chuyển sang Thầy/Cô {assigned_mentor.full_name}.<br><em>Lý do:</em> {change_reason}</p></div>" if reassigned and assigned_mentor else ""}
                        <p>Tất cả thành viên và Giảng viên hướng dẫn đã được kết nối vào phòng Chatgroup chung để cùng thảo luận và cập nhật lại tên đề tài.</p>
                        <a href='{email_link_student}' style='display: inline-block; padding: 10px 20px; background-color: #10b981; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px;'>Vào Chat Nhóm & Thảo luận</a>
                        <br><br><p style='color: #666; font-size: 12px;'>Trân trọng,<br>Hệ thống HOU S-RIMS</p>
                    </div>
                    """
                    send_email_async(student.email, f"[HOU S-RIMS] Đề tài NCKH được phê duyệt", f"Đề tài {topic.title} đã được phê duyệt", html_content_student)

        # 2. Add welcome message into group chat
        if topic.group_id and assigned_mentor:
            sys_msg = Message(
                group_id=topic.group_id,
                sender_id=assigned_mentor.id,
                receiver_id=None,
                content=f"🎉 **Đề tài đã được Khoa phê duyệt chính thức!**\nGiảng viên hướng dẫn: **{assigned_mentor.full_name}**.\nTất cả thành viên và Thầy/Cô có thể trao đổi thảo luận tại đây và cập nhật lại tên đề tài NCKH khi đã thống nhất ý tưởng.",
                message_type='text'
            )
            db.session.add(sys_msg)

        db.session.commit()
        return jsonify({'message': 'Topic approved by faculty', 'reassigned': reassigned}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@topics_bp.route('/<int:topic_id>/update-title', methods=['POST'])
def update_topic_title(topic_id):
    """
    Update topic title and group name
    """
    from flask import session
    user_id = session.get('user_id')
    user_role = session.get('role')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({'error': 'Vui lòng nhập tên đề tài'}), 400
        
    new_title = data['title'].strip()
    new_desc = data.get('description', '').strip()
    
    try:
        from models import Group, GroupMember, Message, User
        topic = Topic.query.get(topic_id)
        if not topic and data.get('group_id'):
            topic = Topic.query.filter_by(group_id=data['group_id']).first()
        if not topic:
            return jsonify({'error': 'Topic not found'}), 404
            
        group = Group.query.get(topic.group_id) if topic.group_id else None
        
        # Check permissions: student in group, leader, mentor, or faculty/admin
        allowed = False
        if user_role in ['faculty', 'admin', 'lecturer']:
            allowed = True
        elif group:
            if group.leader_id == user_id:
                allowed = True
            elif GroupMember.query.filter_by(group_id=group.id, student_id=user_id).first():
                allowed = True
        if not allowed:
            return jsonify({'error': 'Bạn không có quyền cập nhật tên đề tài này'}), 403
            
        topic.title = new_title
        if new_desc:
            topic.description = new_desc
            
        if group:
            group.name = f"Nhóm {new_title}"
            
        # Post system message into group chat
        from models import Message, User
        sender = User.query.get(user_id)
        sender_name = sender.full_name if sender else 'Thành viên'
        sys_msg = Message(
            group_id=topic.group_id,
            sender_id=user_id,
            receiver_id=None,
            content=f"📝 **{sender_name}** đã cập nhật tên đề tài nghiên cứu thành: **{new_title}**",
            message_type='text'
        )
        db.session.add(sys_msg)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Cập nhật tên đề tài thành công',
            'topic': {
                'id': topic.id,
                'title': topic.title,
                'description': topic.description
            },
            'group_name': group.name if group else None
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@topics_bp.route('/<int:topic_id>/faculty-reject', methods=['POST'])
def faculty_reject_topic(topic_id):
    """
    Faculty rejects a topic
    """
    from flask import session, request
    if session.get('role') not in ['faculty', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
        
    try:
        topic = Topic.query.get(topic_id)
        if not topic:
            return jsonify({'error': 'Topic not found'}), 404
            
        data = request.get_json()
        reason = data.get('note', 'Không phù hợp với tiêu chí của Khoa.')
            
        topic.status = 'rejected'
        db.session.commit()
        
        from email_utils import send_email_async
        from models import User, GroupMember, Notification
        
        # Notify Mentor
        mentor = User.query.get(topic.mentor_id)
        if mentor:
            notif_content = f"""
            <p>Xin chào <strong>{mentor.full_name}</strong>,</p>
            <p>Đề tài NCKH <strong>{topic.title}</strong> do bạn hướng dẫn đã <strong>bị từ chối</strong> bởi Khoa.</p>
            <p>Lý do: <em>{reason}</em></p>
            """
            new_notif = Notification(user_id=mentor.id, content=notif_content)
            db.session.add(new_notif)
            
            if mentor.email:
                html_content_mentor = f"""
                <div style='font-family: Arial, sans-serif; padding: 20px; color: #333;'>
                    <h2 style='color: #ef4444;'>Khoa Từ chối Đề tài NCKH</h2>
                    <p>Xin chào <strong>{mentor.full_name}</strong>,</p>
                    <p>Đề tài NCKH <strong>{topic.title}</strong> do bạn hướng dẫn đã <strong>bị từ chối</strong> bởi Khoa.</p>
                    <p><strong>Lý do:</strong> <em>{reason}</em></p>
                    <br><br><p style='color: #666; font-size: 12px;'>Trân trọng,<br>Hệ thống HOU S-RIMS</p>
                </div>
                """
                send_email_async(mentor.email, f"[HOU S-RIMS] Đề tài bị từ chối", f"Đề tài {topic.title} đã bị từ chối", html_content_mentor)
            
        # Notify Students
        members = GroupMember.query.filter_by(group_id=topic.group_id, status='accepted').all()
        for member in members:
            student = User.query.get(member.student_id)
            if student:
                notif_content = f"""
                <p>Xin chào <strong>{student.full_name}</strong>,</p>
                <p>Đề tài NCKH <strong>{topic.title}</strong> của nhóm bạn đã <strong>bị từ chối</strong> bởi Khoa.</p>
                <p>Lý do: <em>{reason}</em></p>
                <p>Vui lòng trao đổi với giảng viên hướng dẫn để chỉnh sửa đề cương và nộp lại.</p>
                """
                new_notif = Notification(user_id=student.id, content=notif_content)
                db.session.add(new_notif)
                
                if student.email:
                    html_content_student = f"""
                    <div style='font-family: Arial, sans-serif; padding: 20px; color: #333;'>
                        <h2 style='color: #ef4444;'>Đề tài NCKH bị từ chối</h2>
                        <p>Xin chào <strong>{student.full_name}</strong>,</p>
                        <p>Đề tài NCKH <strong>{topic.title}</strong> của nhóm bạn đã <strong>bị từ chối</strong> bởi Khoa.</p>
                        <p><strong>Lý do:</strong> <em>{reason}</em></p>
                        <p>Vui lòng trao đổi với giảng viên hướng dẫn để điều chỉnh lại hướng nghiên cứu.</p>
                        <br><br><p style='color: #666; font-size: 12px;'>Trân trọng,<br>Hệ thống HOU S-RIMS</p>
                    </div>
                    """
                    send_email_async(student.email, f"[HOU S-RIMS] Đề tài bị từ chối", f"Đề tài {topic.title} bị từ chối", html_content_student)
                
        db.session.commit()
        return jsonify({'message': 'Topic rejected by faculty'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@topics_bp.route('/<int:topic_id>/approve', methods=['POST'])
def approve_topic(topic_id):
    """
    Approve or reject a topic
    ---
    tags:
      - Topics
    parameters:
      - in: path
        name: topic_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            status:
              type: string
              example: approved
    responses:
      200:
        description: Topic status updated
      400:
        description: Missing status
      404:
        description: Topic not found
    """
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': 'Missing status'}), 400
        
    try:
        topic = Topic.query.get(topic_id)
        if not topic:
            return jsonify({'error': 'Topic not found'}), 404
        # Only allow specific statuses
        if data['status'] not in ['faculty_pending', 'approved', 'rejected']:
            return jsonify({'error': 'Invalid status'}), 400
            
        topic.status = data['status']
        if topic.status == 'approved' and topic.group_id:
            from models import Group, GroupMember
            group = Group.query.get(topic.group_id)
            if group:
                group.status = 'approved'
                if topic.mentor_id:
                    group.mentor_id = topic.mentor_id
                # Đưa tất cả thành viên vào nhóm chính thức
                GroupMember.query.filter_by(group_id=group.id).update({'status': 'accepted'})
        db.session.commit()
        
        from email_utils import send_email_async
        from models import User, GroupMember, Notification
        
        if topic.status == 'faculty_pending':
            # Lecturer approved it, send email to students
            note = (data.get('note') or '').strip()
            note_box = f"<div style='background: #f0fdf4; border-left: 4px solid #22c55e; padding: 10px 14px; margin: 10px 0; border-radius: 6px; color: #166534; font-size: 13px; line-height: 1.6;'><strong>Ghi chú & Định hướng từ Giảng viên:</strong><div class='mt-1 rich-content-display'>{note}</div></div>" if note else ""

            members = GroupMember.query.filter_by(group_id=topic.group_id, status='accepted').all()
            for member in members:
                student = User.query.get(member.student_id)
                if student:
                    link_student = f"/student#s-group"
                    notif_content = f"""
                    <p>Xin chào <strong>{student.full_name}</strong>,</p>
                    <p>Giảng viên hướng dẫn vừa đồng ý tham gia đề tài NCKH: <strong>{topic.title}</strong> của nhóm bạn.</p>
                    {note_box}
                    <p>Hiện tại, đề tài đang chờ Khoa/Viện phê duyệt chính thức.</p>
                    <a href='{link_student}' class='btn btn-primary rounded-pill btn-sm mt-2'>Xem Tiến độ</a>
                    """
                    new_notif = Notification(user_id=student.id, content=notif_content)
                    db.session.add(new_notif)
                    
                    if student.email:
                        email_link_student = f"http://127.0.0.1:5000/student/progress"
                        html_content_student = f"""
                        <div style='font-family: Arial, sans-serif; padding: 20px; color: #333;'>
                            <h2 style='color: #3b82f6;'>Giảng viên đã đồng ý Hướng dẫn</h2>
                            <p>Xin chào <strong>{student.full_name}</strong>,</p>
                            <p>Giảng viên hướng dẫn vừa đồng ý tham gia đề tài NCKH: <strong>{topic.title}</strong> của nhóm bạn.</p>
                            {note_box}
                            <p>Hiện tại, đề tài đang chờ Khoa/Viện phê duyệt chính thức. Vui lòng theo dõi trạng thái thường xuyên.</p>
                            <a href='{email_link_student}' style='display: inline-block; padding: 10px 20px; background-color: #3b82f6; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px;'>Xem Tiến độ</a>
                            <br><br><p style='color: #666; font-size: 12px;'>Trân trọng,<br>Hệ thống HOU S-RIMS</p>
                        </div>
                        """
                        send_email_async(student.email, f"[HOU S-RIMS] Giảng viên đồng ý hướng dẫn", f"Giảng viên đồng ý hướng dẫn đề tài {topic.title}", html_content_student)
            
            # Thông báo cho Ban Chủ nhiệm Khoa (role: faculty)
            desc_fac_html = f"<div style='margin-top: 8px; padding: 10px; background-color: #f8fafc; border-left: 4px solid #f59e0b; border-radius: 4px; font-size: 13px; color: #334155;'><strong>Mô tả / Ý tưởng nghiên cứu:</strong><br>{topic.description}</div>" if topic.description else ""
            faculty_users = User.query.filter_by(role='faculty').all()
            for fac in faculty_users:
                notif_fac_content = f"""
                <p><strong>Đề tài mới chờ Khoa phê duyệt</strong></p>
                <p>Đề tài <strong>{topic.title}</strong> do Giảng viên hướng dẫn vừa đồng ý phê duyệt và đang chờ Hội đồng Khoa thẩm định.</p>
                {desc_fac_html}
                <a href='/faculty/topics' class='btn btn-warning rounded-pill btn-sm mt-2'>Xem & Phê duyệt</a>
                """
                db.session.add(Notification(user_id=fac.id, content=notif_fac_content))
                if fac.email:
                    email_fac_content = f"""
                    <div style='font-family: Arial, sans-serif; padding: 20px; color: #333;'>
                        <h2 style='color: #f59e0b;'>Đề tài mới chờ Khoa phê duyệt</h2>
                        <p>Xin chào <strong>{fac.full_name}</strong>,</p>
                        <p>Đề tài <strong>{topic.title}</strong> đã được Giảng viên hướng dẫn đồng ý và chuyển lên chờ Hội đồng Khoa thẩm định.</p>
                        {desc_fac_html}
                        <a href='http://127.0.0.1:5000/faculty/topics' style='display: inline-block; padding: 10px 20px; background-color: #f59e0b; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px;'>Xem & Phê duyệt</a>
                        <br><br><p style='color: #666; font-size: 12px;'>Trân trọng,<br>Hệ thống HOU S-RIMS</p>
                    </div>
                    """
                    send_email_async(fac.email, f"[HOU S-RIMS] Đề tài mới chờ Khoa phê duyệt: {topic.title}", f"Đề tài {topic.title} chờ duyệt", email_fac_content)
            db.session.commit()
                    
        elif topic.status == 'approved':
            # Faculty approved it, send email to mentor and students
            mentor = User.query.get(topic.mentor_id)
            if mentor:
                link_mentor = f"/lecturer/progress"
                notif_content = f"""
                <p>Xin chào <strong>{mentor.full_name}</strong>,</p>
                <p>Đề tài NCKH <strong>{topic.title}</strong> do bạn hướng dẫn đã được Khoa chính thức phê duyệt.</p>
                <a href='{link_mentor}' class='btn btn-success rounded-pill btn-sm mt-2'>Xem Tiến độ</a>
                """
                new_notif = Notification(user_id=mentor.id, content=notif_content)
                db.session.add(new_notif)
                
                if mentor.email:
                    email_link_mentor = f"http://127.0.0.1:5000/lecturer/progress"
                    html_content_mentor = f"""
                    <div style='font-family: Arial, sans-serif; padding: 20px; color: #333;'>
                        <h2 style='color: #10b981;'>Khoa đã Phê duyệt Đề tài NCKH</h2>
                        <p>Xin chào <strong>{mentor.full_name}</strong>,</p>
                        <p>Đề tài NCKH <strong>{topic.title}</strong> do bạn hướng dẫn đã được Khoa chính thức phê duyệt.</p>
                        <p>Bạn đã có thể truy cập Hệ thống để thiết lập cột mốc tiến độ và thảo luận với sinh viên.</p>
                        <a href='{email_link_mentor}' style='display: inline-block; padding: 10px 20px; background-color: #10b981; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px;'>Xem Tiến độ</a>
                        <br><br><p style='color: #666; font-size: 12px;'>Trân trọng,<br>Hệ thống HOU S-RIMS</p>
                    </div>
                    """
                    send_email_async(mentor.email, f"[HOU S-RIMS] Đề tài được phê duyệt", f"Đề tài {topic.title} đã được phê duyệt", html_content_mentor)
                
            members = GroupMember.query.filter_by(group_id=topic.group_id, status='accepted').all()
            for member in members:
                student = User.query.get(member.student_id)
                if student:
                    link_student = f"/student#s-group"
                    notif_content = f"""
                    <p>Xin chào <strong>{student.full_name}</strong>,</p>
                    <p>Đề tài NCKH <strong>{topic.title}</strong> của nhóm bạn đã được Khoa chính thức phê duyệt.</p>
                    <a href='{link_student}' onclick='if(window.Swal) Swal.close(); window.location.href=\"{link_student}\"; window.location.reload();' class='btn btn-success rounded-pill btn-sm mt-2'>Xem Tiến độ & Nhóm</a>
                    """
                    new_notif = Notification(user_id=student.id, content=notif_content)
                    db.session.add(new_notif)
                    
                    if student.email:
                        email_link_student = f"http://127.0.0.1:5000/student/progress"
                        html_content_student = f"""
                        <div style='font-family: Arial, sans-serif; padding: 20px; color: #333;'>
                            <h2 style='color: #10b981;'>Đề tài NCKH của bạn đã được phê duyệt</h2>
                            <p>Xin chào <strong>{student.full_name}</strong>,</p>
                            <p>Đề tài NCKH <strong>{topic.title}</strong> của nhóm bạn đã được Khoa chính thức phê duyệt.</p>
                            <p>Chúc nhóm bạn hoàn thành xuất sắc dự án nghiên cứu!</p>
                            <a href='{email_link_student}' style='display: inline-block; padding: 10px 20px; background-color: #10b981; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px;'>Xem Tiến độ</a>
                            <br><br><p style='color: #666; font-size: 12px;'>Trân trọng,<br>Hệ thống HOU S-RIMS</p>
                        </div>
                        """
                        send_email_async(student.email, f"[HOU S-RIMS] Đề tài được phê duyệt", f"Đề tài {topic.title} đã được phê duyệt", html_content_student)
                        
        elif topic.status == 'rejected':
            # Lecturer/Faculty rejected it: send in-app notification & email to students so they can pick a new mentor
            reason = data.get('reason', '').strip()
            mentor = User.query.get(topic.mentor_id) if topic.mentor_id else None
            mentor_name = mentor.full_name if mentor else 'Giảng viên'
            
            from models import TopicRegistration
            TopicRegistration.query.filter_by(topic_id=topic.id).update({'status': 'rejected'})
            
            members = GroupMember.query.filter_by(group_id=topic.group_id).all()
            for member in members:
                student = User.query.get(member.student_id)
                if student:
                    reason_box = f"<div style='background: #fef2f2; border-left: 4px solid #ef4444; padding: 10px 14px; margin: 10px 0; border-radius: 4px; color: #991b1b; font-size: 13px;'><strong>Lý do từ chối:</strong> {reason}</div>" if reason else ""
                    notif_content = f"""
                    <p><strong>Giảng viên đã từ chối hướng dẫn đề tài NCKH</strong></p>
                    <p>Giảng viên <strong>{mentor_name}</strong> đã từ chối yêu cầu hướng dẫn đề tài: <strong>{topic.title}</strong> của nhóm bạn.</p>
                    {reason_box}
                    <p>Nhóm bạn không cần đăng ký lại từ đầu mà có thể <strong>chọn lại Giảng viên hướng dẫn khác</strong> ngay trên hệ thống.</p>
                    <a href='/student#s-register' class='btn btn-warning rounded-pill btn-sm mt-1'>Chọn giảng viên mới</a>
                    """
                    new_notif = Notification(user_id=student.id, content=notif_content)
                    db.session.add(new_notif)
                    
                    if student.email:
                        email_reason = f"<div style='background: #fef2f2; border-left: 4px solid #ef4444; padding: 12px 16px; margin: 14px 0; border-radius: 6px; color: #991b1b; font-size: 14px;'><strong>Lý do từ chối từ Giảng viên:</strong><br>{reason}</div>" if reason else ""
                        email_content = f"""
                        <div style='font-family: Arial, sans-serif; padding: 20px; color: #333;'>
                            <h2 style='color: #ef4444;'>Giảng viên từ chối hướng dẫn đề tài NCKH</h2>
                            <p>Xin chào <strong>{student.full_name}</strong>,</p>
                            <p>Giảng viên <strong>{mentor_name}</strong> đã từ chối yêu cầu hướng dẫn cho đề tài NCKH: <strong>{topic.title}</strong> của nhóm bạn.</p>
                            {email_reason}
                            <p>Nhóm bạn không cần phải đăng ký lại từ đầu. Bạn có thể đăng nhập vào hệ thống để <strong>chọn lại một Giảng viên hướng dẫn khác</strong> phù hợp hơn.</p>
                            <a href='http://127.0.0.1:5000/student#s-register' style='display: inline-block; padding: 10px 20px; background-color: #f59e0b; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px; font-weight: bold;'>Chọn Giảng viên mới</a>
                            <br><br><p style='color: #666; font-size: 12px;'>Trân trọng,<br>Hệ thống HOU S-RIMS</p>
                        </div>
                        """
                        send_email_async(student.email, f"[HOU S-RIMS] Giảng viên từ chối hướng dẫn đề tài: {topic.title}", f"Giảng viên từ chối đề tài {topic.title}", email_content)

        db.session.commit()
        return jsonify({'message': 'Topic status updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@topics_bp.route('/<int:topic_id>/change-mentor', methods=['POST'])
def change_mentor(topic_id):
    """
    Allow student (group leader/members) to select a new mentor after rejection or update
    """
    from flask import session
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    from models import Topic, Group, GroupMember, User, Notification, TopicRegistration
    topic = Topic.query.get(topic_id)
    if not topic:
        return jsonify({'error': 'Không tìm thấy đề tài'}), 404

    group = Group.query.get(topic.group_id) if topic.group_id else None
    if not group:
        return jsonify({'error': 'Không tìm thấy nhóm nghiên cứu'}), 404

    is_leader = (group.leader_id == user_id)
    is_member = GroupMember.query.filter_by(group_id=group.id, student_id=user_id, status='accepted').first() is not None
    if not (is_leader or is_member):
        return jsonify({'error': 'Bạn không có quyền thay đổi giảng viên cho đề tài này'}), 403

    if topic.status not in ['rejected', 'pending', 'waiting_for_members']:
        return jsonify({'error': 'Chỉ có thể đổi giảng viên khi đề tài đang chờ duyệt hoặc bị từ chối'}), 400

    data = request.get_json() or {}
    new_mentor_id = data.get('mentor_id')
    if not new_mentor_id:
        return jsonify({'error': 'Vui lòng chọn Giảng viên hướng dẫn mới'}), 400

    new_mentor = User.query.get(int(new_mentor_id))
    if not new_mentor or (new_mentor.role or '').lower() != 'lecturer':
        return jsonify({'error': 'Giảng viên đã chọn không hợp lệ'}), 400

    try:
        # Cập nhật thông tin mentor và trạng thái đề tài
        topic.mentor_id = new_mentor.id
        topic.status = 'pending' # Đưa đề tài trở lại ĐANG CHỜ GV DUYỆT
        group.mentor_id = new_mentor.id
        group.status = 'pending_mentor'

        # Cập nhật topic_registrations
        reg = TopicRegistration.query.filter_by(topic_id=topic.id).first()
        if reg:
            reg.mentor_id = new_mentor.id
            reg.status = 'pending'

        # Gửi thông báo và email cho Giảng viên mới
        link = f"/lecturer/approve"
        desc_html = (
            f"<div style='background: #f8fafc; border-left: 4px solid #4f46e5; padding: 12px 16px; margin: 12px 0; border-radius: 6px; border: 1px solid #e2e8f0;'>"
            f"<strong style='color: #4338ca; display: block; margin-bottom: 6px;'><i class='fa-solid fa-align-left me-1'></i> Mô tả đề tài / Ý tưởng từ sinh viên:</strong>"
            f"<div class='rich-content-display' style='margin: 0; font-size: 13px; color: #334155; line-height: 1.6;'>{topic.description or ''}</div>"
            f"</div>"
        ) if topic.description else ""

        html_content = (
            f"<p>Xin chào <strong>{new_mentor.full_name}</strong>,</p>"
            f"<p>Nhóm sinh viên <strong>{group.name}</strong> vừa gửi yêu cầu nhờ bạn hướng dẫn đề tài NCKH: <strong>{topic.title}</strong>.</p>"
            f"{desc_html}"
            f"<a href='{link}' class='btn btn-primary rounded-pill btn-sm mt-2'>Phê duyệt Đề tài</a>"
        )
        new_notif = Notification(user_id=new_mentor.id, content=html_content)
        db.session.add(new_notif)

        from email_utils import send_email_async
        if new_mentor.email:
            email_desc_html = (
                f"<div style='background: #f1f5f9; border-left: 4px solid #4f46e5; padding: 14px 18px; margin: 14px 0; border-radius: 6px;'>"
                f"<strong style='color: #312e81; display: block; margin-bottom: 8px;'>Mô tả đề tài / Ý tưởng nghiên cứu từ sinh viên:</strong>"
                f"<div class='rich-content-display' style='margin: 0; font-size: 14px; color: #1e293b; line-height: 1.6;'>{topic.description or ''}</div>"
                f"</div>"
            ) if topic.description else ""

            email_html = (
                f"<div style='font-family: Arial, sans-serif; padding: 20px; color: #333;'>"
                f"<h2 style='color: #4f46e5;'>Yêu cầu Hướng dẫn Đề tài NCKH</h2>"
                f"<p>Xin chào <strong>{new_mentor.full_name}</strong>,</p>"
                f"<p>Nhóm sinh viên <strong>{group.name}</strong> vừa gửi yêu cầu nhờ bạn hướng dẫn đề tài NCKH: <strong>{topic.title}</strong>.</p>"
                f"{email_desc_html}"
                f"<p>Vui lòng đăng nhập hệ thống để xem chi tiết và Quyết định Phê duyệt / Từ chối.</p>"
                f"<a href='http://127.0.0.1:5000/lecturer/approve' style='display: inline-block; padding: 10px 20px; background-color: #4f46e5; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px;'>Phê duyệt Đề tài</a>"
                f"<br><br><p style='color: #666; font-size: 12px;'>Trân trọng,<br>Hệ thống HOU S-RIMS</p>"
                f"</div>"
            )
            send_email_async(new_mentor.email, f"[HOU S-RIMS] Yêu cầu Hướng dẫn Đề tài NCKH", f"Yêu cầu hướng dẫn đề tài {topic.title}", email_html)

        # Gửi thông báo cho toàn bộ thành viên nhóm
        for gm in group.members:
            st_notif = Notification(
                user_id=gm.student_id,
                content=f"<p>Đề tài <strong>{topic.title}</strong> đã được gửi yêu cầu hướng dẫn tới Giảng viên <strong>{new_mentor.full_name}</strong>. Đang chờ Thầy/Cô phản hồi.</p>"
            )
            db.session.add(st_notif)

        db.session.commit()

        # Build response topic object for live UI update
        return jsonify({
            'message': f'Đã gửi yêu cầu hướng dẫn thành công tới Giảng viên {new_mentor.full_name}',
            'topic': {
                'id': topic.id,
                'title': topic.title,
                'status': 'pending',
                'status_label': 'ĐANG CHỜ GV DUYỆT',
                'step': 1,
                'pct': 0,
                'mentor_id': new_mentor.id,
                'mentor_name': new_mentor.full_name,
                'group_id': group.id,
                'group_name': group.name,
                'description': topic.description or '',
                'has_rejected_members': False,
                'rejected_names': [],
                'members': [
                    {
                        'student_id': gm.student_id,
                        'full_name': gm.student.full_name if gm.student else '',
                        'student_code': gm.student.student_id or (gm.student.username if gm.student else ''),
                        'faculty': gm.student.faculty if gm.student else '',
                        'status': gm.status,
                        'is_leader': bool(gm.student_id == group.leader_id)
                    }
                    for gm in group.members
                ]
            }
        }), 200
    except Exception as ex:
        db.session.rollback()
        return jsonify({'error': str(ex)}), 500


