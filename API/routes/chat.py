from flask import Blueprint, request, jsonify, session
from models import db, Message, User

chat_bp = Blueprint('chat_api', __name__, url_prefix='/api/chat')

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
            'timestamp': msg.timestamp.strftime('%H:%M %d/%m/%Y')
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
                'timestamp': msg.timestamp.strftime('%d/%m/%Y')
            })
        
        # Group files
        elif msg.message_type == 'file' and msg.file_url:
            files.append({
                'id': msg.id,
                'url': msg.file_url,
                'name': msg.file_name or 'Tài liệu',
                'timestamp': msg.timestamp.strftime('%d/%m/%Y')
            })
            
        # Extract links from text
        urls = url_pattern.findall(msg.content or '')
        for url in urls:
            links.append({
                'id': msg.id,
                'url': url,
                'timestamp': msg.timestamp.strftime('%d/%m/%Y')
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
        
    new_msg = Message(
        sender_id=sender_id,
        group_id=group_id,
        content=data['content'],
        message_type=data.get('message_type', 'text'),
        file_url=data.get('file_url'),
        file_name=data.get('file_name')
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
            'timestamp': new_msg.timestamp.strftime('%H:%M %d/%m/%Y')
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
        
    # Get distinct users we chatted with
    # This requires querying messages where sender_id=me or receiver_id=me
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
                result.append({
                    'id': other_user.id,
                    'name': other_user.full_name,
                    'role': other_user.role,
                    'last_message': msg.content if msg.message_type == 'text' else f'[{msg.message_type}]',
                    'timestamp': msg.timestamp.strftime('%H:%M %d/%m')
                })
    return jsonify(result), 200

@chat_bp.route('/private/<int:user_id>/messages', methods=['GET'])
def get_private_messages(user_id):
    my_id = session.get('user_id')
    if not my_id:
        return jsonify({'error': 'Unauthorized'}), 401
        
    messages = Message.query.filter(
        and_(Message.group_id == None, or_(
            and_(Message.sender_id == my_id, Message.receiver_id == user_id),
            and_(Message.sender_id == user_id, Message.receiver_id == my_id)
        ))
    ).order_by(Message.timestamp.asc()).all()
    
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
            'timestamp': msg.timestamp.strftime('%H:%M %d/%m/%Y')
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
        
    new_msg = Message(
        sender_id=sender_id,
        receiver_id=user_id,
        group_id=None,
        content=data['content'],
        message_type=data.get('message_type', 'text'),
        file_url=data.get('file_url'),
        file_name=data.get('file_name')
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
            'timestamp': new_msg.timestamp.strftime('%H:%M %d/%m/%Y')
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
                'timestamp': msg.timestamp.strftime('%d/%m/%Y')
            })
        elif msg.message_type == 'file' and msg.file_url:
            files.append({
                'id': msg.id,
                'url': msg.file_url,
                'name': msg.file_name or 'Tài liệu',
                'timestamp': msg.timestamp.strftime('%d/%m/%Y')
            })
            
        urls = url_pattern.findall(msg.content or '')
        for url in urls:
            links.append({
                'id': msg.id,
                'url': url,
                'timestamp': msg.timestamp.strftime('%d/%m/%Y')
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
