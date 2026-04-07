# routes/powerbi.py
from flask import Blueprint, request, jsonify, Response
from data_store import DATASETS
import pandas as pd
import io
import re

def normalize_text(text):
    """Normalize text for fuzzy matching."""
    if not text or not isinstance(text, str): return ""
    text = re.sub(r'[\[\]\n\r\t]', ' ', text.lower()).strip()
    return re.sub(r'\s+', ' ', text)

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
        
    df = DATASETS[dataset_id]['df'].copy()
    
    # [SMART HEADERS] Attempt to use descriptive headers
    use_labels = request.args.get("labels", "true").lower() == "true"
    
    if use_labels:
        # 1. Try to find SPSS labels if available
        meta = DATASETS[dataset_id].get('meta')
        if meta and hasattr(meta, 'column_names_to_labels'):
            df.rename(columns=meta.column_names_to_labels, inplace=True)
        else:
            # 2. Try to match with survey mapping keys from data.json
            from API.main import _SURVEY_MAP
            
            # Pre-normalize map keys for faster fuzzy matching
            normalized_map = {normalize_text(k): k for k in _SURVEY_MAP.keys()}
            
            new_cols = {}
            found_promotion = False
            
            for col in df.columns:
                col_norm = normalize_text(str(col))
                
                # Check if column name itself is a match
                if col_norm in normalized_map:
                    new_cols[col] = normalized_map[col_norm]
                    continue
                
                # If column is generic, check the first row value
                if str(col).startswith("Column") and len(df) > 0:
                    val = str(df[col].iloc[0]).strip()
                    val_norm = normalize_text(val)
                    if val_norm in normalized_map:
                        new_cols[col] = normalized_map[val_norm]
                        found_promotion = True
            
            if new_cols:
                df.rename(columns=new_cols, inplace=True)
                # If we promoted a first row, we MUST drop it
                if found_promotion:
                    df = df.iloc[1:].reset_index(drop=True)

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
