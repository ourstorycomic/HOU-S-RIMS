from flask import Blueprint, request, jsonify
from models import db, Milestone, Progress

progress_bp = Blueprint('progress_api', __name__, url_prefix='/api/topics')

@progress_bp.route('/<int:topic_id>/progress', methods=['GET'])
def get_progress(topic_id):
    """
    Get progress of a topic
    ---
    tags:
      - Progress
    parameters:
      - in: path
        name: topic_id
        type: integer
        required: true
    responses:
      200:
        description: List of milestones and progress
    """
    milestones = Milestone.query.filter_by(topic_id=topic_id).all()
    result = []
    for m in milestones:
        progresses = Progress.query.filter_by(milestone_id=m.id).all()
        result.append({
            'milestone_id': m.id,
            'name': m.name,
            'deadline': m.deadline.strftime('%Y-%m-%d %H:%M:%S') if m.deadline else None,
            'status': m.status,
            'progress': [{'id': p.id, 'percentage': p.percentage, 'notes': p.notes} for p in progresses]
        })
    return jsonify(result), 200

@progress_bp.route('/<int:topic_id>/progress', methods=['POST'])
def update_progress(topic_id):
    """
    Update progress of a milestone for a topic
    ---
    tags:
      - Progress
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
            milestone_id:
              type: integer
            percentage:
              type: integer
            notes:
              type: string
    responses:
      201:
        description: Progress updated
    """
    data = request.get_json()
    if not data or 'milestone_id' not in data or 'percentage' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
        
    try:
        new_progress = Progress(
            milestone_id=data['milestone_id'],
            percentage=int(data['percentage']),
            notes=data.get('notes', '')
        )
        db.session.add(new_progress)
        db.session.commit()
        return jsonify({'message': 'Progress updated'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
