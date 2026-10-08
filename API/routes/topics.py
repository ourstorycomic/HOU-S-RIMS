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
        description: Invalid input or Group already registered
    """
    data = request.get_json()
    if not data or 'name' not in data or 'batch_id' not in data or 'mentor_id' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
        
    try:
        from flask import session
        from models import Group, GroupMember
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401
            
        group_id = data.get('group_id', 0)
        members_list = data.get('members', [])
        
        if group_id == 0:
            # Auto-create group
            new_group = Group(
                name=f"Nhóm ID: {user_id}",
                batch_id=data['batch_id'],
                leader_id=user_id
            )
            db.session.add(new_group)
            db.session.flush() # To get new_group.id
            group_id = new_group.id
            
            # Add leader as accepted member
            new_member = GroupMember(group_id=group_id, student_id=user_id, status='accepted')
            db.session.add(new_member)
            
            # Add other members as pending
            for member_id in members_list:
                if str(member_id) != str(user_id):
                    invited_member = GroupMember(group_id=group_id, student_id=int(member_id), status='pending')
                    db.session.add(invited_member)
                    
                    # Send invitation as a private chat message (type: invitation)
                    from models import Message as Msg
                    import json
                    inviter = User.query.get(user_id)
                    invite_msg = Msg(
                        sender_id=user_id,
                        receiver_id=int(member_id),
                        group_id=None,
                        content=f"📩 Mời bạn tham gia nhóm NCKH cho đề tài **{data['name']}**. Nhấn Đồng ý để xác nhận.",
                        message_type='invitation',
                        meta_data=json.dumps({'invite_group_id': group_id, 'topic_name': data['name']})
                    )
                    db.session.add(invite_msg)
                    
                    from email_utils import send_email_async
                    invited_user = User.query.get(int(member_id))
                    if invited_user and invited_user.email:
                        link = f"http://127.0.0.1:5000/student/chat"
                        html_content = f"""
                        <div style='font-family: Arial, sans-serif; padding: 20px; color: #333;'>
                            <h2 style='color: #4f46e5;'>Lời mời tham gia nhóm NCKH</h2>
                            <p>Xin chào <strong>{invited_user.full_name}</strong>,</p>
                            <p>Bạn vừa nhận được lời mời tham gia nhóm NCKH cho đề tài: <strong>{data['name']}</strong> từ sinh viên {inviter.full_name}.</p>
                            <p>Vui lòng đăng nhập hệ thống và vào mục Chat Cá nhân để Đồng ý hoặc Từ chối lời mời này.</p>
                            <a href='{link}' style='display: inline-block; padding: 10px 20px; background-color: #4f46e5; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px;'>Xem lời mời</a>
                            <br><br><p style='color: #666; font-size: 12px;'>Trân trọng,<br>Hệ thống HOU S-RIMS</p>
                        </div>
                        """
                        send_email_async(invited_user.email, f"[HOU S-RIMS] Lời mời tham gia nhóm NCKH", f"Bạn được mời tham gia đề tài {data['name']}", html_content)
        else:
            # Check if group already has a topic in this batch
            existing_topic = Topic.query.filter_by(group_id=group_id, batch_id=data['batch_id']).first()
            if existing_topic:
                return jsonify({'error': 'Group already registered a topic for this batch'}), 400
            
        # Determine topic status based on pending members
        topic_status = 'pending'
        pending_members = GroupMember.query.filter_by(group_id=group_id, status='pending').first()
        if pending_members or (group_id == 0 and len(members_list) > 0):
            topic_status = 'waiting_for_members'

        new_topic = Topic(
            title=data['name'], # Note: Model uses 'title'
            description=data.get('description', ''),
            batch_id=data['batch_id'],
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
            status='pending'
        )
        db.session.add(registration)
        db.session.commit() # Transaction completed
        
        if topic_status == 'pending':
            from email_utils import send_email_async
            mentor = User.query.get(data['mentor_id'])
            if mentor and mentor.email:
                link = f"http://127.0.0.1:5000/lecturer/approve"
                html_content = f"""
                <div style='font-family: Arial, sans-serif; padding: 20px; color: #333;'>
                    <h2 style='color: #4f46e5;'>Yêu cầu Hướng dẫn Đề tài NCKH</h2>
                    <p>Xin chào <strong>{mentor.full_name}</strong>,</p>
                    <p>Nhóm sinh viên vừa gửi yêu cầu nhờ bạn hướng dẫn đề tài NCKH: <strong>{data['name']}</strong>.</p>
                    <p>Vui lòng đăng nhập hệ thống để xem chi tiết và Quyết định Phê duyệt / Từ chối.</p>
                    <a href='{link}' style='display: inline-block; padding: 10px 20px; background-color: #4f46e5; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px;'>Phê duyệt Đề tài</a>
                    <br><br><p style='color: #666; font-size: 12px;'>Trân trọng,<br>Hệ thống HOU S-RIMS</p>
                </div>
                """
                send_email_async(mentor.email, f"[HOU S-RIMS] Yêu cầu hướng dẫn đề tài", f"Yêu cầu hướng dẫn đề tài {data['name']}", html_content)
                
        return jsonify({'message': 'Topic registered successfully', 'topic_id': new_topic.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@topics_bp.route('/invitation', methods=['POST'])
def handle_invitation():
    from flask import session
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    group_id = data.get('group_id')
    action = data.get('action') # 'accepted' or 'rejected'
    msg_id = data.get('msg_id')
    
    if not group_id or not action:
        return jsonify({'error': 'Missing parameters'}), 400
        
    try:
        from models import GroupMember, Topic, Message
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
                    
        member = GroupMember.query.filter_by(group_id=group_id, student_id=user_id, status='pending').first()
        if not member:
            return jsonify({'error': 'Invitation not found'}), 404
            
        if action == 'rejected':
            member.status = 'rejected'
        else:
            member.status = 'accepted'
            
        # Check if all members accepted
        db.session.flush()
        pending_count = GroupMember.query.filter_by(group_id=group_id, status='pending').count()
        rejected_count = GroupMember.query.filter_by(group_id=group_id, status='rejected').count()
        topic = Topic.query.filter_by(group_id=group_id).first()
        
        if topic and topic.status == 'waiting_for_members':
            if rejected_count > 0:
                pass # Don't advance if someone rejected, leave it for the leader to cancel
            elif pending_count == 0:
                topic.status = 'pending' # Now waiting for lecturer
                
                from email_utils import send_email_async
                from models import User
                mentor = User.query.get(topic.mentor_id)
                if mentor and mentor.email:
                    link = f"http://127.0.0.1:5000/lecturer/approve"
                    html_content = f"""
                    <div style='font-family: Arial, sans-serif; padding: 20px; color: #333;'>
                        <h2 style='color: #4f46e5;'>Yêu cầu Hướng dẫn Đề tài NCKH</h2>
                        <p>Xin chào <strong>{mentor.full_name}</strong>,</p>
                        <p>Nhóm sinh viên vừa gửi yêu cầu nhờ bạn hướng dẫn đề tài NCKH: <strong>{topic.title}</strong>.</p>
                        <p>Vui lòng đăng nhập hệ thống để xem chi tiết và Quyết định Phê duyệt / Từ chối.</p>
                        <a href='{link}' style='display: inline-block; padding: 10px 20px; background-color: #4f46e5; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px;'>Phê duyệt Đề tài</a>
                        <br><br><p style='color: #666; font-size: 12px;'>Trân trọng,<br>Hệ thống HOU S-RIMS</p>
                    </div>
                    """
                    send_email_async(mentor.email, f"[HOU S-RIMS] Yêu cầu hướng dẫn đề tài", f"Yêu cầu hướng dẫn đề tài {topic.title}", html_content)
            
        db.session.commit()
        return jsonify({'message': 'Successfully processed invitation'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@topics_bp.route('/<int:topic_id>', methods=['DELETE'])
def cancel_topic(topic_id):
    from flask import session
    from models import Topic, TopicRegistration, Group, GroupMember
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
        
    try:
        topic = Topic.query.get(topic_id)
        if not topic:
            return jsonify({'error': 'Topic not found'}), 404
            
        group = Group.query.get(topic.group_id)
        if not group or group.leader_id != user_id:
            return jsonify({'error': 'Only the group leader can cancel this registration'}), 403
            
        if topic.status != 'waiting_for_members':
            return jsonify({'error': 'Cannot cancel this topic because it has already progressed'}), 400
            
        # Delete registration
        TopicRegistration.query.filter_by(topic_id=topic.id).delete()
        
        # Delete topic
        db.session.delete(topic)
        
        # Delete group members and group
        GroupMember.query.filter_by(group_id=group.id).delete()
        
        from models import Message
        Message.query.filter_by(group_id=group.id).delete()
        
        db.session.delete(group)
        
        db.session.commit()
        return jsonify({'message': 'Topic and group deleted successfully'}), 200
        
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
@topics_bp.route('/<int:topic_id>/faculty-approve', methods=['POST'])
def faculty_approve_topic(topic_id):
    """
    Faculty approves a topic
    """
    from flask import session
    if session.get('role') not in ['faculty', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
        
    try:
        topic = Topic.query.get(topic_id)
        if not topic:
            return jsonify({'error': 'Topic not found'}), 404
            
        topic.status = 'approved'
        db.session.commit()
        
        from email_utils import send_email_async
        from models import User, GroupMember
        
        # Notify Mentor
        mentor = User.query.get(topic.mentor_id)
        if mentor and mentor.email:
            link_mentor = f"http://127.0.0.1:5000/lecturer/progress"
            html_content_mentor = f"""
            <div style='font-family: Arial, sans-serif; padding: 20px; color: #333;'>
                <h2 style='color: #10b981;'>Khoa đã Phê duyệt Đề tài NCKH</h2>
                <p>Xin chào <strong>{mentor.full_name}</strong>,</p>
                <p>Đề tài NCKH <strong>{topic.title}</strong> do bạn hướng dẫn đã được Khoa chính thức phê duyệt.</p>
                <p>Bạn đã có thể truy cập Hệ thống để thiết lập cột mốc tiến độ và thảo luận với sinh viên.</p>
                <a href='{link_mentor}' style='display: inline-block; padding: 10px 20px; background-color: #10b981; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px;'>Xem Tiến độ</a>
                <br><br><p style='color: #666; font-size: 12px;'>Trân trọng,<br>Hệ thống HOU S-RIMS</p>
            </div>
            """
            send_email_async(mentor.email, f"[HOU S-RIMS] Đề tài được phê duyệt", f"Đề tài {topic.title} đã được phê duyệt", html_content_mentor)
            
        # Notify Students
        members = GroupMember.query.filter_by(group_id=topic.group_id, status='accepted').all()
        for member in members:
            student = User.query.get(member.student_id)
            if student and student.email:
                link_student = f"http://127.0.0.1:5000/student/progress"
                html_content_student = f"""
                <div style='font-family: Arial, sans-serif; padding: 20px; color: #333;'>
                    <h2 style='color: #10b981;'>Đề tài NCKH của bạn đã được phê duyệt</h2>
                    <p>Xin chào <strong>{student.full_name}</strong>,</p>
                    <p>Đề tài NCKH <strong>{topic.title}</strong> của nhóm bạn đã được Khoa chính thức phê duyệt.</p>
                    <p>Chúc nhóm bạn hoàn thành xuất sắc dự án nghiên cứu!</p>
                    <a href='{link_student}' style='display: inline-block; padding: 10px 20px; background-color: #10b981; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px;'>Xem Tiến độ</a>
                    <br><br><p style='color: #666; font-size: 12px;'>Trân trọng,<br>Hệ thống HOU S-RIMS</p>
                </div>
                """
                send_email_async(student.email, f"[HOU S-RIMS] Đề tài được phê duyệt", f"Đề tài {topic.title} đã được phê duyệt", html_content_student)
                
        return jsonify({'message': 'Topic approved by faculty'}), 200
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
        db.session.commit()
        
        from email_utils import send_email_async
        from models import User, GroupMember
        
        if topic.status == 'faculty_pending':
            # Lecturer approved it, send email to students
            members = GroupMember.query.filter_by(group_id=topic.group_id, status='accepted').all()
            for member in members:
                student = User.query.get(member.student_id)
                if student and student.email:
                    link_student = f"http://127.0.0.1:5000/student/progress"
                    html_content_student = f"""
                    <div style='font-family: Arial, sans-serif; padding: 20px; color: #333;'>
                        <h2 style='color: #3b82f6;'>Giảng viên đã đồng ý Hướng dẫn</h2>
                        <p>Xin chào <strong>{student.full_name}</strong>,</p>
                        <p>Giảng viên hướng dẫn vừa đồng ý tham gia đề tài NCKH: <strong>{topic.title}</strong> của nhóm bạn.</p>
                        <p>Hiện tại, đề tài đang chờ Khoa/Viện phê duyệt chính thức. Vui lòng theo dõi trạng thái thường xuyên.</p>
                        <a href='{link_student}' style='display: inline-block; padding: 10px 20px; background-color: #3b82f6; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px;'>Xem Tiến độ</a>
                        <br><br><p style='color: #666; font-size: 12px;'>Trân trọng,<br>Hệ thống HOU S-RIMS</p>
                    </div>
                    """
                    send_email_async(student.email, f"[HOU S-RIMS] Giảng viên đồng ý hướng dẫn", f"Giảng viên đồng ý hướng dẫn đề tài {topic.title}", html_content_student)
                    
        elif topic.status == 'approved':
            # Faculty approved it, send email to mentor and students
            mentor = User.query.get(topic.mentor_id)
            if mentor and mentor.email:
                link_mentor = f"http://127.0.0.1:5000/lecturer/progress"
                html_content_mentor = f"""
                <div style='font-family: Arial, sans-serif; padding: 20px; color: #333;'>
                    <h2 style='color: #10b981;'>Khoa đã Phê duyệt Đề tài NCKH</h2>
                    <p>Xin chào <strong>{mentor.full_name}</strong>,</p>
                    <p>Đề tài NCKH <strong>{topic.title}</strong> do bạn hướng dẫn đã được Khoa chính thức phê duyệt.</p>
                    <p>Bạn đã có thể truy cập Hệ thống để thiết lập cột mốc tiến độ và thảo luận với sinh viên.</p>
                    <a href='{link_mentor}' style='display: inline-block; padding: 10px 20px; background-color: #10b981; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px;'>Xem Tiến độ</a>
                    <br><br><p style='color: #666; font-size: 12px;'>Trân trọng,<br>Hệ thống HOU S-RIMS</p>
                </div>
                """
                send_email_async(mentor.email, f"[HOU S-RIMS] Đề tài được phê duyệt", f"Đề tài {topic.title} đã được phê duyệt", html_content_mentor)
                
            members = GroupMember.query.filter_by(group_id=topic.group_id, status='accepted').all()
            for member in members:
                student = User.query.get(member.student_id)
                if student and student.email:
                    link_student = f"http://127.0.0.1:5000/student/progress"
                    html_content_student = f"""
                    <div style='font-family: Arial, sans-serif; padding: 20px; color: #333;'>
                        <h2 style='color: #10b981;'>Đề tài NCKH của bạn đã được phê duyệt</h2>
                        <p>Xin chào <strong>{student.full_name}</strong>,</p>
                        <p>Đề tài NCKH <strong>{topic.title}</strong> của nhóm bạn đã được Khoa chính thức phê duyệt.</p>
                        <p>Chúc nhóm bạn hoàn thành xuất sắc dự án nghiên cứu!</p>
                        <a href='{link_student}' style='display: inline-block; padding: 10px 20px; background-color: #10b981; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px;'>Xem Tiến độ</a>
                        <br><br><p style='color: #666; font-size: 12px;'>Trân trọng,<br>Hệ thống HOU S-RIMS</p>
                    </div>
                    """
                    send_email_async(student.email, f"[HOU S-RIMS] Đề tài được phê duyệt", f"Đề tài {topic.title} đã được phê duyệt", html_content_student)
                    
        return jsonify({'message': 'Topic status updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

