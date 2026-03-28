# routes/assistant.py
from flask import Blueprint, request, jsonify
import os, pandas as pd, re
from API.InsightEngine import generate_insights

assistant_bp = Blueprint('assistant', __name__)

@assistant_bp.route("/api/assistant", methods=["POST"])
def api_assistant():
    """Endpoint xử lý hỗ trợ phân tích thông minh."""
    try:
        data = request.get_json()
        cols = data.get("cols", [])
        if not cols and data.get("selected_col"): cols = [data.get("selected_col")]
        
        # Đọc dữ liệu nhanh
        stats = ""
        dataset_id = data.get("dataset_id")
        if dataset_id:
            path = os.path.join(os.getcwd(), 'uploads', dataset_id)
            if not os.path.exists(path):
                if os.path.exists(path+'.xlsx'): path+='.xlsx'
                elif os.path.exists(path+'.csv'): path+='.csv'
            
            if os.path.exists(path):
                if path.endswith('.csv'): df = pd.read_csv(path)
                else: df = pd.read_excel(path, engine='openpyxl')
                
                # Tóm tắt 3 cột đầu
                for c in cols[:3]:
                    if c in df.columns:
                        s = df[c].astype(str).value_counts().head(5)
                        stats += f"\n- {c}: " + ", ".join([f"{k}({v})" for k,v in s.items()])

        # Gọi logic xử lý
        prompt = f"{data.get('prompt','')}\nDữ liệu:\n{stats}"
        reply = generate_insights("Bạn là trợ lý NCKH chuyên nghiệp. Phân tích nội dung.", prompt, data.get("model"))
        
        # Tách gợi ý câu hỏi liên quan
        suggestions = []
        if "///" in reply:
            parts = reply.split("///")
            reply = parts[0].strip() # Nội dung chính
            # Lấy phần gợi ý
            if len(parts) > 1:
                raw_sug = parts[1]
                suggestions = [s.strip() for s in re.split(r'[|\n]', raw_sug) if s.strip()]

        return jsonify({"reply": reply, "suggestions": suggestions})
    except Exception as e:
        return jsonify({"reply": f"Lỗi hệ thống: {str(e)}", "suggestions": []})