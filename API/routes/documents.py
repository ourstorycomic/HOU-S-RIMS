import os
from flask import Blueprint, send_file, jsonify

documents_bp = Blueprint('documents', __name__)

BASE_DIR = os.getcwd()
TEMPLATES_FOLDER = os.path.join(BASE_DIR, 'data', 'templates')

os.makedirs(TEMPLATES_FOLDER, exist_ok=True)

@documents_bp.route('/api/documents/templates/<path:filename>', methods=['GET'])
def get_document_template(filename):
    try:
        file_path = os.path.join(TEMPLATES_FOLDER, filename)
        
        if not os.path.exists(file_path):
            return jsonify({
                "success": False, 
                "message": f"Không tìm thấy file mẫu '{filename}' trong hệ thống."
            }), 404
            
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi server: {str(e)}"}), 500