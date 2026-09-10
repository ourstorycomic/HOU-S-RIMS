import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from models import db, Submission

submissions_bp = Blueprint('submissions_api', __name__, url_prefix='/api/submissions')

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'zip'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@submissions_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    Upload a submission file
    ---
    tags:
      - Submissions
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: file
        type: file
        required: true
        description: The file to upload
      - in: formData
        name: topic_id
        type: integer
        required: true
      - in: formData
        name: uploader_id
        type: integer
        required: true
      - in: formData
        name: type
        type: string
        required: true
    responses:
      201:
        description: File uploaded successfully
      400:
        description: Invalid request
    """
    from app import app # to get UPLOAD_FOLDER
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if not request.form.get('topic_id') or not request.form.get('uploader_id') or not request.form.get('type'):
        return jsonify({'error': 'Missing metadata (topic_id, uploader_id, type)'}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            new_submission = Submission(
                topic_id=int(request.form['topic_id']),
                uploader_id=int(request.form['uploader_id']),
                file_url=file_path,
                type=request.form['type']
            )
            db.session.add(new_submission)
            db.session.commit()
            return jsonify({'message': 'File uploaded successfully', 'file_url': file_path}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
            
    return jsonify({'error': 'File type not allowed'}), 400
