# routes/document.py
from flask import Blueprint, request, send_file
import os
import io
import base64
import pandas as pd
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

document_bp = Blueprint('document', __name__)

def add_heading(doc, text, level):
    h = doc.add_heading(text, level)
    run = h.runs[0]
    run.font.color.rgb = RGBColor(0, 51, 102) # Màu xanh đậm chuyên nghiệp

def get_stats_table(df, col):
    """Tạo bảng thống kê tần suất cho 1 cột"""
    try:
        # Đếm số lượng và %
        val_counts = df[col].value_counts()
        total = len(df)
        stats = []
        for idx, val in val_counts.items():
            pct = (val / total) * 100
            stats.append([str(idx), str(val), f"{pct:.2f}%"])
        return stats
    except: return []

@document_bp.route("/api/generate_doc", methods=["POST"])
def generate_doc():
    try:
        data = request.get_json()
        
        # Dữ liệu từ Client
        image_data = data.get('image')
        col_names = data.get('col_name', '').split(',') # Danh sách cột
        dataset_id = data.get('dataset_id')
        ai_analysis = data.get('ai_analysis', 'Chưa có phân tích từ AI.')
        
        # Đọc dữ liệu gốc để tính toán
        df = None
        if dataset_id:
            path = os.path.join(os.getcwd(), 'uploads', dataset_id)
            if not os.path.exists(path):
                if os.path.exists(path+'.xlsx'): path+='.xlsx'
                elif os.path.exists(path+'.csv'): path+='.csv'
            
            if os.path.exists(path):
                if path.endswith('.csv'): df = pd.read_csv(path)
                else: df = pd.read_excel(path, engine='openpyxl')

        # --- TẠO FILE WORD ---
        doc = Document()
        
        # 1. TIÊU ĐỀ
        title = doc.add_heading('BÁO CÁO PHÂN TÍCH DỮ LIỆU NCKH', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_paragraph(f'Ngày xuất báo cáo: {pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")}')
        doc.add_paragraph(f'Nguồn dữ liệu: {dataset_id}')
        doc.add_paragraph(f'Tiêu chí phân tích: {", ".join(col_names)}')
        doc.add_paragraph('_' * 50)

        # 2. BIỂU ĐỒ
        add_heading(doc, 'I. BIỂU ĐỒ TRỰC QUAN', 1)
        if image_data:
            try:
                if "," in image_data: image_data = image_data.split(",")[1]
                image_bytes = io.BytesIO(base64.b64decode(image_data))
                doc.add_picture(image_bytes, width=Inches(6))
                caption = doc.add_paragraph('Hình 1. Biểu đồ phân tích dữ liệu')
                caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
            except Exception as e:
                doc.add_paragraph(f"[Lỗi ảnh: {e}]")

        # 3. BẢNG SỐ LIỆU CHI TIẾT (Phần bạn cần)
        add_heading(doc, 'II. SỐ LIỆU THỐNG KÊ CHI TIẾT', 1)
        
        if df is not None:
            for col in col_names:
                col = col.strip()
                if col in df.columns:
                    doc.add_heading(f'2.{col_names.index(col)+1}. Phân bố: {col}', level=2)
                    
                    # Lấy thống kê
                    stats = get_stats_table(df, col)
                    if stats:
                        # Tạo bảng trong Word
                        table = doc.add_table(rows=1, cols=3)
                        table.style = 'Table Grid'
                        hdr_cells = table.rows[0].cells
                        hdr_cells[0].text = 'Câu trả lời / Mức độ'
                        hdr_cells[1].text = 'Số lượng (N)'
                        hdr_cells[2].text = 'Tỷ lệ (%)'
                        
                        # Đổ dữ liệu vào
                        for item in stats:
                            row_cells = table.add_row().cells
                            row_cells[0].text = str(item[0])
                            row_cells[1].text = str(item[1])
                            row_cells[2].text = str(item[2])
                        
                        doc.add_paragraph(f"Tổng mẫu khảo sát: {len(df)}")
                        doc.add_paragraph("") # Xuống dòng

        # 4. PHÂN TÍCH TỪ AI (Lấy từ khung chat)
        add_heading(doc, 'III. NHẬN XÉT & ĐÁNH GIÁ (AI ANALYTICS)', 1)
        # Làm sạch văn bản AI (xóa các ký tự markdown)
        clean_ai = ai_analysis.replace('*', '').replace('#', '')
        p = doc.add_paragraph(clean_ai)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        # 5. KẾT LUẬN
        add_heading(doc, 'IV. KẾT LUẬN', 1)
        doc.add_paragraph('Dựa trên các số liệu và phân tích trên, nhóm nghiên cứu có thể đưa ra các giải pháp phù hợp...')

        # --- XUẤT FILE ---
        f = io.BytesIO()
        doc.save(f)
        f.seek(0)
        
        return send_file(
            f,
            as_attachment=True,
            download_name=f'Bao_cao_Chi_tiet_{pd.Timestamp.now().strftime("%H%M")}.docx',
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    except Exception as e:
        print(f"Report Error: {e}")
        return {"error": str(e)}, 500