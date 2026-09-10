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
        new_council = Council(
            name=data['name'],
            batch_id=data['batch_id']
        )
        db.session.add(new_council)
        db.session.commit()
        return jsonify({'message': 'Council created', 'id': new_council.id}), 201
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
