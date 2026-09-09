from flask import Blueprint, request, jsonify
from models import db, Batch
from datetime import datetime

batches_bp = Blueprint('batches', __name__, url_prefix='/api/batches')

@batches_bp.route('', methods=['POST'])
def create_batch():
    data = request.get_json()
    
    if not data or not 'name' in data or not 'start_date' in data or not 'end_date' in data:
        return jsonify({'error': 'Missing required fields'}), 400
        
    try:
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
        
        new_batch = Batch(
            name=data['name'],
            start_date=start_date,
            end_date=end_date,
            status=data.get('status', 'active')
        )
        db.session.add(new_batch)
        db.session.commit()
        
        return jsonify({
            'message': 'Batch created successfully',
            'batch': {
                'id': new_batch.id,
                'name': new_batch.name,
                'start_date': new_batch.start_date.strftime('%Y-%m-%d'),
                'end_date': new_batch.end_date.strftime('%Y-%m-%d'),
                'status': new_batch.status
            }
        }), 201
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@batches_bp.route('', methods=['GET'])
def get_batches():
    batches = Batch.query.all()
    result = []
    for batch in batches:
        result.append({
            'id': batch.id,
            'name': batch.name,
            'start_date': batch.start_date.strftime('%Y-%m-%d'),
            'end_date': batch.end_date.strftime('%Y-%m-%d'),
            'status': batch.status
        })
    return jsonify(result), 200
