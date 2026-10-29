import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from app import app
from models import db, User, Batch, Group, Topic, GroupMember, Notification, Message

def setup_database():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database recreated.")

        u_admin = User(username="admin", password_hash=generate_password_hash("admin123"), full_name="Admin Truong HOU", email="admin@hou.edu.vn", role="admin", faculty="Phong Quan ly NCKH")
        u_faculty = User(username="faculty1", password_hash=generate_password_hash("faculty123"), full_name="PGS.TS Khoa CNTT", email="faculty@hou.edu.vn", role="faculty", faculty="Khoa Công nghệ Thông tin")

        lecturers = [
            User(username="lecturer1", password_hash=generate_password_hash("lecturer123"), full_name="TS. Nguyễn Văn An", email="nva@hou.edu.vn", role="Lecturer", faculty="Khoa Công nghệ Thông tin", bio="Trí tuệ nhân tạo (AI), Machine Learning, Khai phá dữ liệu lớn và Ứng dụng Computer Vision trong xử trị hình ảnh y tế."),
            User(username="lecturer2", password_hash=generate_password_hash("lecturer123"), full_name="ThS. Lê Thị Bình", email="ltb@hou.edu.vn", role="Lecturer", faculty="Khoa Luật", bio="Pháp luật về Thương mại điện tử, Luật Sở hữu trí tuệ số, Khung pháp lý về bảo vệ dữ liệu cá nhân & Trí tuệ nhân tạo."),
            User(username="lecturer3", password_hash=generate_password_hash("lecturer123"), full_name="PGS.TS. Trần Quốc Tuấn", email="tuantq@hou.edu.vn", role="Lecturer", faculty="Khoa Công nghệ Thông tin", bio="An toàn không gian mạng (Cybersecurity), Mạng máy tính & Điện toán đám mây (Cloud Computing), Hệ thống IoT thông minh."),
            User(username="lecturer4", password_hash=generate_password_hash("lecturer123"), full_name="TS. Phạm Minh Đức", email="pmduc@hou.edu.vn", role="Lecturer", faculty="Khoa Kinh tế & QTKD", bio="Kinh tế số & Thương mại điện tử, Quản trị chuỗi cung ứng bền vững, Phân tích hành vi tiêu dùng đa kênh."),
            User(username="lecturer5", password_hash=generate_password_hash("lecturer123"), full_name="ThS. Phạm Thu Trang", email="trangpt@hou.edu.vn", role="Lecturer", faculty="Khoa Kinh tế & QTKD", bio="Tài chính doanh nghiệp, Công nghệ tài chính (Fintech), Quản trị rủi ro và Đầu tư bền vững ESG."),
            User(username="lecturer6", password_hash=generate_password_hash("lecturer123"), full_name="TS. Vũ Đình Dũng", email="dungvd@hou.edu.vn", role="Lecturer", faculty="Khoa Kinh tế & QTKD", bio="Marketing số, Tối ưu hóa phễu bán hàng đa nền tảng, Chiến lược thương hiệu số cho doanh nghiệp khởi nghiệp."),
            User(username="lecturer7", password_hash=generate_password_hash("lecturer123"), full_name="TS. Đỗ Quỳnh Anh", email="anhdq@hou.edu.vn", role="Lecturer", faculty="Khoa Ngoại ngữ", bio="Ngôn ngữ học ứng dụng, Ứng dụng AI và Công nghệ trong giảng dạy ngoại ngữ (CALL), Dịch thuật tự động và bản địa hóa."),
            User(username="lecturer8", password_hash=generate_password_hash("lecturer123"), full_name="ThS. Nguyễn Hoàng Long", email="longnh@hou.edu.vn", role="Lecturer", faculty="Khoa Ngoại ngữ", bio="Giao tiếp liên văn hóa trong kỷ nguyên số, Phân tích diễn ngôn truyền thông tiếng Anh, Phương pháp sư phạm ngôn ngữ hiện đại."),
            User(username="lecturer9", password_hash=generate_password_hash("lecturer123"), full_name="PGS.TS. Trần Văn Hùng", email="hungtv@hou.edu.vn", role="Lecturer", faculty="Khoa Luật", bio="Luật Kinh tế quốc tế, Giải quyết tranh chấp thương mại xuyên biên giới, Pháp luật đầu tư nước ngoài và hiệp định FTA."),
            User(username="lecturer10", password_hash=generate_password_hash("lecturer123"), full_name="TS. Vũ Thị Lan Anh", email="lananhvt@hou.edu.vn", role="Lecturer", faculty="Khoa Du lịch", bio="Du lịch thông minh (Smart Tourism), Quản trị dịch vụ khách sạn - resort cao cấp, Phát triển du lịch cộng đồng bền vững."),
            User(username="lecturer11", password_hash=generate_password_hash("lecturer123"), full_name="ThS. Đặng Quốc Bảo", email="baodq@hou.edu.vn", role="Lecturer", faculty="Khoa Du lịch", bio="Thiết kế và quản trị tour du lịch trải nghiệm, Ứng dụng công nghệ VR/AR quảng bá di sản văn hóa và điểm đến du lịch."),
            User(username="lecturer12", password_hash=generate_password_hash("lecturer123"), full_name="TS. Hoàng Đình Quang", email="quanghd@hou.edu.vn", role="Lecturer", faculty="Khoa Công nghệ Sinh học", bio="Công nghệ vi sinh vật ứng dụng trong nông nghiệp sạch, Chiết xuất hoạt chất sinh học tự nhiên phục vụ y dược."),
            User(username="lecturer13", password_hash=generate_password_hash("lecturer123"), full_name="KTS. Lê Hoàng Long", email="longlh@hou.edu.vn", role="Lecturer", faculty="Khoa Tạo dáng Công nghiệp", bio="Thiết kế trải nghiệm người dùng (UX/UI Design), Thiết kế kiểu dáng sản phẩm công nghiệp thông minh, Đồ họa truyền thông số."),
            User(username="lecturer14", password_hash=generate_password_hash("lecturer123"), full_name="TS. Ngô Thị Bích Loan", email="loanntb@hou.edu.vn", role="Lecturer", faculty="Khoa Công nghệ Thông tin", bio="Hệ thống thông tin quản lý (MIS), Kho dữ liệu (Data Warehouse) & Business Intelligence (BI), Chuyển đổi số trong giáo dục.")
        ]

        u_sv1   = User(username="student1", password_hash=generate_password_hash("student123"), full_name="Tran Minh Tuan", email="tmt@hou.edu.vn", role="student", student_id="21010001", faculty="Khoa CNTT")
        u_sv2   = User(username="student2", password_hash=generate_password_hash("student123"), full_name="Nguyen Van Hoc", email="nvh@hou.edu.vn", role="student", student_id="21010042", faculty="Khoa CNTT")
        u_sv3   = User(username="student3", password_hash=generate_password_hash("student123"), full_name="Le Thi Lan", email="ltlan@hou.edu.vn", role="student", student_id="21010043", faculty="Khoa CNTT")
        
        db.session.add_all([u_admin, u_faculty] + lecturers + [u_sv1, u_sv2, u_sv3])
        db.session.commit()

if __name__ == "__main__":
    setup_database()
