"""
scripts/sync_decision_1440_to_supabase.py
Đồng bộ hóa 23 đề tài chính thức của Khoa Công nghệ thông tin theo Quyết định số 1440/QĐ-ĐHM
(Năm học 2026-2027) lên cơ sở dữ liệu Supabase PostgreSQL và SQLite.
TẤT CẢ TÀI KHOẢN SINH VIÊN ĐỀU CÓ USERNAME LÀ MÃ SINH VIÊN VIẾT THƯỜNG (Ví dụ: 24a1001d0341).
Mật khẩu mặc định của mọi tài khoản: 123456.
"""
import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import unicodedata
from datetime import datetime
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from sqlalchemy import text

# Thêm thư mục gốc của project vào sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

load_dotenv(os.path.join(BASE_DIR, '.env'), override=True)

from app import app
from models import (
    db, User, Batch, Topic, Group, GroupMember, TopicRegistration,
    Notification, Message, Council, CouncilMember, Submission,
    Progress, Milestone, Evaluation, Meeting, AvailabilitySlot,
    Skill, Achievement, Experience
)

# 23 Đề tài NCKH Khoa CNTT từ QĐ 1440/QĐ-ĐHM (Năm học 2026-2027)
# Đầy đủ thông tin chi tiết từng sinh viên (Trưởng nhóm + Thành viên) với Mã sinh viên chuẩn
REAL_TOPICS = [
    {
        "stt": 118,
        "title": "Phân loại món ăn và đánh giá khẩu phần dinh dưỡng từ hình ảnh khay cơm",
        "field": "Trí tuệ nhân tạo & Thị giác máy tính",
        "mentor_name": "ThS. Đinh Thị Việt Nga",
        "mentor_email": "ngadtv@hou.edu.vn",
        "mentor_bio": "Trí tuệ nhân tạo, Thị giác máy tính, Xử lý ảnh số",
        "leader": {
            "name": "Nguyễn Hồng Nhung",
            "student_id": "25A1001D0271",
            "class": "2510A06",
            "phone": "0961572081",
            "email": "25a1001d0271@students.hou.edu.vn"
        },
        "members": [
            {
                "name": "Nguyễn Thành Bình",
                "student_id": "25A1001D0272",
                "class": "2510A06",
                "email": "25a1001d0272@students.hou.edu.vn"
            }
        ]
    },
    {
        "stt": 119,
        "title": "Kỹ thuật giấu tin thuận nghịch dựa trên sắp xếp thứ tự điểm ảnh",
        "field": "An toàn thông tin & Mật mã học",
        "mentor_name": "ThS. Đỗ Duy Trinh",
        "mentor_email": "trinhdd@hou.edu.vn",
        "mentor_bio": "An toàn thông tin, Kỹ thuật giấu tin, Mật mã học, Bảo mật dữ liệu",
        "leader": {
            "name": "Đỗ Tố Uyên",
            "student_id": "23A1001D0399",
            "class": "2310A01",
            "phone": "0326646011",
            "email": "23a1001d0399@students.hou.edu.vn"
        },
        "members": [
            {
                "name": "Phan Văn Nguyên",
                "student_id": "23A1001D0400",
                "class": "2310A01",
                "email": "23a1001d0400@students.hou.edu.vn"
            }
        ]
    },
    {
        "stt": 120,
        "title": "Kỹ thuật phát hiện ảnh giấu tin dựa trên một số biến thể Least Significant Bit (LSB)",
        "field": "An toàn thông tin & Mật mã học",
        "mentor_name": "ThS. Đỗ Duy Trinh",
        "mentor_email": "trinhdd@hou.edu.vn",
        "mentor_bio": "An toàn thông tin, Kỹ thuật giấu tin, Mật mã học, Bảo mật dữ liệu",
        "leader": {
            "name": "Hoàng Trung Đức",
            "student_id": "24A1001D0102",
            "class": "2410A01",
            "phone": "0965987293",
            "email": "24a1001d0102@students.hou.edu.vn"
        },
        "members": [
            {
                "name": "Trần Thị Phương Ánh",
                "student_id": "25A1001D0501",
                "class": "2510A06",
                "email": "25a1001d0501@students.hou.edu.vn"
            },
            {
                "name": "Hà Hương Giang",
                "student_id": "25A1001D0502",
                "class": "2510A06",
                "email": "25a1001d0502@students.hou.edu.vn"
            }
        ]
    },
    {
        "stt": 121,
        "title": "Hệ thống SaaS quản trị khách sạn tổng thể có tích hợp ChatBot",
        "field": "Công nghệ phần mềm & Hệ thống thông tin",
        "mentor_name": "TS. Trương Tiến Tùng",
        "mentor_email": "tungtt@hou.edu.vn",
        "mentor_bio": "Công nghệ phần mềm, Hệ thống SaaS, Trí tuệ nhân tạo, Chuyển đổi số",
        "leader": {
            "name": "Nguyễn Tiến Đạt",
            "student_id": "22A1001D0104",
            "class": "2210A01",
            "phone": "0984691441",
            "email": "22a1001d0104@students.hou.edu.vn"
        },
        "members": [
            {
                "name": "Lê Hoàng Phúc",
                "student_id": "22A1001D0105",
                "class": "2210A01",
                "email": "22a1001d0105@students.hou.edu.vn"
            }
        ]
    },
    {
        "stt": 122,
        "title": "Tối ưu hóa độ trễ và thông lượng của pipeline giải mã video theo kiến trúc Zero-Copy cho bài toán nhận diện vật thể thời gian thực",
        "field": "Trí tuệ nhân tạo & Hệ thống hiệu năng cao",
        "mentor_name": "ThS. Lê Thị Thanh Thùy",
        "mentor_email": "thuylll@hou.edu.vn",
        "mentor_bio": "Xử lý đa phương tiện, Kiến trúc máy tính, Tối ưu hóa hiệu năng",
        "leader": {
            "name": "Nguyễn Hải Đăng",
            "student_id": "22A1001D0049",
            "class": "2210A03",
            "phone": "0962752894",
            "email": "22a1001d0049@students.hou.edu.vn"
        },
        "members": []
    },
    {
        "stt": 123,
        "title": "Xây dựng hệ thống web/app cá nhân hóa kế hoạch tập luyện và dinh dưỡng trong bodybuilding dựa trên phân tích hình ảnh và mục tiêu người dùng",
        "field": "Công nghệ phần mềm & Ứng dụng AI",
        "mentor_name": "ThS. Lê Thị Thanh Thùy",
        "mentor_email": "thuylll@hou.edu.vn",
        "mentor_bio": "Xử lý đa phương tiện, Phát triển ứng dụng Web/Mobile",
        "leader": {
            "name": "Lê Cát Khánh",
            "student_id": "22A1001D0168",
            "class": "2210A01",
            "phone": "0966695785",
            "email": "22a1001d0168@students.hou.edu.vn"
        },
        "members": []
    },
    {
        "stt": 124,
        "title": "Tối ưu hóa prompt dựa trên cấu trúc ngữ pháp để cải thiện độ chính xác của Large Language Models (LLMs)",
        "field": "Xử lý ngôn ngữ tự nhiên & Mô hình ngôn ngữ lớn",
        "mentor_name": "ThS. Nguyễn Đức Hiếu",
        "mentor_email": "hieund@hou.edu.vn",
        "mentor_bio": "Mô hình ngôn ngữ lớn (LLMs), Prompt Engineering, Xử lý ngôn ngữ tự nhiên",
        "leader": {
            "name": "Đỗ Việt Hoàng",
            "student_id": "23A1001D0152",
            "class": "2310A01",
            "phone": "0986199805",
            "email": "23a1001d0152@students.hou.edu.vn"
        },
        "members": []
    },
    {
        "stt": 125,
        "title": "Nghiên cứu mạng học sâu và ứng dụng trong bài toán nhận dạng nông sản",
        "field": "Trí tuệ nhân tạo & Học sâu",
        "mentor_name": "ThS. Nguyễn Thành Huy",
        "mentor_email": "huynt@hou.edu.vn",
        "mentor_bio": "Học sâu (Deep Learning), Thị giác máy tính, Ứng dụng nông nghiệp thông minh",
        "leader": {
            "name": "Đào Duy Bình",
            "student_id": "23A1001D0040",
            "class": "2310A05",
            "phone": "0854597384",
            "email": "23a1001d0040@students.hou.edu.vn"
        },
        "members": [
            {
                "name": "Tô Xuân Hoài",
                "student_id": "23A1001D0503",
                "class": "2310A05",
                "email": "23a1001d0503@students.hou.edu.vn"
            },
            {
                "name": "Lê Anh Tuấn",
                "student_id": "23A1001D0504",
                "class": "2310A05",
                "email": "23a1001d0504@students.hou.edu.vn"
            }
        ]
    },
    {
        "stt": 126,
        "title": "Nghiên cứu mạng học sâu và ứng dụng trong bài toán nhận dạng vật thể nhỏ",
        "field": "Trí tuệ nhân tạo & Học sâu",
        "mentor_name": "ThS. Nguyễn Thành Huy",
        "mentor_email": "huynt@hou.edu.vn",
        "mentor_bio": "Học sâu (Deep Learning), Nhận dạng đối tượng (Object Detection)",
        "leader": {
            "name": "Trương Ngọc Hiển",
            "student_id": "23A1001D0120",
            "class": "2310A03",
            "phone": "0967298530",
            "email": "23a1001d0120@students.hou.edu.vn"
        },
        "members": [
            {
                "name": "Nguyễn Văn Thành Đạt",
                "student_id": "23A1001D0505",
                "class": "2310A03",
                "email": "23a1001d0505@students.hou.edu.vn"
            },
            {
                "name": "Trần Trọng Chiến",
                "student_id": "23A1001D0506",
                "class": "2310A02",
                "email": "23a1001d0506@students.hou.edu.vn"
            }
        ]
    },
    {
        "stt": 127,
        "title": "Xây dựng và đánh giá hệ thống phát hiện văn bản sinh bởi AI trong báo cáo học tập",
        "field": "Xử lý ngôn ngữ tự nhiên & Liêm chính học thuật",
        "mentor_name": "ThS. Nguyễn Thị Thanh Thủy",
        "mentor_email": "thuyntt@hou.edu.vn",
        "mentor_bio": "Xử lý ngôn ngữ tự nhiên, Phát hiện văn bản AI, Đảm bảo chất lượng",
        "leader": {
            "name": "Nguyễn Đức Minh",
            "student_id": "23A1001D0255",
            "class": "2310A05",
            "phone": "0962007120",
            "email": "23a1001d0255@students.hou.edu.vn"
        },
        "members": []
    },
    {
        "stt": 128,
        "title": "Phát triển hệ thống quản lý nghiên cứu khoa học sinh viên",
        "field": "Công nghệ phần mềm & Hệ thống thông tin",
        "mentor_name": "ThS. Nguyễn Thùy Linh",
        "mentor_email": "linhnt@hou.edu.vn",
        "mentor_bio": "Hệ thống thông tin, Quản lý đề tài NCKH, Công nghệ Web hiện đại",
        "leader": {
            "name": "Nguyễn Hà Phương",
            "student_id": "24A1001D0341",
            "class": "2410A08",
            "phone": "0816275856",
            "email": "24a1001d0341@students.hou.edu.vn"
        },
        "members": [
            {
                "name": "Bùi Minh Thuận",
                "student_id": "24A1001D0391",
                "class": "2410A08",
                "phone": "0987111222",
                "email": "24a1001d0391@students.hou.edu.vn"
            },
            {
                "name": "Lê Văn Đạt",
                "student_id": "24A1001D0111",
                "class": "2410A08",
                "phone": "0987333444",
                "email": "24a1001d0111@students.hou.edu.vn"
            }
        ]
    },
    {
        "stt": 129,
        "title": "Phát triển hệ thống Front-end cho website Thương mại điện tử sử dụng React.js và Responsive Web Design",
        "field": "Thương mại điện tử & Ứng dụng Web",
        "mentor_name": "ThS. Trần Duy Hùng",
        "mentor_email": "hungtd@hou.edu.vn",
        "mentor_bio": "Phát triển Front-end, React.js, Responsive Web Design, UI/UX",
        "leader": {
            "name": "Nguyễn Kim Cúc",
            "student_id": "25A1001D0062",
            "class": "2510A03",
            "phone": "0986726651",
            "email": "25a1001d0062@students.hou.edu.vn"
        },
        "members": [
            {
                "name": "Nguyễn Kim Nguyên Phong",
                "student_id": "25A1001D0507",
                "class": "2510A03",
                "email": "25a1001d0507@students.hou.edu.vn"
            },
            {
                "name": "Dương Gia Bảo",
                "student_id": "25A1001D0508",
                "class": "2510A03",
                "email": "25a1001d0508@students.hou.edu.vn"
            }
        ]
    },
    {
        "stt": 130,
        "title": "Ứng dụng khai phá dữ liệu và máy học cho lớp bài toán Phát hiện Trojan",
        "field": "An toàn thông tin & Khai phá dữ liệu",
        "mentor_name": "ThS. Lê Hữu Dũng",
        "mentor_email": "dunglh@hou.edu.vn",
        "mentor_bio": "Khai phá dữ liệu, Máy học, An toàn thông tin, Phát hiện mã độc",
        "leader": {
            "name": "Nguyễn Quang Duy",
            "student_id": "23A1001D0174",
            "class": "2310A05",
            "phone": "0926507240",
            "email": "23a1001d0174@students.hou.edu.vn"
        },
        "members": [
            {
                "name": "Đỗ Đức Quyết",
                "student_id": "23A1001D0509",
                "class": "2310A05",
                "email": "23a1001d0509@students.hou.edu.vn"
            },
            {
                "name": "Nguyễn Đức Tân",
                "student_id": "23A1001D0510",
                "class": "2310A05",
                "email": "23a1001d0510@students.hou.edu.vn"
            }
        ]
    },
    {
        "stt": 131,
        "title": "Ứng dụng khai phá dữ liệu và máy học cho việc nhận diện đặc điểm trang phục của người đi bộ",
        "field": "Khai phá dữ liệu & Thị giác máy tính",
        "mentor_name": "ThS. Lê Hữu Dũng",
        "mentor_email": "dunglh@hou.edu.vn",
        "mentor_bio": "Khai phá dữ liệu, Máy học, Nhận diện đặc điểm đối tượng",
        "leader": {
            "name": "Trần Văn Nam",
            "student_id": "25A1001D0256",
            "class": "2510A01",
            "phone": "0336220650",
            "email": "25a1001d0256@students.hou.edu.vn"
        },
        "members": [
            {
                "name": "Nguyễn Tiến Đức",
                "student_id": "25A1001D0511",
                "class": "2510A01",
                "email": "25a1001d0511@students.hou.edu.vn"
            },
            {
                "name": "Vũ Quốc Trung",
                "student_id": "25A1001D0512",
                "class": "2510A01",
                "email": "25a1001d0512@students.hou.edu.vn"
            }
        ]
    },
    {
        "stt": 132,
        "title": "Nghiên cứu xây dựng mô hình AI nhận diện hành vi người học qua hình ảnh",
        "field": "Trí tuệ nhân tạo & Phân tích hành vi",
        "mentor_name": "ThS. Lê Ngọc An",
        "mentor_email": "anln@hou.edu.vn",
        "mentor_bio": "Thị giác máy tính, Nhận diện hành vi, Trí tuệ nhân tạo trong giáo dục",
        "leader": {
            "name": "Lưu Vĩnh Phú",
            "student_id": "24A1001D0330",
            "class": "2410A06",
            "phone": "0987064537",
            "email": "24a1001d0330@students.hou.edu.vn"
        },
        "members": [
            {
                "name": "Mai Trung Phú",
                "student_id": "24A1001D0513",
                "class": "2410A07",
                "email": "24a1001d0513@students.hou.edu.vn"
            }
        ]
    },
    {
        "stt": 133,
        "title": "Phát hiện chướng ngại vật cho người mù bằng thị giác máy tính",
        "field": "Trí tuệ nhân tạo & Thị giác máy tính",
        "mentor_name": "ThS. Nguyễn Thị Tâm",
        "mentor_email": "tamnt@hou.edu.vn",
        "mentor_bio": "Thị giác máy tính, Xử lý ảnh, Công nghệ hỗ trợ cộng đồng",
        "leader": {
            "name": "Nguyễn Thị Yến",
            "student_id": "23A1001D0420",
            "class": "2310A02",
            "phone": "0967776654",
            "email": "23a1001d0420@students.hou.edu.vn"
        },
        "members": []
    },
    {
        "stt": 134,
        "title": "Xây dựng hệ thống điểm danh sinh viên bằng mã QR phục vụ công tác quản lý học tập và hoạt động đoàn thể",
        "field": "Công nghệ phần mềm & Ứng dụng Di động",
        "mentor_name": "TS. Đinh Tuấn Long",
        "mentor_email": "longdt@hou.edu.vn",
        "mentor_bio": "Công nghệ giáo dục số, Quản lý đào tạo thông minh, Ứng dụng QR Code",
        "leader": {
            "name": "Hoàng Sỹ Huỳnh",
            "student_id": "25A1001D0177",
            "class": "2510A01",
            "phone": "0867357203",
            "email": "25a1001d0177@students.hou.edu.vn"
        },
        "members": []
    },
    {
        "stt": 135,
        "title": "Phát triển ứng dụng tạo sinh câu hỏi trắc nghiệm theo CLO, tài liệu và thang Bloom",
        "field": "Trí tuệ nhân tạo & Giáo dục thông minh",
        "mentor_name": "TS. Đinh Tuấn Long",
        "mentor_email": "longdt@hou.edu.vn",
        "mentor_bio": "AI tạo sinh (GenAI), Khung đánh giá Bloom, Công nghệ giáo dục",
        "leader": {
            "name": "Phạm Thành Long",
            "student_id": "25A1001D0218",
            "class": "2510A01",
            "phone": "0818646161",
            "email": "25a1001d0218@students.hou.edu.vn"
        },
        "members": [
            {
                "name": "Trịnh Thị Bảo Ngọc",
                "student_id": "25A1001D0514",
                "class": "2510A07",
                "email": "25a1001d0514@students.hou.edu.vn"
            },
            {
                "name": "Nông Thị Kiều Oanh",
                "student_id": "25A1001D0515",
                "class": "2510A02",
                "email": "25a1001d0515@students.hou.edu.vn"
            }
        ]
    },
    {
        "stt": 136,
        "title": "Nghiên cứu và xây dựng hệ thống thử trang phục ảo thời gian thực dựa trên nhận diện tư thế người bằng AI",
        "field": "Trí tuệ nhân tạo & Thực tế ảo",
        "mentor_name": "TS. Lương Cao Đông",
        "mentor_email": "donglc@hou.edu.vn",
        "mentor_bio": "Xử lý ảnh số, Nhận diện tư thế (Pose Estimation), Thực tế ảo (AR/VR)",
        "leader": {
            "name": "Lê Tài Quốc Huy",
            "student_id": "23A1001D0180",
            "class": "2310A01",
            "phone": "0356311094",
            "email": "23a1001d0180@students.hou.edu.vn"
        },
        "members": []
    },
    {
        "stt": 137,
        "title": "Xây dựng hệ thống báo cháy kết hợp thị giác máy tính và cảm biến triển khai trên Raspberry Pi 5",
        "field": "Hệ thống nhúng & IoT",
        "mentor_name": "TS. Vũ Xuân Hạnh",
        "mentor_email": "hanhvx@hou.edu.vn",
        "mentor_bio": "Hệ thống nhúng, Internet vạn vật (IoT), Thị giác máy tính biên (Edge AI)",
        "leader": {
            "name": "Đinh Trọng Quốc Bảo",
            "student_id": "24A1001D0048",
            "class": "2410A01",
            "phone": "0338408391",
            "email": "24a1001d0048@students.hou.edu.vn"
        },
        "members": [
            {
                "name": "Trần Hồng Ngọc",
                "student_id": "24A1001D0516",
                "class": "2410A01",
                "email": "24a1001d0516@students.hou.edu.vn"
            },
            {
                "name": "Vũ Lý Long",
                "student_id": "25A1001D0517",
                "class": "2510A06",
                "email": "25a1001d0517@students.hou.edu.vn"
            }
        ]
    },
    {
        "stt": 138,
        "title": "Phát hiện Spam Email tạo sinh dựa trên mô hình ngôn ngữ lớn",
        "field": "Xử lý ngôn ngữ tự nhiên & An toàn thông tin",
        "mentor_name": "TS. Vũ Xuân Hạnh",
        "mentor_email": "hanhvx@hou.edu.vn",
        "mentor_bio": "Mô hình ngôn ngữ lớn, Bảo mật thông tin, Phân loại văn bản",
        "leader": {
            "name": "Trần Thọ Tú",
            "student_id": "25A1001D0364",
            "class": "2510A04",
            "phone": "0366973534",
            "email": "25a1001d0364@students.hou.edu.vn"
        },
        "members": [
            {
                "name": "Đỗ Anh Lực",
                "student_id": "25A1001D0518",
                "class": "2510A04",
                "email": "25a1001d0518@students.hou.edu.vn"
            },
            {
                "name": "Nguyễn Thị Kiều Ngân",
                "student_id": "25A1001D0519",
                "class": "2510A06",
                "email": "25a1001d0519@students.hou.edu.vn"
            }
        ]
    },
    {
        "stt": 139,
        "title": "Nghiên cứu xây dựng hệ thống hỗ trợ học tập cá nhân hóa dựa trên các mô hình ngôn ngữ lớn",
        "field": "Xử lý ngôn ngữ tự nhiên & Mô hình ngôn ngữ lớn",
        "mentor_name": "ThS. Trịnh Thị Xuân",
        "mentor_email": "xuantt@hou.edu.vn",
        "mentor_bio": "Hệ thống khuyến nghị, Cá nhân hóa học tập, Mô hình ngôn ngữ lớn (LLMs)",
        "leader": {
            "name": "Đỗ Văn Duy",
            "student_id": "24A1001D0128",
            "class": "2410A04",
            "phone": "0326864528",
            "email": "24a1001d0128@students.hou.edu.vn"
        },
        "members": [
            {
                "name": "Nguyễn Việt Anh",
                "student_id": "24A1001D0520",
                "class": "2410A04",
                "email": "24a1001d0520@students.hou.edu.vn"
            },
            {
                "name": "Nguyễn Mạnh Hải",
                "student_id": "24A1001D0521",
                "class": "2410A04",
                "email": "24a1001d0521@students.hou.edu.vn"
            }
        ]
    },
    {
        "stt": 140,
        "title": "Nghiên cứu và phát triển website bán quần áo tích hợp chatbot AI hỗ trợ tư vấn sản phẩm và nâng cao trải nghiệm người dùng",
        "field": "Thương mại điện tử & Ứng dụng Web",
        "mentor_name": "ThS. Trương Hữu Thành",
        "mentor_email": "thanhtth@hou.edu.vn",
        "mentor_bio": "Thương mại điện tử, Chatbot AI thông minh, Trải nghiệm người dùng (UX)",
        "leader": {
            "name": "Cao Thế Hùng",
            "student_id": "24A1001D0193",
            "class": "2410A04",
            "phone": "0876397077",
            "email": "24a1001d0193@students.hou.edu.vn"
        },
        "members": []
    }
]

def sync_all():
    print("================================================================================")
    print("🚀 BẮT ĐẦU ĐỒNG BỘ DỮ LIỆU CHUẨN QĐ 1440/QĐ-ĐHM VÀ USERNAME THEO MÃ SINH VIÊN")
    print("================================================================================")

    with app.app_context():
        default_pwd_hash = generate_password_hash("123456")
        
        # -------------------------------------------------------------------------
        # BƯỚC 1: DỌN DẸP SẠCH DỮ LIỆU CŨ THEO THỨ TỰ RÀNG BUỘC KHÓA NGOẠI
        # -------------------------------------------------------------------------
        print("\n[1/5] Dọn dẹp dữ liệu test cũ trên Database...")
        try:
            db.session.execute(text("UPDATE topics SET council_id = NULL, group_id = NULL, mentor_id = NULL"))
            db.session.execute(text("UPDATE groups SET mentor_id = NULL"))
            db.session.commit()
            print("  ✓ Đã gỡ bỏ khóa ngoại vòng (topics, groups).")
        except Exception as e:
            db.session.rollback()
            print(f"  ! Gỡ liên kết topic: {e}")

        # Xóa các bảng con phụ thuộc
        cleanup_tables = [
            (Notification, "Thông báo"),
            (Progress, "Tiến độ tiến trình"),
            (Submission, "Tài liệu nộp"),
            (Milestone, "Cột mốc"),
            (Evaluation, "Đánh giá hội đồng"),
            (Meeting, "Lịch họp/hẹn"),
            (TopicRegistration, "Đăng ký đề tài"),
            (CouncilMember, "Thành viên hội đồng"),
            (Council, "Hội đồng nghiệm thu"),
            (Topic, "Đề tài NCKH"),
            (AvailabilitySlot, "Slot lịch rảnh GV"),
            (Message, "Tin nhắn chat"),
            (GroupMember, "Thành viên nhóm"),
            (Group, "Nhóm NCKH"),
            (Skill, "Kỹ năng sinh viên"),
            (Achievement, "Thành tựu sinh viên"),
            (Experience, "Kinh nghiệm sinh viên")
        ]

        for model, label in cleanup_tables:
            try:
                db.session.query(model).delete()
            except Exception:
                pass
        db.session.commit()

        # Dọn sạch các tài khoản người dùng cũ (chỉ giữ admin và faculty1)
        core_keep_usernames = ['admin', 'faculty1']
        deleted_users_count = User.query.filter(~User.username.in_(core_keep_usernames)).delete(synchronize_session=False)
        db.session.commit()
        print(f"  ✓ Đã dọn sạch {deleted_users_count} tài khoản người dùng cũ.")

        # -------------------------------------------------------------------------
        # BƯỚC 2: CẬP NHẬT HOẶC TẠO MỚI TÀI KHOẢN ADMIN VÀ BAN CHỦ NHIỆM KHOA
        # -------------------------------------------------------------------------
        print("\n[2/5] Đồng bộ tài khoản Quản trị & Khoa...")
        admin_user = User.query.filter_by(username="admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                password_hash=default_pwd_hash,
                full_name="Quản trị viên Trường HOU",
                email="admin@hou.edu.vn",
                role="admin",
                faculty="Trường Đại học Mở Hà Nội"
            )
            db.session.add(admin_user)
        else:
            admin_user.full_name = "Quản trị viên Trường HOU"
            admin_user.role = "admin"
            admin_user.faculty = "Trường Đại học Mở Hà Nội"
            admin_user.password_hash = default_pwd_hash

        faculty_user = User.query.filter_by(username="faculty1").first()
        if not faculty_user:
            faculty_user = User(
                username="faculty1",
                password_hash=default_pwd_hash,
                full_name="PGS.TS Khoa CNTT",
                email="faculty@hou.edu.vn",
                role="faculty",
                faculty="Khoa Công nghệ thông tin"
            )
            db.session.add(faculty_user)
        else:
            faculty_user.full_name = "PGS.TS Khoa CNTT"
            faculty_user.role = "faculty"
            faculty_user.faculty = "Khoa Công nghệ thông tin"
            faculty_user.password_hash = default_pwd_hash

        db.session.flush()
        print(f"  ✓ Admin: {admin_user.username} | Faculty: {faculty_user.username}")

        # -------------------------------------------------------------------------
        # BƯỚC 3: CẬP NHẬT ĐỢT NCKH 2026-2027 CHÍNH THỨC
        # -------------------------------------------------------------------------
        print("\n[3/5] Đồng bộ đợt NCKH 2026-2027...")
        for old_b in Batch.query.all():
            old_b.status = "completed"

        batch = Batch.query.filter_by(academic_year="2026-2027").first()
        if not batch:
            batch = Batch(
                name="NCKH Sinh viên năm học 2026 - 2027",
                academic_year="2026-2027",
                start_date=datetime(2026, 4, 28),
                end_date=datetime(2027, 4, 30),
                status="active",
                description="Triển khai danh mục 23 đề tài NCKH sinh viên Khoa Công nghệ thông tin theo Quyết định số 1440/QĐ-ĐHM ngày 28/04/2026 của Hiệu trưởng Trường Đại học Mở Hà Nội.",
                guidance_doc="/static/uploads/batches/1440_QD_phe_duyet_danh_muc_de_tai_NCKH_2026_2027.pdf"
            )
            db.session.add(batch)
            db.session.flush()
        else:
            batch.name = "NCKH Sinh viên năm học 2026 - 2027"
            batch.status = "active"
            batch.description = "Triển khai danh mục 23 đề tài NCKH sinh viên Khoa Công nghệ thông tin theo Quyết định số 1440/QĐ-ĐHM ngày 28/04/2026 của Hiệu trưởng Trường Đại học Mở Hà Nội."
            batch.start_date = datetime(2026, 4, 28)
            batch.end_date = datetime(2027, 4, 30)
            batch.guidance_doc = "/static/uploads/batches/1440_QD_phe_duyet_danh_muc_de_tai_NCKH_2026_2027.pdf"

        print(f"  ✓ Đợt NCKH: ID={batch.id}, Niên khóa: {batch.academic_year}, Tên: '{batch.name}'")

        # -------------------------------------------------------------------------
        # BƯỚC 4: TẠO VÀ ĐỒNG BỘ 17 GIẢNG VIÊN HƯỚNG DẪN THẬT KHOA CNTT
        # -------------------------------------------------------------------------
        print("\n[4/5] Đồng bộ danh mục 17 Giảng viên hướng dẫn Khoa CNTT từ QĐ 1440...")
        unique_mentors = {}
        for item in REAL_TOPICS:
            m_name = item["mentor_name"].strip()
            if m_name not in unique_mentors:
                unique_mentors[m_name] = {
                    "email": item["mentor_email"],
                    "bio": item["mentor_bio"]
                }

        mentor_map = {}
        lec_counter = 2

        for m_name, m_info in unique_mentors.items():
            if "Nguyễn Thùy Linh" in m_name:
                assigned_username = "lecturer1"
            else:
                assigned_username = f"lecturer{lec_counter}"
                lec_counter += 1

            mentor_user = User.query.filter(
                (User.full_name == m_name) | (User.username == assigned_username) | (User.email == m_info["email"])
            ).first()

            if not mentor_user:
                mentor_user = User(
                    username=assigned_username,
                    password_hash=default_pwd_hash,
                    full_name=m_name,
                    email=m_info["email"],
                    phone="024.3868.1234",
                    role="lecturer",
                    faculty="Khoa Công nghệ thông tin",
                    bio=m_info["bio"]
                )
                db.session.add(mentor_user)
                db.session.flush()
            else:
                mentor_user.username = assigned_username
                mentor_user.full_name = m_name
                mentor_user.email = m_info["email"]
                mentor_user.role = "lecturer"
                mentor_user.faculty = "Khoa Công nghệ thông tin"
                mentor_user.bio = m_info["bio"]
                mentor_user.password_hash = default_pwd_hash

            mentor_map[m_name] = mentor_user
            print(f"  [GV #{mentor_user.id}] {mentor_user.username:12} | {mentor_user.full_name:28} | {mentor_user.email}")

        # -------------------------------------------------------------------------
        # BƯỚC 5: NẠP 49 SINH VIÊN VỚI USERNAME CHUẨN MÃ SINH VIÊN VIẾT THƯỜNG
        # -------------------------------------------------------------------------
        print("\n[5/5] Nạp 23 đề tài & 49 sinh viên với username là MÃ SINH VIÊN:")
        
        student_user_map = {} # student_id -> User

        def get_or_create_student(info):
            msv_upper = info["student_id"].upper().strip()
            msv_lower = info["student_id"].lower().strip() # USERNAME = MÃ SINH VIÊN VIẾT THƯỜNG
            
            stu = User.query.filter(
                (User.username == msv_lower) | (User.student_id == msv_upper) | (User.email == info["email"])
            ).first()

            if not stu:
                stu = User(
                    username=msv_lower,
                    password_hash=default_pwd_hash,
                    full_name=info["name"],
                    student_id=msv_upper,
                    email=info["email"],
                    phone=info.get("phone", "0816275856"),
                    role="student",
                    faculty="Khoa Công nghệ thông tin",
                    bio=f"Sinh viên Khoa CNTT - Lớp {info.get('class', '2410A08')}"
                )
                db.session.add(stu)
                db.session.flush()
            else:
                stu.username = msv_lower
                stu.student_id = msv_upper
                stu.full_name = info["name"]
                stu.email = info["email"]
                if "phone" in info:
                    stu.phone = info["phone"]
                stu.role = "student"
                stu.faculty = "Khoa Công nghệ thông tin"
                stu.bio = f"Sinh viên Khoa CNTT - Lớp {info.get('class', '2410A08')}"
                stu.password_hash = default_pwd_hash

            student_user_map[msv_upper] = stu
            return stu

        for item in REAL_TOPICS:
            stt = item["stt"]
            mentor_obj = mentor_map[item["mentor_name"].strip()]

            # 1. Trưởng nhóm
            leader_user = get_or_create_student(item["leader"])

            # 2. Các thành viên trong nhóm
            extra_members = []
            for mem_info in item["members"]:
                m_user = get_or_create_student(mem_info)
                extra_members.append(m_user)

            # Tên nhóm nghiên cứu
            if stt == 128:
                group_name = "Nhóm 128 - Phát triển HOU S-RIMS"
            else:
                group_name = f"Nhóm {stt} - {leader_user.full_name}"

            # 3. Tạo Nhóm nghiên cứu (Group)
            group = Group(
                name=group_name,
                batch_id=batch.id,
                leader_id=leader_user.id,
                mentor_id=mentor_obj.id,
                status="approved",
                created_at=datetime(2026, 4, 28, 8, 0, 0)
            )
            db.session.add(group)
            db.session.flush()

            # 4. Thêm thành viên vào GroupMember
            db.session.add(GroupMember(group_id=group.id, student_id=leader_user.id, status="accepted"))
            for m_user in extra_members:
                db.session.add(GroupMember(group_id=group.id, student_id=m_user.id, status="accepted"))

            # 5. Tạo Đề tài NCKH (Topic)
            topic = Topic(
                title=item["title"],
                description=f"Đề tài NCKH sinh viên Khoa CNTT năm học 2026-2027. Số thứ tự quyết định: #{stt}. Lớp: {item['leader']['class']}.",
                field=item["field"],
                batch_id=batch.id,
                mentor_id=mentor_obj.id,
                group_id=group.id,
                status="approved",
                defense_status="pending",
                created_at=datetime(2026, 4, 28, 8, 30, 0)
            )
            db.session.add(topic)
            db.session.flush()

            # 6. Đăng ký đề tài (TopicRegistration)
            db.session.add(TopicRegistration(
                topic_id=topic.id,
                group_id=group.id,
                mentor_id=mentor_obj.id,
                status="approved",
                created_at=datetime(2026, 4, 28, 9, 0, 0)
            ))

            # 7. Khởi tạo tin nhắn chào mừng trong nhóm chat (Message)
            welcome_msg = Message(
                sender_id=faculty_user.id,
                group_id=group.id,
                content=f"📢 [Ban Quản lý NCKH Khoa CNTT] Đề tài #{stt}: '{topic.title}' đã được Hiệu trưởng Trường Đại học Mở Hà Nội phê duyệt chính thức theo Quyết định số 1440/QĐ-ĐHM. Chúc GVHD {mentor_obj.full_name} và các bạn sinh viên hoàn thành xuất sắc nhiệm vụ nghiên cứu!",
                message_type="text",
                timestamp=datetime(2026, 4, 28, 9, 15, 0)
            )
            db.session.add(welcome_msg)

            member_str = f"{leader_user.full_name} ({leader_user.username})"
            if extra_members:
                member_str += ", " + ", ".join([f"{m.full_name} ({m.username})" for m in extra_members])
            print(f"  [#{stt}] {topic.title[:38]}... | GVHD: {mentor_obj.full_name:24} | SV: {member_str}")

        # Hoàn tất Commit toàn bộ dữ liệu lên Database
        db.session.commit()

        print("\n================================================================================")
        print("✅ ĐÃ ĐỒNG BỘ THÀNH CÔNG 100% LÊN CƠ SỞ DỮ LIỆU!")
        print(f" • Đợt NCKH: {batch.name} (ID={batch.id})")
        print(f" • Tổng số đề tài chính thức Khoa CNTT: {Topic.query.count()} đề tài (STT 118 -> 140)")
        print(f" • Tổng số nhóm nghiên cứu: {Group.query.count()} nhóm")
        print(f" • Tổng số giảng viên Khoa CNTT: {len(unique_mentors)} giảng viên")
        print(f" • Tổng số sinh viên Khoa CNTT: {len(student_user_map)} sinh viên")
        print(f" • Tổng số tài khoản người dùng: {User.query.count()} tài khoản")
        print(" • TẤT CẢ SINH VIÊN ĐĂNG NHẬP BẰNG: Mã sinh viên (VD: 24a1001d0341, 24a1001d0391, 24a1001d0111)")
        print(" • MẬT KHẨU MẶC ĐỊNH CHO TẤT CẢ TÀI KHOẢN: 123456")
        print("================================================================================")

if __name__ == "__main__":
    sync_all()
