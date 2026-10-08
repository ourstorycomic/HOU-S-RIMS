from flask import Blueprint, request, jsonify
from models import db, Council, Rubric, Evaluation
import json

evaluation_bp = Blueprint('evaluation_api', __name__, url_prefix='/api')

@evaluation_bp.route('/councils', methods=['POST'])
def create_council():
    """
    Create a new council
    ---
    tags:
      - Evaluation
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
            batch_id:
              type: integer
    responses:
      201:
        description: Council created
    """
    data = request.get_json()
    if not data or 'name' not in data or 'batch_id' not in data:
        return jsonify({'error': 'Missing name or batch_id'}), 400
        
    try:
        from datetime import datetime
        meeting_date = None
        if data.get('meeting_date'):
            meeting_date = datetime.strptime(data['meeting_date'], '%Y-%m-%d').date()
            
        meeting_time = None
        if data.get('meeting_time'):
            meeting_time = datetime.strptime(data['meeting_time'], '%H:%M').time()
            
        new_council = Council(
            name=data['name'],
            decision_number=data.get('decision_number'),
            meeting_date=meeting_date,
            meeting_time=meeting_time,
            location=data.get('location'),
            batch_id=data['batch_id']
        )
        db.session.add(new_council)
        db.session.flush() # to get new_council.id
        
        from models import CouncilMember, Topic, User, Notification, GroupMember
        from email_utils import send_notification_email
        
        # Add members - all fields are now arrays
        lecturers_to_notify = set()
        
        
        # Check if lecturers are already in another council for this batch
        all_lecturer_ids = (data.get('president') or []) + (data.get('secretary') or []) + (data.get('members') or [])
        if all_lecturer_ids:
            existing_members = CouncilMember.query.join(Council).filter(
                Council.batch_id == data['batch_id'],
                CouncilMember.mentor_id.in_(all_lecturer_ids)
            ).all()
            if existing_members:
                conflict_users = list(set([User.query.get(m.mentor_id).full_name for m in existing_members]))
                return jsonify({'error': f'Các giảng viên sau đã được phân công vào hội đồng khác trong đợt này: {", ".join(conflict_users)}'}), 400

        for p_id in (data.get('president') or []):
            if p_id:
                db.session.add(CouncilMember(council_id=new_council.id, mentor_id=p_id, role='president'))
                lecturers_to_notify.add(int(p_id))
            
        for s_id in (data.get('secretary') or []):
            if s_id:
                db.session.add(CouncilMember(council_id=new_council.id, mentor_id=s_id, role='secretary'))
                lecturers_to_notify.add(int(s_id))
            
        for m_id in (data.get('members') or []):
            if m_id:
                db.session.add(CouncilMember(council_id=new_council.id, mentor_id=m_id, role='member'))
                lecturers_to_notify.add(int(m_id))
                
        # Assign topics
        students_to_notify = set()
        if data.get('topics'):
            for t_item in data['topics']:
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
        
        # Notify lecturers
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
                
        # Notify students
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
    from models import Council, CouncilMember, Topic, Notification, User
    from app import db
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
        
        CouncilMember.query.filter_by(council_id=council.id).delete()
        db.session.delete(council)
        db.session.commit()
        return jsonify({'message': 'Deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@evaluation_bp.route('/councils/<int:council_id>', methods=['PUT'])
def update_council(council_id):
    from models import Council, CouncilMember, Topic, Notification, User, GroupMember
    from email_utils import send_notification_email
    from app import db
    from datetime import datetime
    
    data = request.json
    try:
        council = Council.query.get_or_404(council_id)
        council.name = data.get('name', council.name)
        council.decision_number = data.get('decision_number', council.decision_number)
        council.location = data.get('location', council.location)
        
        if data.get('meeting_date'):
            council.meeting_date = datetime.strptime(data['meeting_date'], '%Y-%m-%d').date()
        if data.get('meeting_time'):
            council.meeting_time = datetime.strptime(data['meeting_time'], '%H:%M').time()
            
        # Update members if provided
        if any(k in data for k in ['president', 'secretary', 'members']):
            all_lecturer_ids = (data.get('president') or []) + (data.get('secretary') or []) + (data.get('members') or [])
            if all_lecturer_ids:
                existing_members = CouncilMember.query.join(Council).filter(
                    Council.batch_id == council.batch_id,
                    Council.id != council.id,
                    CouncilMember.mentor_id.in_(all_lecturer_ids)
                ).all()
                if existing_members:
                    conflict_users = list(set([User.query.get(m.mentor_id).full_name for m in existing_members]))
                    return jsonify({'error': f'Các giảng viên sau đã được phân công vào hội đồng khác trong đợt này: {", ".join(conflict_users)}'}), 400

            CouncilMember.query.filter_by(council_id=council.id).delete()
            for p_id in (data.get('president') or []):
                db.session.add(CouncilMember(council_id=council.id, mentor_id=p_id, role='president'))
            for s_id in (data.get('secretary') or []):
                db.session.add(CouncilMember(council_id=council.id, mentor_id=s_id, role='secretary'))
            for m_id in (data.get('members') or []):
                db.session.add(CouncilMember(council_id=council.id, mentor_id=m_id, role='member'))
                
        # Update topics
        if 'topics' in data:
            Topic.query.filter_by(council_id=council.id).update({'council_id': None, 'presentation_time': None})
            for t_item in data['topics']:
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

@evaluation_bp.route('/rubrics', methods=['POST', 'PUT'])
def manage_rubrics():
    """
    Create or update a rubric
    ---
    tags:
      - Evaluation
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
            criteria_json:
              type: string
              description: JSON string of criteria
            total_score:
              type: number
    responses:
      200:
        description: Rubric processed
    """
    data = request.get_json()
    if not data or 'name' not in data or 'criteria_json' not in data or 'total_score' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
        
    try:
        # For simplicity, treating POST/PUT the same as create new or we can search by name
        new_rubric = Rubric(
            name=data['name'],
            criteria_json=json.dumps(data['criteria_json']) if isinstance(data['criteria_json'], dict) else data['criteria_json'],
            total_score=float(data['total_score'])
        )
        db.session.add(new_rubric)
        db.session.commit()
        return jsonify({'message': 'Rubric saved', 'id': new_rubric.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
