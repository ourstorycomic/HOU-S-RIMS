import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

submissions_bp = Blueprint('submissions', __name__)

BASE_DIR = os.getcwd()
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'data', 'uploads', 'submissions')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
    responses:
      200:
        description: Upload thành công
    """
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "Không tìm thấy file gửi lên."}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"success": False, "message": "Tên file rỗng. Vui lòng chọn file."}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        try:
            file.save(file_path)
            
            return jsonify({
                "success": True,
                "message": "Upload file thành công.",
                "data": {
                    "filename": filename,
                    "file_path": f"data/uploads/submissions/{filename}" 
                }
            }), 201
            
        except Exception as e:
            return jsonify({"success": False, "message": f"Lỗi hệ thống khi lưu file: {str(e)}"}), 500
            
    return jsonify({"success": False, "message": "Định dạng file không được hỗ trợ."}), 400