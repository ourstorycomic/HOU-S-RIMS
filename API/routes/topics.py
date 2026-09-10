from flask import Blueprint, jsonify, request
from models import Topic, User, db

topics_bp = Blueprint('topics', __name__, url_prefix='/api/topics')

@topics_bp.route('', methods=['GET'])
def get_topics():
    topics = Topic.query.all()
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

mentors_bp = Blueprint('mentors', __name__, url_prefix='/api/mentors')

@mentors_bp.route('', methods=['GET'])
def get_mentors():
    mentors = User.query.filter_by(role='Mentor').all()
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
    data = request.get_json()
    if not data or 'name' not in data or 'batch_id' not in data or 'mentor_id' not in data or 'group_id' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
        
    try:
        existing_topic = Topic.query.filter_by(group_id=data['group_id'], batch_id=data['batch_id']).first()
        if existing_topic:
            return jsonify({'error': 'Group already registered a topic for this batch'}), 400
            
        new_topic = Topic(
            name=data['name'],
            description=data.get('description', ''),
            batch_id=data['batch_id'],
            mentor_id=data['mentor_id'],
            group_id=data['group_id'],
            status='pending'
        )
        db.session.add(new_topic)
        db.session.flush() 
        
        from models import TopicRegistration
        registration = TopicRegistration(
            topic_id=new_topic.id,
            group_id=new_topic.group_id,
            mentor_id=new_topic.mentor_id,
            status='pending'
        )
        db.session.add(registration)
        db.session.commit() 
        
        return jsonify({'message': 'Topic registered successfully', 'topic_id': new_topic.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@topics_bp.route('/<int:topic_id>/approve', methods=['POST'])
def approve_topic(topic_id):
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': 'Missing status'}), 400
        
    try:
        topic = Topic.query.get(topic_id)
        if not topic:
            return jsonify({'error': 'Topic not found'}), 404
            
        topic.status = data['status']
        db.session.commit()
        return jsonify({'message': 'Topic status updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

