from flask import Blueprint, jsonify, request
from models import Topic, User, db

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
    query = Topic.query
    
    # Filter by mentor
    mentor_id = request.args.get('mentor_id')
    if mentor_id:
        query = query.filter_by(mentor_id=mentor_id)
        
    # Filter by status (e.g. pending)
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)
        
    # Filter by group_id
    group_id = request.args.get('group_id')
    if group_id:
        if group_id.lower() == 'null' or group_id == '0':
            query = query.filter(Topic.group_id.is_(None))
        else:
            query = query.filter_by(group_id=group_id)
            
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
        
        if group_id == 0:
            # Auto-create group
            new_group = Group(
                name=f"Nhóm của {session.get('user_name', 'SV')}",
                batch_id=data['batch_id'],
                leader_id=user_id
            )
            db.session.add(new_group)
            db.session.flush() # To get new_group.id
            group_id = new_group.id
            
            # Add leader as member
            new_member = GroupMember(group_id=group_id, student_id=user_id)
            db.session.add(new_member)
        else:
            # Check if group already has a topic in this batch
            existing_topic = Topic.query.filter_by(group_id=group_id, batch_id=data['batch_id']).first()
            if existing_topic:
                return jsonify({'error': 'Group already registered a topic for this batch'}), 400
            
        new_topic = Topic(
            title=data['name'], # Note: Model uses 'title'
            description=data.get('description', ''),
            batch_id=data['batch_id'],
            mentor_id=data['mentor_id'],
            group_id=group_id,
            status='pending'
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
        
        return jsonify({'message': 'Topic registered successfully', 'topic_id': new_topic.id}), 201
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
    if session.get('role') != 'faculty':
        return jsonify({'error': 'Unauthorized'}), 403
        
    try:
        topic = Topic.query.get(topic_id)
        if not topic:
            return jsonify({'error': 'Topic not found'}), 404
            
        topic.status = 'approved'
        db.session.commit()
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
        return jsonify({'message': 'Topic status updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

