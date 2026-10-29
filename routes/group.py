from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from models import db, Group, GroupMember, User, Batch, Notification
from datetime import datetime
from sqlalchemy import func, or_

group_bp = Blueprint('group_registration', __name__)

def get_current_user():
    """Helper lấy user hiện tại từ session hoặc JWT nếu có"""
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

# ==========================================
# 1. VIEW ROUTE: Chuyển hướng sang SPA Cổng Sinh Viên (#s-register)
# ==========================================
@group_bp.route('/student/group-registration')
@group_bp.route('/group/register')
def group_registration_page():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return redirect(url_for('web.student_page') + '#s-register')

@group_bp.route('/api/groups/my_group', methods=['GET'])
def get_my_group():
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'error': 'Vui lòng đăng nhập!'}), 401
    
    active_group = Group.query.filter_by(leader_id=current_user.id).order_by(Group.id.desc()).first()
    if not active_group:
        membership = GroupMember.query.filter_by(student_id=current_user.id).order_by(GroupMember.id.desc()).first()
        if membership:
            active_group = Group.query.get(membership.group_id)
            
    if not active_group:
        return jsonify({'success': True, 'group': None}), 200
        
    return jsonify({
        'success': True,
        'group': active_group.to_dict()
    }), 200

@group_bp.route('/api/groups/<int:group_id>/name', methods=['PUT'])
def update_group_name(group_id):
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'error': 'Vui lòng đăng nhập!'}), 401
        
    group = Group.query.get(group_id)
    if not group:
        return jsonify({'success': False, 'error': 'Không tìm thấy nhóm!'}), 404
        
    if group.leader_id != current_user.id:
        return jsonify({'success': False, 'error': 'Chỉ trưởng nhóm mới có quyền đổi tên nhóm!'}), 403
        
    data = request.get_json(silent=True) or {}
    new_name = (data.get('name') or '').strip()
    if not new_name:
        return jsonify({'success': False, 'error': 'Tên nhóm không được để trống!'}), 400
        
    group.name = new_name
    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'Đã cập nhật tên nhóm thành công!',
        'group': group.to_dict()
    }), 200


# ==========================================
# 2. API: Khởi tạo nhóm mới
# POST /api/groups/create
# ==========================================
@group_bp.route('/api/groups/create', methods=['POST'])
def create_group():
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'error': 'Vui lòng đăng nhập để thực hiện thao tác này!'}), 401
    
    try:
        data = request.get_json(silent=True) or {}
        
        # Kiểm tra đợt NCKH đang active nếu có
        active_batch = Batch.query.filter_by(status='active').order_by(Batch.id.desc()).first()
        batch_id = active_batch.id if active_batch else None
        
        # Tên nhóm mặc định nếu không truyền
        group_name = data.get('name') or f"Nhóm NCKH - {current_user.full_name}"
        
        # Tạo nhóm mới
        new_group = Group(
            name=group_name,
            batch_id=batch_id,
            leader_id=current_user.id,
            mentor_id=None,
            status='draft',
            created_at=datetime.utcnow()
        )
        db.session.add(new_group)
        db.session.flush() # Lấy new_group.id
        
        # Tự động thêm Trưởng nhóm vào bảng group_members với status 'joined'
        leader_member = GroupMember(
            group_id=new_group.id,
            student_id=current_user.id,
            status='joined'
        )
        db.session.add(leader_member)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Khởi tạo nhóm nghiên cứu thành công!',
            'group': new_group.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Lỗi khi tạo nhóm: {str(e)}'
        }), 500


# ==========================================
# 3. API: Thêm thành viên vào nhóm bằng Mã SV
# POST /api/groups/<group_id>/invite
# ==========================================
@group_bp.route('/api/groups/<int:group_id>/invite', methods=['POST'])
def invite_member(group_id):
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'error': 'Vui lòng đăng nhập!'}), 401
    
    try:
        group = Group.query.get(group_id)
        if not group:
            return jsonify({'success': False, 'error': 'Không tìm thấy nhóm này!'}), 404
        
        # Kiểm tra quyền: Chỉ trưởng nhóm mới được mời thành viên
        if group.leader_id != current_user.id:
            return jsonify({'success': False, 'error': 'Chỉ trưởng nhóm mới có quyền mời thành viên!'}), 403
        
        data = request.get_json(silent=True) or {}
        raw_student_id = (data.get('student_id') or data.get('student_code') or '').strip()
        
        if not raw_student_id:
            return jsonify({'success': False, 'error': 'Vui lòng nhập Mã Sinh Viên!'}), 400
        
        # Tìm sinh viên trong hệ thống theo Mã SV (student_id), hoặc username
        target_student = User.query.filter(
            func.lower(User.role) == 'student',
            or_(
                func.lower(User.student_id) == raw_student_id.lower(),
                func.lower(User.username) == raw_student_id.lower(),
                User.id == (int(raw_student_id) if raw_student_id.isdigit() else -1)
            )
        ).first()
        
        if not target_student:
            return jsonify({
                'success': False,
                'error': f'Không tìm thấy sinh viên nào với Mã SV "{raw_student_id}" trong hệ thống!'
            }), 404
            
        # Không được tự mời chính mình (đã là leader)
        if target_student.id == group.leader_id:
            return jsonify({
                'success': False,
                'error': 'Bạn là Trưởng nhóm, đã có tên trong danh sách thành viên!'
            }), 400
            
        # Kiểm tra xem sinh viên này đã có trong nhóm chưa
        existing_member = GroupMember.query.filter_by(group_id=group.id, student_id=target_student.id).first()
        if existing_member:
            status_text = 'đã tham gia nhóm' if existing_member.status == 'joined' else 'đang trong trạng thái được mời'
            return jsonify({
                'success': False,
                'error': f'Sinh viên {target_student.full_name} ({target_student.student_id or target_student.username}) {status_text}!'
            }), 400
            
        # Thêm vào bảng group_members với status 'invited'
        new_member = GroupMember(
            group_id=group.id,
            student_id=target_student.id,
            status='invited'
        )
        db.session.add(new_member)
        
        # Tạo thông báo gửi đến sinh viên được mời
        try:
            notif = Notification(
                user_id=target_student.id,
                content=f"Sinh viên {current_user.full_name} đã mời bạn tham gia nhóm NCKH: {group.name}."
            )
            db.session.add(notif)
        except Exception:
            pass
            
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Đã gửi lời mời thành công đến sinh viên {target_student.full_name} ({target_student.student_id or target_student.username})!',
            'member': new_member.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Lỗi khi mời thành viên: {str(e)}'
        }), 500


# ==========================================
# 4. API: Chọn Mentor mong muốn & chuyển trạng thái
# POST /api/groups/<group_id>/select_mentor
# ==========================================
@group_bp.route('/api/groups/<int:group_id>/select_mentor', methods=['POST'])
def select_mentor(group_id):
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'error': 'Vui lòng đăng nhập!'}), 401
        
    try:
        group = Group.query.get(group_id)
        if not group:
            return jsonify({'success': False, 'error': 'Không tìm thấy nhóm này!'}), 404
            
        if group.leader_id != current_user.id:
            return jsonify({'success': False, 'error': 'Chỉ trưởng nhóm mới có quyền chọn Mentor hướng dẫn!'}), 403
            
        data = request.get_json(silent=True) or {}
        mentor_id = data.get('mentor_id')
        
        if not mentor_id:
            return jsonify({'success': False, 'error': 'Vui lòng chọn Giảng viên hướng dẫn!'}), 400
            
        mentor = User.query.get(mentor_id)
        if not mentor or mentor.role.lower() != 'lecturer':
            return jsonify({'success': False, 'error': 'Giảng viên đã chọn không hợp lệ trong hệ thống!'}), 400
            
        # Gán mentor_id và cập nhật trạng thái nhóm
        group.mentor_id = mentor.id
        group.status = 'pending_mentor'
        
        # Gửi thông báo đến Mentor (Chỉ gửi nếu nhóm không có thành viên nào đang chờ xác nhận)
        try:
            pending_members_cnt = GroupMember.query.filter(
                GroupMember.group_id == group_id,
                GroupMember.student_id != current_user.id,
                GroupMember.status.in_(['pending', 'invited'])
            ).count()
            if pending_members_cnt == 0:
                notif = Notification(
                    user_id=mentor.id,
                    content=f"Nhóm NCKH của sinh viên {current_user.full_name} ({current_user.student_id or ''}) đã gửi lời mời bạn làm Giảng viên Hướng dẫn."
                )
                db.session.add(notif)
        except Exception:
            pass
            
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Đã gửi yêu cầu hướng dẫn đến Thầy/Cô {mentor.full_name} thành công!',
            'group': group.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Lỗi khi chọn Mentor: {str(e)}'
        }), 500


# ==========================================
# 5. CÁC API PHỤ TRỢ: Lấy chi tiết & Xóa thành viên
# ==========================================
@group_bp.route('/api/groups/<int:group_id>', methods=['GET'])
def get_group_detail(group_id):
    group = Group.query.get(group_id)
    if not group:
        return jsonify({'success': False, 'error': 'Không tìm thấy nhóm!'}), 404
    return jsonify({
        'success': True,
        'group': group.to_dict()
    }), 200

@group_bp.route('/api/groups/<int:group_id>/members/<int:member_id>', methods=['DELETE'])
def remove_member(group_id, member_id):
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'error': 'Vui lòng đăng nhập!'}), 401
        
    try:
        group = Group.query.get(group_id)
        if not group:
            return jsonify({'success': False, 'error': 'Không tìm thấy nhóm!'}), 404
            
        if group.leader_id != current_user.id:
            return jsonify({'success': False, 'error': 'Chỉ trưởng nhóm mới có quyền xóa thành viên!'}), 403
            
        member = GroupMember.query.filter_by(id=member_id, group_id=group.id).first()
        if not member:
            return jsonify({'success': False, 'error': 'Không tìm thấy thành viên trong nhóm!'}), 404
            
        if member.student_id == group.leader_id:
            return jsonify({'success': False, 'error': 'Không thể xóa Trưởng nhóm!'}), 400
            
        db.session.delete(member)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Đã xóa thành viên / hủy lời mời thành công!'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@group_bp.route('/api/groups/mentors', methods=['GET'])
def get_mentors_list():
    try:
        mentors = User.query.filter(func.lower(User.role) == 'lecturer').all()
        return jsonify({
            'success': True,
            'mentors': [{
                'id': m.id,
                'name': m.full_name,
                'faculty': m.faculty or 'Khoa CNTT',
                'email': m.email,
                'bio': m.bio or ''
            } for m in mentors]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
