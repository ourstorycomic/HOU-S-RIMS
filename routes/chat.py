from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Message

chat_bp = Blueprint('chat_bp', __name__, url_prefix='/api/chat')

@chat_bp.route('/messages', methods=['POST'])
@jwt_required()
def create_message():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({"msg": "Thiếu nội dung tin nhắn (text)"}), 400
    
    new_message = Message(
        user_id=current_user_id,
        text=data['text']
    )
    db.session.add(new_message)
    db.session.commit()
    
    return jsonify({
        "msg": "Gửi tin nhắn thành công!",
        "message": new_message.to_dict()
    }), 201

@chat_bp.route('/messages', methods=['GET'])
@jwt_required()
def get_messages():
    current_user_id = get_jwt_identity()
    
    # Phân trang
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Lấy tin nhắn của user hiện tại, sắp xếp mới nhất lên đầu
    pagination = Message.query.filter_by(user_id=current_user_id)\
                              .order_by(Message.created_at.desc())\
                              .paginate(page=page, per_page=per_page, error_out=False)
    
    messages = [msg.to_dict() for msg in pagination.items]
    
    return jsonify({
        "messages": messages,
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev
    }), 200
