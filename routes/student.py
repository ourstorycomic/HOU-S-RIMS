# routes/student.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User

student_bp = Blueprint('student', __name__)

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
