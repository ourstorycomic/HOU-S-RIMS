from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session
from models import db, Message, User

chat_bp = Blueprint('chat_api', __name__, url_prefix='/api/chat')

def to_vn_time(dt, fmt='%H:%M %d/%m/%Y'):
    """
    Chuyển đổi thời gian UTC sang múi giờ Việt Nam (UTC+7 / GMT+7)
    """
    if not dt:
        dt = datetime.utcnow()
    vn_dt = dt + timedelta(hours=7)
    return vn_dt.strftime(fmt)

@chat_bp.route('/<int:group_id>/messages', methods=['GET'])
def get_messages(group_id):
    """
    Get all chat messages for a specific group
    """
    search_query = request.args.get('search', '').strip()
    
    query = Message.query.filter_by(group_id=group_id)
    if search_query:
        query = query.filter(Message.content.ilike(f'%{search_query}%'))
        
    messages = query.order_by(Message.timestamp.asc()).all()
    result = []
    for msg in messages:
        sender = User.query.get(msg.sender_id)
        result.append({
            'id': msg.id,
            'sender_id': msg.sender_id,
            'sender_name': sender.full_name if sender else 'Unknown',
            'sender_role': sender.role if sender else 'Unknown',
            'content': msg.content,
            'message_type': msg.message_type,
            'file_url': msg.file_url,
            'file_name': msg.file_name,
            'timestamp': to_vn_time(msg.timestamp)
        })
    return jsonify(result), 200

import re

@chat_bp.route('/<int:group_id>/media', methods=['GET'])
def get_media(group_id):
    """
    Get media, files, and links for a specific group
    """
    messages = Message.query.filter_by(group_id=group_id).order_by(Message.timestamp.desc()).all()
    
    images_videos = []
    files = []
    links = []
    
    # Simple URL regex
    url_pattern = re.compile(r'(https?://[^\s]+)')
    
    for msg in messages:
        # Group images, videos, stickers
        if msg.message_type in ['image', 'video', 'sticker'] and msg.file_url:
            images_videos.append({
                'id': msg.id,
                'url': msg.file_url,
                'type': msg.message_type,
                'timestamp': to_vn_time(msg.timestamp, '%d/%m/%Y')
            })
        
        # Group files
        elif msg.message_type == 'file' and msg.file_url:
            files.append({
                'id': msg.id,
                'url': msg.file_url,
                'name': msg.file_name or 'Tài liệu',
                'timestamp': to_vn_time(msg.timestamp, '%d/%m/%Y')
            })
            
        # Extract links from text
        urls = url_pattern.findall(msg.content or '')
        for url in urls:
            links.append({
                'id': msg.id,
                'url': url,
                'timestamp': to_vn_time(msg.timestamp, '%d/%m/%Y')
            })
            
    return jsonify({
        'images_videos': images_videos,
        'files': files,
        'links': links
    }), 200

@chat_bp.route('/<int:group_id>/messages', methods=['POST'])
def send_message(group_id):
    """
    Send a new message to a specific group
    """
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': 'Message content is required'}), 400
        
    sender_id = session.get('user_id') or data.get('sender_id')
    if not sender_id:
        return jsonify({'error': 'Unauthorized or missing sender_id'}), 401
        
    now_utc = datetime.utcnow()
    new_msg = Message(
        sender_id=sender_id,
        group_id=group_id,
        content=data['content'],
        message_type=data.get('message_type', 'text'),
        file_url=data.get('file_url'),
        file_name=data.get('file_name'),
        timestamp=now_utc
    )
    db.session.add(new_msg)
    db.session.commit()
    
    sender = User.query.get(sender_id)
    return jsonify({
        'message': 'Sent successfully',
        'data': {
            'id': new_msg.id,
            'sender_id': sender_id,
            'sender_name': sender.full_name if sender else 'Unknown',
            'sender_role': sender.role if sender else 'Unknown',
            'content': new_msg.content,
            'message_type': new_msg.message_type,
            'file_url': new_msg.file_url,
            'file_name': new_msg.file_name,
            'timestamp': to_vn_time(new_msg.timestamp)
        }
    }), 201

import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/uploads/chat'

@chat_bp.route('/<int:group_id>/upload', methods=['POST'])
def upload_file(group_id):
    """
    Upload a file for chat
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        filename = secure_filename(file.filename)
        # Ensure dir exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        return jsonify({
            'file_url': f'/{UPLOAD_FOLDER}/{filename}',
            'file_name': filename
        }), 200


from sqlalchemy import or_, and_, desc

import unicodedata

def normalize_text(text):
    if not text:
        return ''
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8').lower()

@chat_bp.route('/users/search', methods=['GET'])
def search_users():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
        
    query_norm = normalize_text(query)
    
    # Fetch all users (assuming small DB for this project) to do robust search
    all_users = User.query.all()
    
    matched_users = []
    for u in all_users:
        if query_norm in normalize_text(u.full_name) or query_norm in normalize_text(u.username):
            matched_users.append(u)
            if len(matched_users) >= 10:
                break
                
    result = [{'id': u.id, 'name': u.full_name, 'role': u.role, 'code': u.username} for u in matched_users]
    return jsonify(result), 200

@chat_bp.route('/private/conversations', methods=['GET'])
def get_private_conversations():
    my_id = session.get('user_id')
    if not my_id:
        return jsonify({'error': 'Unauthorized'}), 401
        
    from models import User, Group, GroupMember, Topic, Message
    from sqlalchemy import or_, and_

    # 1. Get distinct users we chatted with
    messages = Message.query.filter(
        and_(Message.group_id == None, or_(Message.sender_id == my_id, Message.receiver_id == my_id))
    ).order_by(Message.timestamp.desc()).all()
    
    seen = set()
    result = []
    for msg in messages:
        other_id = msg.receiver_id if msg.sender_id == my_id else msg.sender_id
        if other_id and other_id not in seen:
            seen.add(other_id)
            other_user = User.query.get(other_id)
            if other_user:
                sub_text = msg.content if msg.message_type == 'text' else ('Lời mời tham gia nhóm' if msg.message_type == 'invitation' else f'[{msg.message_type}]')
                result.append({
                    'id': other_user.id,
                    'name': other_user.full_name,
                    'role': other_user.role,
                    'last_message': sub_text,
                    'timestamp': to_vn_time(msg.timestamp, '%H:%M %d/%m')
                })

    # 2. Add group peers: mentor (GVHD), leader, and group members from all approved groups/topics that my_id belongs to
    group_ids = set()

    # If my_id is a group member
    member_records = GroupMember.query.filter(GroupMember.student_id == my_id).all()
    for mr in member_records:
        group_ids.add(mr.group_id)

    # If my_id is group leader
    led_groups = Group.query.filter_by(leader_id=my_id).all()
    for lg in led_groups:
        group_ids.add(lg.id)

    # If my_id is mentor (Lecturer)
    mentored_topics = Topic.query.filter_by(mentor_id=my_id).all()
    for mt in mentored_topics:
        if mt.group_id:
            group_ids.add(mt.group_id)

    mentored_groups = Group.query.filter_by(mentor_id=my_id).all()
    for mg in mentored_groups:
        group_ids.add(mg.id)

    peer_dict = {}  # peer_id -> role_description

    if group_ids:
        groups = Group.query.filter(Group.id.in_(list(group_ids))).all()
        for g in groups:
            # A. Mentor (GVHD): Luôn cho phép trao đổi cá nhân 1-1 với Giảng viên hướng dẫn ngay từ khi đăng ký
            m_id = g.mentor_id
            if not m_id:
                for t in g.topics:
                    if t.mentor_id:
                        m_id = t.mentor_id
                        break
            if m_id and m_id != my_id:
                peer_dict[m_id] = 'Giảng viên hướng dẫn'
            elif my_id == m_id and g.leader_id and g.leader_id != my_id:
                if g.leader_id not in peer_dict:
                    peer_dict[g.leader_id] = 'Sinh viên (Trưởng nhóm đề tài)'

            # B & C: Thành viên nhóm khác chỉ được tạo hội thoại riêng khi đề tài đã được Khoa/Viện phê duyệt
            is_approved = (g.status == 'approved') or any(t.status == 'approved' for t in g.topics)
            if is_approved:
                # Group Leader
                if g.leader_id and g.leader_id != my_id:
                    if g.leader_id not in peer_dict:
                        peer_dict[g.leader_id] = 'Trưởng nhóm NCKH'

                # Group Members
                for gm in g.members:
                    if gm.student_id != my_id:
                        if gm.student_id not in peer_dict:
                            peer_dict[gm.student_id] = 'Thành viên nhóm'

    # Append any peer not yet in seen
    for peer_id, role_label in peer_dict.items():
        if peer_id not in seen:
            seen.add(peer_id)
            peer_user = User.query.get(peer_id)
            if peer_user:
                result.append({
                    'id': peer_user.id,
                    'name': peer_user.full_name,
                    'role': peer_user.role,
                    'last_message': role_label,
                    'timestamp': ''
                })

    return jsonify(result), 200

@chat_bp.route('/private/<int:user_id>/messages', methods=['GET'])
def get_private_messages(user_id):
    from datetime import datetime
    my_id = session.get('user_id')
    if not my_id:
        return jsonify({'error': 'Unauthorized'}), 401
        
    messages = Message.query.filter(
        and_(Message.group_id == None, or_(
            and_(Message.sender_id == my_id, Message.receiver_id == user_id),
            and_(Message.sender_id == user_id, Message.receiver_id == my_id)
        ))
    ).order_by(Message.timestamp.asc()).all()
    
    # Mark incoming messages as read
    unread = [m for m in messages if m.receiver_id == my_id and not m.is_read]
    for m in unread:
        m.is_read = True
        m.read_at = datetime.utcnow()
    if unread:
        db.session.commit()
    
    result = []
    for msg in messages:
        sender = User.query.get(msg.sender_id)
        result.append({
            'id': msg.id,
            'sender_id': msg.sender_id,
            'sender_name': sender.full_name if sender else 'Unknown',
            'sender_role': sender.role if sender else 'Unknown',
            'content': msg.content,
            'message_type': msg.message_type,
            'file_url': msg.file_url,
            'file_name': msg.file_name,
            'meta_data': msg.meta_data,
            'is_read': msg.is_read,
            'timestamp': to_vn_time(msg.timestamp)
        })
    return jsonify(result), 200

@chat_bp.route('/private/<int:user_id>/messages', methods=['POST'])
def send_private_message(user_id):
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': 'Message content is required'}), 400
        
    sender_id = session.get('user_id') or data.get('sender_id')
    if not sender_id:
        return jsonify({'error': 'Unauthorized or missing sender_id'}), 401
        
    now_utc = datetime.utcnow()
    new_msg = Message(
        sender_id=sender_id,
        receiver_id=user_id,
        group_id=None,
        content=data['content'],
        message_type=data.get('message_type', 'text'),
        file_url=data.get('file_url'),
        file_name=data.get('file_name'),
        timestamp=now_utc
    )
    db.session.add(new_msg)
    db.session.commit()
    
    sender = User.query.get(sender_id)
    return jsonify({
        'message': 'Sent successfully',
        'data': {
            'id': new_msg.id,
            'sender_id': sender_id,
            'sender_name': sender.full_name if sender else 'Unknown',
            'sender_role': sender.role if sender else 'Unknown',
            'content': new_msg.content,
            'message_type': new_msg.message_type,
            'file_url': new_msg.file_url,
            'file_name': new_msg.file_name,
            'timestamp': to_vn_time(new_msg.timestamp)
        }
    }), 201

@chat_bp.route('/private/<int:user_id>/media', methods=['GET'])
def get_private_media(user_id):
    my_id = session.get('user_id')
    if not my_id:
        return jsonify({'error': 'Unauthorized'}), 401
        
    messages = Message.query.filter(
        and_(Message.group_id == None, or_(
            and_(Message.sender_id == my_id, Message.receiver_id == user_id),
            and_(Message.sender_id == user_id, Message.receiver_id == my_id)
        ))
    ).order_by(Message.timestamp.desc()).all()
    
    images_videos = []
    files = []
    links = []
    
    url_pattern = re.compile(r'(https?://[^\s]+)')
    
    for msg in messages:
        if msg.message_type in ['image', 'video', 'sticker'] and msg.file_url:
            images_videos.append({
                'id': msg.id,
                'url': msg.file_url,
                'type': msg.message_type,
                'timestamp': to_vn_time(msg.timestamp, '%d/%m/%Y')
            })
        elif msg.message_type == 'file' and msg.file_url:
            files.append({
                'id': msg.id,
                'url': msg.file_url,
                'name': msg.file_name or 'Tài liệu',
                'timestamp': to_vn_time(msg.timestamp, '%d/%m/%Y')
            })
            
        urls = url_pattern.findall(msg.content or '')
        for url in urls:
            links.append({
                'id': msg.id,
                'url': url,
                'timestamp': to_vn_time(msg.timestamp, '%d/%m/%Y')
            })
            
    return jsonify({
        'images_videos': images_videos,
        'files': files,
        'links': links
    }), 200

@chat_bp.route('/private/<int:user_id>/upload', methods=['POST'])
def upload_private_file(user_id):
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        filename = secure_filename(file.filename)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        return jsonify({
            'file_url': f'/{UPLOAD_FOLDER}/{filename}',
            'file_name': filename
        }), 200
