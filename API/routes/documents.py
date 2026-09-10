import os
from flask import Blueprint, send_from_directory, jsonify
from werkzeug.exceptions import NotFound

documents_bp = Blueprint('documents', __name__)

BASE_DIR = os.getcwd()
TEMPLATES_FOLDER = os.path.join(BASE_DIR, 'data', 'templates')

os.makedirs(TEMPLATES_FOLDER, exist_ok=True)

@documents_bp.route('/api/documents/templates/<path:filename>', methods=['GET'])
def get_document_template(filename):
    """
    Tải file tài liệu mẫu
    ---
    tags:
      - Documents
    parameters:
      - in: path
        name: filename
        type: string
        required: true
        description: Tên file mẫu (VD: BÀI LÀM CHÍNH.docx)
    responses:
      200:
        description: Tải file thành công
      404:
        description: Không tìm thấy file
    """
    try:
        return send_from_directory(TEMPLATES_FOLDER, filename, as_attachment=True)
        
    except NotFound:
        return jsonify({
            "success": False, 
            "message": f"Không tìm thấy file mẫu '{filename}' trong hệ thống hoặc truy cập bị từ chối."
        }), 404
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi server: {str(e)}"}), 500