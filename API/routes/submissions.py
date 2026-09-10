import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from models import db, Submission 
submissions_bp = Blueprint('submissions', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'zip', 'rar', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@submissions_bp.route('/api/submissions/upload', methods=['POST'])
def upload_submission_file():
    """
    Upload file báo cáo/tài liệu
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
        description: Chọn file cần tải lên
      - in: formData
        name: topic_id
        type: integer
        required: false
        description: ID của đề tài (nếu có)
    responses:
      201:
        description: Upload thành công
    """
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "Không tìm thấy file gửi lên."}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"success": False, "message": "Tên file rỗng. Vui lòng chọn file."}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'submissions')
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        
        try:
            file.save(file_path)
            
            topic_id = request.form.get('topic_id') 
            new_submission = Submission(
                filename=filename,
                file_path=f"uploads/submissions/{filename}",
            )
            
            db.session.add(new_submission)
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "Upload file và lưu cơ sở dữ liệu thành công.",
                "data": {
                    "id": new_submission.id,
                    "filename": filename,
                    "file_path": f"uploads/submissions/{filename}" 
                }
            }), 201
            
        except Exception as e:
            db.session.rollback() 
            return jsonify({"success": False, "message": f"Lỗi hệ thống khi lưu file: {str(e)}"}), 500
            
    return jsonify({"success": False, "message": "Định dạng file không được hỗ trợ."}), 400