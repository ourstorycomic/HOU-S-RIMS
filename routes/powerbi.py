# routes/powerbi.py
from flask import Blueprint, request, jsonify, Response
from data_store import DATASETS
import pandas as pd
import io

powerbi_bp = Blueprint('powerbi', __name__)

@powerbi_bp.route("/api/powerbi/data", methods=["GET", "POST"])
def api_powerbi_data():
    """
    Endpoint for Power BI to consume data.
    """
    dataset_id = request.args.get("dataset_id")
    if not dataset_id:
        # Try to extract from Path if the URL ends in something like /dataset_id.csv
        path = request.path
        if path.endswith('.csv'):
            dataset_id = path.split('/')[-1].replace('.csv', '')
    
    if not dataset_id:
        data = request.get_json(silent=True)
        if data:
            dataset_id = data.get("dataset_id")
    
    if not dataset_id or dataset_id not in DATASETS:
        return jsonify({"error": "Dataset not found."}), 404
        
    df = DATASETS[dataset_id]['df']
    
    # Check output format - Default to CSV for Power BI Web source
    format = request.args.get("format", "csv")
    
    if format == "csv":
        output = io.StringIO()
        # Use UTF-8 with BOM for Excel/Power BI font compatibility
        df.to_csv(output, index=False, encoding='utf-8-sig') 
        return Response(
            output.getvalue(), 
            mimetype="text/csv", 
            headers={"Content-disposition": "inline; filename=data.csv"}
        )
    
    return jsonify(df.to_dict(orient='records'))

@powerbi_bp.route("/api/powerbi/generate_info", methods=["POST"])
def api_generate_pbi_info():
    """Generates the URL and instructions for Power BI integration."""
    data = request.get_json()
    dataset_id = data.get("dataset_id")
    if not dataset_id:
        return jsonify({"error": "Dataset not found"}), 404
        
    base_url = request.host_url.rstrip('/')
    # Adding .csv at the end to help Power BI auto-detect format
    pbi_url = f"{base_url}/api/powerbi/data?dataset_id={dataset_id}&format=csv&_v=.csv"
    
    return jsonify({
        "url": pbi_url,
        "instructions": [
            "1. Mở Power BI Desktop.",
            "2. Chọn 'Lấy dữ liệu' (Get Data) -> 'Web'.",
            "3. Dán URL bên trên vào.",
            "4. Chọn 'Kết nối' (Connect) -> Hệ thống sẽ tự động nhận diện CSV."
        ]
    })
