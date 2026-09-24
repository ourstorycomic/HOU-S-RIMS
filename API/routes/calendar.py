from flask import Blueprint, request, jsonify
from models import db, Meeting

calendar_bp = Blueprint('calendar_api', __name__, url_prefix='/api/calendar')

@calendar_bp.route('/events', methods=['GET'])
def get_events():
    """
    Get all calendar events/meetings
    ---
    tags:
      - Calendar
    parameters:
      - in: query
        name: user_id
        type: integer
        description: Filter events by user ID
    responses:
      200:
        description: List of events
    """
    from models import Milestone
    meetings = Meeting.query.filter(Meeting.status.in_(['approved', 'pending'])).all()
    result = []
    for m in meetings:
        result.append({
            'id': m.id,
            'title': m.title,
            'description': m.description,
            'start': m.start_time.strftime('%Y-%m-%d %H:%M:%S') if m.start_time else None,
            'end': m.end_time.strftime('%Y-%m-%d %H:%M:%S') if m.end_time else None,
            'organizer_id': m.organizer_id,
            'topic_id': m.topic_id,
            'status': m.status
        })
        
    milestones = Milestone.query.all()
    for ms in milestones:
        result.append({
            'id': f'ms_{ms.id}',
            'title': f'🚩 Deadline: {ms.name}',
            'start': ms.deadline.strftime('%Y-%m-%d %H:%M:%S') if ms.deadline else None,
            'end': ms.deadline.strftime('%Y-%m-%d %H:%M:%S') if ms.deadline else None,
            'status': 'milestone'
        })
        
    return jsonify(result), 200

@calendar_bp.route('/events', methods=['POST'])
def create_event():
    """
    Create a new event/meeting
    """
    from datetime import datetime
    data = request.get_json()
    if not data or 'title' not in data or 'start_time' not in data:
        return jsonify({'error': 'Missing required fields (title, start_time)'}), 400
        
    try:
        from flask import session
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401
            
        new_meeting = Meeting(
            title=data['title'],
            description=data.get('description', ''),
            start_time=datetime.strptime(data['start_time'], '%Y-%m-%dT%H:%M') if 'T' in data['start_time'] else datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M'),
            end_time=datetime.strptime(data.get('end_time', data['start_time']), '%Y-%m-%dT%H:%M') if 'T' in data.get('end_time', data['start_time']) else datetime.strptime(data.get('end_time', data['start_time']), '%Y-%m-%d %H:%M'),
            organizer_id=user_id,
            topic_id=data.get('topic_id'),
            status='pending'
        )
        db.session.add(new_meeting)
        db.session.commit()
        return jsonify({'message': 'Meeting created successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@calendar_bp.route('/events/<int:meeting_id>', methods=['DELETE'])
def delete_event(meeting_id):
    """
    Delete (revoke) an event/meeting
    """
    try:
        from flask import session
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401
            
        meeting = Meeting.query.get(meeting_id)
        if not meeting:
            return jsonify({'error': 'Meeting not found'}), 404
            
        # Optional: check if user is organizer
        if meeting.organizer_id != user_id:
            return jsonify({'error': 'Permission denied'}), 403
            
        db.session.delete(meeting)
        db.session.commit()
        return jsonify({'message': 'Meeting deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@calendar_bp.route('/events/<int:id>/status', methods=['PUT'])
def update_event_status(id):
    from models import db, Meeting
    meeting = Meeting.query.get(id)
    if not meeting:
        return jsonify({'error': 'Meeting not found'}), 404
        
    data = request.get_json()
    new_status = data.get('status')
    if new_status not in ['approved', 'rejected', 'pending']:
        return jsonify({'error': 'Invalid status'}), 400
        
    meeting.status = new_status
    db.session.commit()
    return jsonify({'message': 'Status updated successfully'})
