from flask import Blueprint, jsonify, send_file
from models import DocumentTemplate
import os

documents_bp = Blueprint('documents_api', __name__, url_prefix='/api/documents')

@documents_bp.route('/templates', methods=['GET'])
def get_templates():
    """
    Get list of document templates
    ---
    tags:
      - Documents
    responses:
      200:
        description: List of templates
    """
    templates = DocumentTemplate.query.all()
    result = []
    for t in templates:
        result.append({
            'id': t.id,
            'name': t.name,
            'file_url': t.file_url,
            'type': t.type
        })
    return jsonify(result), 200

@documents_bp.route('/templates/<int:template_id>/download', methods=['GET'])
def download_template(template_id):
    """
    Download a template file
    ---
    tags:
      - Documents
    parameters:
      - in: path
        name: template_id
        type: integer
        required: true
    responses:
      200:
        description: File downloaded
      404:
        description: Template not found
    """
    template = DocumentTemplate.query.get(template_id)
    if not template or not os.path.exists(template.file_url):
        return jsonify({'error': 'Template not found'}), 404
        
    return send_file(template.file_url, as_attachment=True)