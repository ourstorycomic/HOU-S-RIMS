# routes/plot.py
from flask import Blueprint, request, jsonify
from API.main import plot_multiple
import pandas as pd
import os

plot_bp = Blueprint('plot', __name__)

@plot_bp.route("/api/plot", methods=["POST"])
def api_plot():
    try:
        data = request.get_json()
        dataset_id = data.get('dataset_id')
        plots_req = data.get('plots', [])
        
        if not dataset_id:
            return jsonify({"error": "Thiếu dataset_id"}), 400

        # Tìm đường dẫn file (hỗ trợ cả csv và xlsx)
        base_dir = os.getcwd()
        path = os.path.join(base_dir, 'uploads', dataset_id)
        
        if not os.path.exists(path):
            if os.path.exists(path + '.xlsx'): path += '.xlsx'
            elif os.path.exists(path + '.csv'): path += '.csv'
            else: return jsonify({"error": "File không tồn tại"}), 404

        # Đọc file với Pandas
        # Dùng engine='openpyxl' cho Excel để ổn định hơn
        if path.endswith('.csv'): 
            df = pd.read_csv(path)
        else: 
            df = pd.read_excel(path, engine='openpyxl')

        # Gọi hàm vẽ từ API/main.py
        images = plot_multiple(df, plots_req)
        
        return jsonify({"images": images})

    except Exception as e:
        print(f"Lỗi API Plot: {e}")
        return jsonify({"error": str(e)}), 500