# routes/analysis.py
from flask import Blueprint, request, jsonify
from data_store import DATASETS
from API.statistics import calculate_reliability, calculate_correlation, calculate_regression
import pandas as pd

analysis_bp = Blueprint('analysis_bp', __name__)

@analysis_bp.route("/api/analysis/reliability", methods=["POST"])
def api_reliability():
    data = request.get_json()
    dataset_id = data.get("dataset_id")
    cols = data.get("cols", [])
    
    if not dataset_id or dataset_id not in DATASETS:
        return jsonify({"error": "Dataset not found"}), 404
        
    df = DATASETS[dataset_id]['df']
    result = calculate_reliability(df, cols)
    
    return jsonify(result)

@analysis_bp.route("/api/analysis/correlation", methods=["POST"])
def api_correlation():
    data = request.get_json()
    dataset_id = data.get("dataset_id")
    cols = data.get("cols", [])
    
    if not dataset_id or dataset_id not in DATASETS:
        return jsonify({"error": "Dataset not found"}), 404
        
    df = DATASETS[dataset_id]['df']
    result = calculate_correlation(df, cols)
    
    return jsonify(result)

@analysis_bp.route("/api/analysis/regression", methods=["POST"])
def api_regression():
    data = request.get_json()
    dataset_id = data.get("dataset_id")
    target = data.get("target")
    predictors = data.get("predictors", [])
    
    if not dataset_id or dataset_id not in DATASETS:
        return jsonify({"error": "Dataset not found"}), 404
        
    df = DATASETS[dataset_id]['df']
    result = calculate_regression(df, target, predictors)
    
    return jsonify(result)

@analysis_bp.route("/api/analysis/descriptive", methods=["POST"])
def api_descriptive():
    data = request.get_json()
    dataset_id = data.get("dataset_id")
    cols = data.get("cols", [])
    
    if not dataset_id or dataset_id not in DATASETS:
        return jsonify({"error": "Dataset not found"}), 404
        
    df = DATASETS[dataset_id]['df']
    stats_df = df[cols].describe().round(3)
    
    # Thêm variance, kurtosis, skewness nếu cần chuyên nghiệp hơn
    more_stats = pd.DataFrame({
        "variance": df[cols].var(),
        "skewness": df[cols].skew(),
        "kurtosis": df[cols].kurtosis()
    }).T.round(3)
    
    full_stats = pd.concat([stats_df, more_stats])
    
    return jsonify({
        "columns": cols,
        "stats": full_stats.to_dict()
    })
