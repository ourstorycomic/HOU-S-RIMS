import pandas as pd
import json
import os

excel_path = r'd:\develop\test\HOU-S-RIMS\data\date_upload\Tong_hop_du_lieu_khao_sat_day_du_sach_final.xlsx'
json_path = r'd:\develop\test\HOU-S-RIMS\data\data.json'

def update_mapping():
    try:
        df = pd.read_excel(excel_path)
        mapping = {
            "__comment__": "FILE ĐƯỢC CẬP NHẬT TỰ ĐỘNG TỪ EXCEL KHẢO SÁT SÁCH FINAL",
            "default_likert": {
                "1": "Hoàn toàn không đồng ý",
                "2": "Không đồng ý",
                "3": "Phân vân",
                "4": "Đồng ý",
                "5": "Hoàn toàn đồng ý"
            }
        }

        # Các thang đo phổ biến
        likert_5 = mapping["default_likert"]
        binary_01 = {"0": "Không", "1": "Có"}
        
        for col in df.columns:
            unique_vals = [str(x) for x in df[col].dropna().unique()]
            
            # Nếu là thang đo 1-5
            if all(v in ["1","2","3","4","5"] for v in unique_vals) and len(unique_vals) >= 2:
                mapping[col] = likert_5
            # Nếu là Có/Không 0-1
            elif all(v in ["0","1"] for v in unique_vals):
                mapping[col] = binary_01
            # Thêm các trường hợp đặc biệt cho Năm học (nếu có)
            if "năm thứ mấy" in col.lower():
                mapping[col] = {
                    "1": "Năm 1", "2": "Năm 2", "3": "Năm 3", "4": "Năm 4", "5": "Năm cuối/Khác"
                }
            if "vai trò" in col.lower() or "động lực" in col.lower():
                mapping[col] = binary_01

        # Lưu lại
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        print(f"Thành công! Đã mapping {len(mapping)-2} cột vào data.json")
        
    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == "__main__":
    update_mapping()
