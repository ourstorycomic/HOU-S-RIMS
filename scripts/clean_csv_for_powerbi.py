import os

# Đường dẫn file
input_file = r'd:\develop\test\HOU-S-RIMS\data\Tong_hop_du_lieu_khao_sat_day_du_sach_final.csv'
output_file = r'd:\develop\test\HOU-S-RIMS\data\Tong_hop_du_lieu_CLEAN.csv'

def robust_clean_csv():
    if not os.path.exists(input_file):
        print(f"[ERROR] Không tìm thấy file: {input_file}")
        return

    print(f"[INFO] Đang xử lý file thủ công: {input_file}")
    
    try:
        # Đọc toàn bộ nội dung file dưới dạng list các dòng
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if len(lines) < 19:
            print(f"[ERROR] File chỉ có {len(lines)} dòng, không đủ để xử lý.")
            return

        # 1. Xử lý Header: Nối dòng 1 và dòng 2
        # Chúng ta loại bỏ dấu ngoặc kép trong tiêu đề để tránh lỗi "EOF inside string" khi nạp vào Power BI
        h1 = lines[0].strip()
        h2 = lines[1].strip()
        # Nối h1 và h2, loại bỏ ngoặc kép dư thừa để Power BI không bị lỗi parse
        header = (h1 + " " + h2).replace('"', '')
        
        # 2. Lấy dữ liệu thực tế (Bắt đầu từ dòng 19, index 18)
        data_lines = lines[18:]
        
        # 3. Ghi file output
        with open(output_file, 'w', encoding='utf-8-sig') as f:
            # Ghi tiêu đề đã làm sạch
            f.write(header + "\n")
            # Ghi từng dòng dữ liệu
            for line in data_lines:
                f.write(line.strip() + "\n")
        
        print(f"[SUCCESS] Đã tạo file sạch tại: {output_file}")
        print(f"[INFO] Đã xử lý {len(data_lines)} dòng dữ liệu.")
        print("[TIP] Bây giờ bạn hãy nạp file 'Tong_hop_du_lieu_CLEAN.csv' vào Power BI.")

    except Exception as e:
        print(f"[ERROR] Có lỗi xảy ra: {str(e)}")

if __name__ == "__main__":
    robust_clean_csv()
