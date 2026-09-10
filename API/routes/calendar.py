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
    # Simply returning all meetings for now. 
    # In reality, we filter by user_id if they are mentor or student.
    meetings = Meeting.query.all()
    result = []
    for m in meetings:
        result.append({
            'id': m.id,
            'topic_id': m.topic_id,
            'meeting_time': m.meeting_time.strftime('%Y-%m-%d %H:%M:%S') if m.meeting_time else None,
            'location': m.location,
            'notes': m.notes
        })
    return jsonify(result), 200

@calendar_bp.route('/events', methods=['POST'])
def create_event():
    """
    Create a new event/meeting
    ---
    tags:
      - Calendar
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            topic_id:
              type: integer
            location:
              type: string
            notes:
              type: string
    responses:
      201:
        description: Event created
    """
    data = request.get_json()
    if not data or 'topic_id' not in data:
        return jsonify({'error': 'Missing topic_id'}), 400
        
    from datetime import datetime
    new_meeting = Meeting(
        topic_id=data['topic_id'],
        meeting_time=datetime.now(), # Mock time
        location=data.get('location', 'Online'),
        notes=data.get('notes', '')
    )
    db.session.add(new_meeting)
    db.session.commit()
    
    return jsonify({'message': 'Event created', 'id': new_meeting.id}), 201
