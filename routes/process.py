#routes/process.py
from flask import Blueprint, request, jsonify
from data_store import DATASETS

process_bp = Blueprint('process', __name__)

@process_bp.route("/api/clean", methods=["POST"])
def api_clean():
    data = request.get_json()
    dataset_id = data.get("dataset_id")
    
    if not dataset_id or dataset_id not in DATASETS:
        return jsonify({"error": "Dataset not found"}), 404
    
    df = DATASETS[dataset_id]['df']
    old_len = len(df)
    
    if data.get("drop_na"):
        df = df.dropna(how='all') # Xóa dòng trắng
    
    if data.get("drop_duplicates"):
        df = df.drop_duplicates()
        
    DATASETS[dataset_id]['df'] = df
    new_len = len(df)
    
    return jsonify({
        "message": "Cleaned",
        "removed": old_len - new_len,
        "remaining": new_len,
        "columns": list(df.columns)
    })