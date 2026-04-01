# routes/analysis.py
from flask import Blueprint, request, jsonify
from data_store import DATASETS
from API.statistics import calculate_reliability, calculate_correlation, calculate_regression, calculate_chi2, calculate_anova, calculate_descriptive_detailed
import pandas as pd

analysis_bp = Blueprint('analysis_bp', __name__)

# 1. API ĐỘ TIN CẬY (CRONBACH'S ALPHA)
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

# 2. API TƯƠNG QUAN (CORRELATION)
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

# 3. API HỒI QUY (REGRESSION)
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

@analysis_bp.route("/api/analysis/chi2", methods=["POST"])
def api_chi2():
    data = request.get_json()
    dataset_id = data.get("dataset_id")
    cols = data.get("cols", [])
    
    if not dataset_id or dataset_id not in DATASETS:
        return jsonify({"error": "Dataset not found"}), 404
    if len(cols) < 2:
        return jsonify({"error": "Cần ít nhất 2 cột"}), 400
        
    df = DATASETS[dataset_id]['df']
    result = calculate_chi2(df, cols[0], cols[1])
    return jsonify(result)

@analysis_bp.route("/api/analysis/anova", methods=["POST"])
def api_anova():
    data = request.get_json()
    dataset_id = data.get("dataset_id")
    cols = data.get("cols", [])
    
    if not dataset_id or dataset_id not in DATASETS:
        return jsonify({"error": "Dataset not found"}), 404
    if len(cols) < 2:
        return jsonify({"error": "Cần ít nhất 2 cột (Nhóm và Giá trị)"}), 400
        
    df = DATASETS[dataset_id]['df']
    result = calculate_anova(df, cols[0], cols[1])
    return jsonify(result)

@analysis_bp.route("/api/analysis/descriptive", methods=["POST"])
def api_descriptive():
    data = request.get_json()
    dataset_id = data.get("dataset_id")
    cols = data.get("cols", [])
    
    if not dataset_id or dataset_id not in DATASETS:
        return jsonify({"error": "Dataset not found"}), 404
        
    df = DATASETS[dataset_id]['df']
    result = calculate_descriptive_detailed(df, cols)
    return jsonify(result)
