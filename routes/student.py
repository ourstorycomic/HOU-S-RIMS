# routes/student.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User

student_bp = Blueprint('student_api', __name__)

@student_bp.route('/api/students/profile', methods=['GET', 'PUT'])
@jwt_required()
def student_profile():
    # Lấy username từ token (đã được xác thực)
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()

    if not user:
        return jsonify({"msg": "Người dùng không tồn tại"}), 404

    if request.method == 'GET':
        return jsonify(user.to_dict()), 200

    if request.method == 'PUT':
        data = request.get_json()
        if not data:
            return jsonify({"msg": "Thiếu dữ liệu (Body)"}), 400

        # Cập nhật thông tin nếu có truyền lên
        if 'bio' in data:
            user.bio = data['bio']
        if 'phone' in data:
            user.phone = data['phone']

        db.session.commit()

        return jsonify({
            "msg": "Cập nhật profile thành công!",
            "user": user.to_dict()
        }), 200

@student_bp.route('/api/students/lookup', methods=['GET', 'POST'])
def lookup_student():
    if request.method == 'POST':
        data = request.get_json(silent=True) or request.form or {}
        code = (data.get('student_id') or data.get('code') or '').strip()
    else:
        code = (request.args.get('student_id') or request.args.get('code') or '').strip()

    if not code:
        return jsonify({'success': False, 'error': 'Vui lòng nhập Mã sinh viên!'}), 400

    from sqlalchemy import func, or_
    student = User.query.filter(
        or_(
            func.lower(User.student_id) == code.lower(),
            func.lower(User.username) == code.lower()
        ),
        func.lower(User.role) == 'student'
    ).first()

    if not student:
        return jsonify({'success': False, 'error': f'Không tìm thấy sinh viên với mã "{code}"!'}), 404

    return jsonify({
        'success': True,
        'student': {
            'id': student.id,
            'student_id': student.student_id or student.username,
            'full_name': student.full_name,
            'username': student.username,
            'email': student.email,
            'faculty': student.faculty or 'Khoa Công nghệ Thông tin'
        }
    }), 200

@student_bp.route('/api/mentors/lookup', methods=['GET'])
def lookup_mentors():
    name = (request.args.get('name') or '').strip()
    from sqlalchemy import func
    query = User.query.filter(func.lower(User.role) == 'lecturer')
    if name:
        query = query.filter(User.full_name.ilike(f'%{name}%'))
    mentors = query.all()
    return jsonify({
        'success': True,
        'mentors': [
            {
                'id': m.id,
                'username': m.username,
                'full_name': m.full_name,
                'faculty': m.faculty,
                'email': m.email
            }
            for m in mentors
        ]
    })

