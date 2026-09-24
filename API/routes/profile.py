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
        
    from models import Skill, Achievement, Experience
    skills = [{'id': s.id, 'name': s.name} for s in Skill.query.filter_by(student_id=user.id).all()]
    achievements = [{'id': a.id, 'name': a.name, 'year': a.year, 'description': a.description} for a in Achievement.query.filter_by(student_id=user.id).all()]
    experiences = [{'id': e.id, 'project_name': e.project_name, 'role': e.role, 'duration': e.duration, 'description': e.description} for e in Experience.query.filter_by(student_id=user.id).all()]
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'full_name': user.full_name,
        'email': user.email,
        'phone': user.phone,
        'bio': user.bio,
        'role': user.role,
        'student_id': user.student_id,
        'skills': skills,
        'achievements': achievements,
        'experiences': experiences
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
    if 'faculty' in data: user.faculty = data['faculty']
    
    db.session.commit()
    return jsonify({'message': 'Profile updated successfully'}), 200

# ================= Portfolio endpoints =================

@profile_bp.route('/skills', methods=['POST'])
def add_skill():
    from models import Skill
    data = request.get_json()
    user_id = session.get('user_id')
    if not user_id or not data.get('name'):
        return jsonify({'error': 'Missing data'}), 400
    try:
        new_skill = Skill(student_id=user_id, name=data['name'])
        db.session.add(new_skill)
        db.session.commit()
        return jsonify({'message': 'Skill added successfully', 'id': new_skill.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/skills/<int:skill_id>', methods=['DELETE'])
def delete_skill(skill_id):
    from models import Skill
    user_id = session.get('user_id')
    try:
        skill = Skill.query.get(skill_id)
        if skill and skill.student_id == user_id:
            db.session.delete(skill)
            db.session.commit()
            return jsonify({'message': 'Skill deleted'}), 200
        return jsonify({'error': 'Not found or unauthorized'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/achievements', methods=['POST'])
def add_achievement():
    from models import Achievement
    data = request.get_json()
    user_id = session.get('user_id')
    if not user_id or not data.get('name'):
        return jsonify({'error': 'Missing data'}), 400
    try:
        new_achv = Achievement(
            student_id=user_id, 
            name=data['name'], 
            year=data.get('year'), 
            description=data.get('description')
        )
        db.session.add(new_achv)
        db.session.commit()
        return jsonify({'message': 'Achievement added', 'id': new_achv.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/experiences', methods=['POST'])
def add_experience():
    from models import Experience
    data = request.get_json()
    user_id = session.get('user_id')
    if not user_id or not data.get('project_name'):
        return jsonify({'error': 'Missing data'}), 400
    try:
        new_exp = Experience(
            student_id=user_id, 
            project_name=data['project_name'], 
            role=data.get('role'), 
            duration=data.get('duration'), 
            description=data.get('description')
        )
        db.session.add(new_exp)
        db.session.commit()
        return jsonify({'message': 'Experience added', 'id': new_exp.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/achievements/<int:id>', methods=['DELETE'])
def delete_achievement(id):
    from models import Achievement
    user_id = session.get('user_id')
    try:
        ach = Achievement.query.get(id)
        if ach and ach.student_id == user_id:
            db.session.delete(ach)
            db.session.commit()
            return jsonify({'message': 'Achievement deleted'}), 200
        return jsonify({'error': 'Not found or unauthorized'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/experiences/<int:id>', methods=['DELETE'])
def delete_experience(id):
    from models import Experience
    user_id = session.get('user_id')
    try:
        exp = Experience.query.get(id)
        if exp and exp.student_id == user_id:
            db.session.delete(exp)
            db.session.commit()
            return jsonify({'message': 'Experience deleted'}), 200
        return jsonify({'error': 'Not found or unauthorized'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'}), 200
