#routes/cleaning.py
from flask import Blueprint, request, jsonify
import os
import pandas as pd

clean_bp = Blueprint('clean', __name__)

@clean_bp.route("/api/clean", methods=["POST"])
def api_clean():
    try:
        data = request.get_json()
        dataset_id = data.get('dataset_id')
        drop_na = data.get('drop_na', False)
        drop_dup = data.get('drop_duplicates', False)

        if not dataset_id: return jsonify({"error": "Chưa có file"}), 400

        base_dir = os.getcwd()
        file_path = os.path.join(base_dir, 'uploads', dataset_id)

        # [FIX] Tự động dò đuôi file
        real_path = file_path
        if not os.path.exists(real_path):
            if os.path.exists(file_path + '.xlsx'): real_path = file_path + '.xlsx'
            elif os.path.exists(file_path + '.csv'): real_path = file_path + '.csv'
            else: return jsonify({"error": "File không tồn tại"}), 404

        # Đọc file
        if real_path.endswith('.csv'): df = pd.read_csv(real_path)
        else: df = pd.read_excel(real_path)

        old_len = len(df)

        # Xử lý làm sạch
        if drop_na: df.dropna(inplace=True)
        if drop_dup: df.drop_duplicates(inplace=True)

        new_len = len(df)

        # [TỐI ƯU] Chỉ ghi file nếu có sự thay đổi
        if new_len < old_len:
            if real_path.endswith('.csv'): df.to_csv(real_path, index=False)
            else: df.to_excel(real_path, index=False)

        return jsonify({
            "message": "OK", 
            "old_shape": (old_len, df.shape[1]), 
            "new_shape": (new_len, df.shape[1])
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500