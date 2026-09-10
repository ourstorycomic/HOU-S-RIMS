from flask import Blueprint, request, jsonify
from models import db, Group, GroupMember, User

groups_bp = Blueprint('groups', __name__, url_prefix='/api/groups')

@groups_bp.route('', methods=['POST'])
def create_group():
    data = request.get_json()
    if not data or 'name' not in data or 'batch_id' not in data or 'leader_id' not in data:
        return jsonify({'error': 'Missing required fields: name, batch_id, leader_id'}), 400
        
    try:
        new_group = Group(
            name=data['name'],
            batch_id=data['batch_id'],
            leader_id=data['leader_id']
        )
        db.session.add(new_group)
        db.session.commit()
        
        # Add leader to group members automatically
        member = GroupMember(group_id=new_group.id, student_id=new_group.leader_id)
        db.session.add(member)
        db.session.commit()
        
        return jsonify({
            'message': 'Group created successfully',
            'group': {
                'id': new_group.id,
                'name': new_group.name,
                'batch_id': new_group.batch_id,
                'leader_id': new_group.leader_id
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@groups_bp.route('/<int:group_id>/members', methods=['POST'])
def add_member(group_id):
    data = request.get_json()
    if not data or 'student_id' not in data:
        return jsonify({'error': 'Missing student_id'}), 400
        
    try:
        # Check if student exists
        student = User.query.get(data['student_id'])
        if not student or student.role != 'Student':
            return jsonify({'error': 'Invalid student'}), 400
            
        # Check if already a member
        existing = GroupMember.query.filter_by(group_id=group_id, student_id=data['student_id']).first()
        if existing:
            return jsonify({'error': 'Student is already a member of this group'}), 400
            
        member = GroupMember(
            group_id=group_id,
            student_id=data['student_id']
        )
        db.session.add(member)
        db.session.commit()
        
        return jsonify({'message': 'Member added successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
