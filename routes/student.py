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



# =========================================================================
# TASK 3.4: UPLOAD AVATAR & BẢNG ĐIỂM (TRANSCRIPT)
# =========================================================================
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import session

@student_bp.route('/api/students/upload-avatar', methods=['POST'])
@student_bp.route('/api/user/upload-avatar', methods=['POST'])
def upload_avatar():
    uid = session.get('user_id')
    user = User.query.get(uid) if uid else None
    if not user:
        return jsonify({'error': 'Vui lòng đăng nhập để thực hiện!'}), 401
    
    import base64
    is_serverless = bool(os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME') or os.getenv('LAMBDA_TASK_ROOT'))
    if is_serverless:
        upload_dir = '/tmp/uploads/avatars'
    else:
        upload_dir = os.path.join(request.environ.get('FLASK_APP_DIR', '.'), 'static', 'uploads', 'avatars')
    try:
        os.makedirs(upload_dir, exist_ok=True)
    except Exception:
        pass

    # Check if base64 data URI was sent (e.g. from Cropper.js)
    data = request.get_json(silent=True) or {}
    base64_data = data.get('avatar_base64') or data.get('image')

    if base64_data:
        try:
            if ',' in base64_data:
                header, encoded = base64_data.split(',', 1)
            else:
                encoded = base64_data
            img_bytes = base64.b64decode(encoded)
            unique_name = f"avatar_{user.id}_{int(datetime.utcnow().timestamp())}.png"
            save_path = os.path.join(upload_dir, unique_name)
            with open(save_path, 'wb') as f:
                f.write(img_bytes)
        except Exception as e:
            return jsonify({'error': f'Lỗi xử lý ảnh crop: {str(e)}'}), 400
    else:
        file = request.files.get('avatar') or request.files.get('file')
        if not file or file.filename == '':
            return jsonify({'error': 'Vui lòng chọn file ảnh tải lên!'}), 400
            
        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
            return jsonify({'error': 'Chỉ chấp nhận file ảnh định dạng JPG, PNG hoặc WEBP!'}), 400
        
        unique_name = f"avatar_{user.id}_{int(datetime.utcnow().timestamp())}{ext}"
        save_path = os.path.join(upload_dir, unique_name)
        file.save(save_path)
    
    relative_path = f"uploads/avatars/{unique_name}"
    user.avatar_url = relative_path
    db.session.commit()
    
    return jsonify({
        'message': 'Đã cập nhật ảnh đại diện thành công!',
        'avatar_url': relative_path
    }), 200

@student_bp.route('/api/students/upload-transcript', methods=['POST'])
@student_bp.route('/api/user/upload-transcript', methods=['POST'])
def upload_transcript():
    uid = session.get('user_id')
    user = User.query.get(uid) if uid else None
    if not user:
        return jsonify({'error': 'Vui lòng đăng nhập để thực hiện!'}), 401
    
    file = request.files.get('transcript') or request.files.get('file')
    if not file or file.filename == '':
        return jsonify({'error': 'Vui lòng chọn file bảng điểm tải lên!'}), 400
        
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ['.pdf', '.jpg', '.jpeg', '.png']:
        return jsonify({'error': 'Chỉ chấp nhận file bảng điểm định dạng PDF, JPG hoặc PNG!'}), 400
        
    is_serverless = bool(os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME') or os.getenv('LAMBDA_TASK_ROOT'))
    if is_serverless:
        upload_dir = '/tmp/uploads/transcripts'
    else:
        upload_dir = os.path.join(request.environ.get('FLASK_APP_DIR', '.'), 'static', 'uploads', 'transcripts')
    try:
        os.makedirs(upload_dir, exist_ok=True)
    except Exception:
        pass
    
    unique_name = f"transcript_{user.id}_{int(datetime.utcnow().timestamp())}{ext}"
    save_path = os.path.join(upload_dir, unique_name)
    file.save(save_path)
    
    relative_path = f"uploads/transcripts/{unique_name}"
    user.transcript_url = relative_path
    db.session.commit()
    
    return jsonify({
        'message': 'Đã tải lên bảng điểm thành công!',
        'transcript_url': relative_path
    }), 200
