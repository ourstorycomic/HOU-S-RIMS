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
        
        # Đọc dữ liệu nhanh và tạo tóm tắt chi tiết cho AI
        stats = ""
        dataset_id = data.get("dataset_id")
        if dataset_id:
            path = os.path.join(os.getcwd(), 'uploads', dataset_id)
            if not os.path.exists(path):
                for ext in ['.xlsx', '.csv', '.sav']:
                    if os.path.exists(path + ext): path += ext; break
            
            if os.path.exists(path):
                if path.endswith('.csv'): df = pd.read_csv(path)
                elif path.endswith('.sav'): 
                    import pyreadstat
                    df, _ = pyreadstat.read_sav(path)
                else: df = pd.read_excel(path, engine='openpyxl')
                
                # Tóm tắt các cột quan trọng (tối đa 5 cột)
                target_cols = cols if cols else df.columns[:5]
                for c in target_cols[:5]:
                    if c in df.columns:
                        counts = df[c].value_counts().head(5)
                        total = len(df)
                        stats += f"\n- Biến '{c}': " + ", ".join([f"{k} (n={v}, {v/total*100:.1f}%)" for k,v in counts.items()])

        # Gọi logic xử lý với Prompt giàu ngữ cảnh
        base_prompt = data.get('prompt','')
        full_prompt = f"{base_prompt}\n\nDỮ LIỆU THỐNG KÊ CHI TIẾT:\n{stats}\n\n(Yêu cầu: Phân tích sâu sắc, dùng văn phong NCKH chuẩn mực)"
        reply = generate_insights("Bạn là một Chuyên gia phân tích dữ liệu cao cấp. Hãy đưa ra các nhận xét chuyên môn, logic và thực tiễn.", full_prompt, data.get("model"))
        
        # Tách gợi ý câu hỏi liên quan
        suggestions = []
        if "///" in reply:
            parts = reply.split("///")
            reply = parts[0].strip()
            if len(parts) > 1:
                suggestions = [s.strip() for s in re.split(r'[|\n]', parts[1]) if s.strip()]

        return jsonify({"reply": reply, "suggestions": suggestions})
    except Exception as e:
        return jsonify({"reply": f"Lỗi hệ thống: {str(e)}", "suggestions": []})