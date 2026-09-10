from flask import Blueprint, request, jsonify, session
from models import User, db

profile_bp = Blueprint('profile_api', __name__, url_prefix='/api/profile')

@profile_bp.route('/<int:user_id>', methods=['GET'])
def get_profile(user_id):
    """
    Get user profile
    ---
    tags:
      - Profile
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
    responses:
      200:
        description: User profile data
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    return jsonify({
        'id': user.id,
        'username': user.username,
        'full_name': user.full_name,
        'email': user.email,
        'phone': user.phone,
        'bio': user.bio,
        'role': user.role
    }), 200

@profile_bp.route('/<int:user_id>', methods=['PUT'])
def update_profile(user_id):
    """
    Update user profile
    ---
    tags:
      - Profile
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            full_name:
              type: string
            email:
              type: string
            phone:
              type: string
            bio:
              type: string
    responses:
      200:
        description: Profile updated
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    data = request.get_json()
    if 'full_name' in data: user.full_name = data['full_name']
    if 'email' in data: user.email = data['email']
    if 'phone' in data: user.phone = data['phone']
    if 'bio' in data: user.bio = data['bio']
    
    db.session.commit()
    return jsonify({'message': 'Profile updated successfully'}), 200
