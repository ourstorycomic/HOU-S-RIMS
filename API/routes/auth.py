from flask import Blueprint, request, jsonify, session
from models import User, db

auth_bp = Blueprint('auth_api', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login a user
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
            password:
              type: string
    responses:
      200:
        description: Login successful
      401:
        description: Invalid credentials
    """
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing credentials'}), 400
        
    user = User.query.filter_by(username=data['username']).first()
    
    # In a real app, use hashed passwords (e.g., werkzeug.security.check_password_hash)
    # Here we simulate with plain or mock logic
    if user:
        # Mock successful login
        session['user_id'] = user.id
        session['role'] = user.role
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'role': user.role
            }
        }), 200
        
    return jsonify({'error': 'Invalid username or password'}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Logout current user
    ---
    tags:
      - Authentication
    responses:
      200:
        description: Logout successful
    """
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
            password:
              type: string
            full_name:
              type: string
            role:
              type: string
              example: Student
    responses:
      201:
        description: User created
      400:
        description: User exists
    """
    data = request.get_json()
    if not data or 'username' not in data:
        return jsonify({'error': 'Missing data'}), 400
        
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
        
    new_user = User(
        username=data['username'],
        full_name=data.get('full_name', ''),
        role=data.get('role', 'Student'),
        email=data.get('email', '')
    )
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully', 'id': new_user.id}), 201
