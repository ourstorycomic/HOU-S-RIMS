# Comprehensive test for buildModernNotificationHtml logic

samples = [
    # 1. Khoa phê duyệt đề cương
    ('<p><strong>🎉 PGS.TS Khoa CNTT đã phê duyệt Đề cương nghiên cứu chi tiết</strong></p>'
     '<p>Đề tài: <strong>Xây dựng hệ thống nghiên cứu khoa học</strong> (v2 - BTL - AN NINH BẢO MẬT DỮ LIỆU (1).docx)</p>'
     '<p>Kết quả cấp Khoa: <span class="badge bg-success">KHOA ĐÃ PHÊ DUYỆT ĐẠT YÊU CẦU</span></p>'
     '<p>Ý kiến chỉ đạo của Khoa: Bài làm đúng nội dung đầy đủ ý, tiến hành các bước tiếp theo.</p>'
     '<a href="/student#s-submit" class="btn btn-outline-primary rounded-pill">Xem Hồ sơ Bài nộp</a>'),
     
    # 2. Khoa yêu cầu sửa báo cáo tiến độ
    ('<p><strong>⚠️ Khoa CNTT yêu cầu chỉnh sửa Báo cáo tiến độ</strong></p>'
     '<p>Đề tài: <strong>Ứng dụng AI trong y tế</strong> (v1 - BC_Tiendo.docx)</p>'
     '<p>Kết quả cấp Khoa: <span class="badge bg-danger">YÊU CẦU CHỈNH SỬA</span></p>'
     '<p>Ý kiến chỉ đạo của Khoa: Cần bổ sung bảng số liệu thực nghiệm tuần 3 và 4.</p>'
     '<a href="/student#s-submit" class="btn btn-outline-primary rounded-pill">Xem Hồ sơ Bài nộp</a>'),

    # 3. Giảng viên đánh giá
    ('<p><strong>🎉 TS. Ngô Thị Bích Loan đã phê duyệt Đề cương nghiên cứu chi tiết</strong></p>'
     '<p>Đề tài: <strong>Xây dựng hệ thống nghiên cứu khoa học</strong> (v2 - docx)</p>'
     '<p>Kết quả: <span class="badge bg-success">ĐÃ DUYỆT (ĐẠT)</span></p>'
     '<p>Ghi chú: Bài làm tốt, chuẩn bị nộp lên Khoa thẩm định.</p>'
     '<a href="/student#s-submit" class="btn btn-outline-primary rounded-pill">Xem Chi tiết</a>'),

    # 4. Giảng viên nhận thông báo bài nộp mới từ sinh viên
    ('<p><strong>Bài nộp mới từ nhóm nghiên cứu</strong></p>'
     '<p>Nhóm đề tài <strong>Xây dựng hệ thống nghiên cứu khoa học</strong> vừa nộp <strong>Đề cương chi tiết (Phiên bản v2)</strong>.</p>'
     '<a href="/lecturer/progress" class="btn btn-primary rounded-pill btn-sm mt-1">Xem & Nhận xét</a>'),

    # 5. Khoa nhận thông báo đề tài mới chờ duyệt
    ('<p><strong>Đề tài mới chờ Khoa phê duyệt</strong></p>'
     '<p>Đề tài <strong>Nghiên cứu thị giác máy tính</strong> do Giảng viên hướng dẫn vừa đồng ý phê duyệt và đang chờ Hội đồng Khoa thẩm định.</p>'
     '<div style="margin-top: 8px;"><strong>Mô tả / Ý tưởng nghiên cứu:</strong><br>Xây dựng mô hình nhận diện hành vi bất thường trong giao thông...</div>'
     '<a href="/faculty/topics" class="btn btn-warning rounded-pill btn-sm mt-2">Xem & Phê duyệt</a>'),

    # 6. Thông báo đợt nckh có file đính kèm
    ('<p><strong>Thông báo Kế hoạch NCKH Sinh viên 2026</strong></p>'
     '<p>Khoa CNTT thông báo phát động phong trào NCKH sinh viên năm học 2025-2026. Sinh viên tải biểu mẫu đính kèm.</p>|||Bieu_mau_NCKH_2026.pdf|||Quy_dinh_NCKH.docx'),

    # 7. Lời mời tham gia nhóm
    ('<p>Bạn nhận được lời mời tham gia nhóm nghiên cứu <strong>Nhóm AI Lab</strong> cho đề tài <strong>Xử lý ngôn ngữ tự nhiên tiếng Việt</strong>.</p>'
     '<a href="/student#s-group" class="btn btn-success rounded-pill">Xem Nhóm</a>')
]

print(f"Total samples to verify: {len(samples)}")

