import re

def test_parse(content):
    parts = content.split('|||')
    mainHtml = parts[0]
    
    # 1. Action button extraction
    actionUrl = ''
    actionText = 'Xem chi tiết'
    actionIcon = 'fa-solid fa-arrow-up-right-from-square'
    
    m_a = re.search(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', mainHtml, re.IGNORECASE)
    if m_a:
        actionUrl = m_a.group(1)
        raw_text = re.sub(r'<[^>]+>', '', m_a.group(2)).strip()
        if raw_text:
            actionText = raw_text
        if 'submit' in actionUrl:
            actionIcon = 'fa-solid fa-file-arrow-up'
            actionText = 'Xem Hồ sơ Bài nộp'
        # remove <a> tag from mainHtml
        mainHtml = mainHtml.replace(m_a.group(0), '')
        
    textContent = re.sub(r'<[^>]+>', ' ', mainHtml)
    
    # Theme
    isFacultyApproval = ('Khoa' in textContent) and ('phê duyệt' in textContent or 'ĐÃ PHÊ DUYỆT' in textContent)
    print("isFacultyApproval:", isFacultyApproval)
    print("actionUrl:", actionUrl)
    print("actionText:", actionText)
    
    # Topic
    topicRegex = r'Đề tài:\s*(?:<strong>)?(.*?)(?:</strong>)?(?:\s*\((.*?)\))?(?:</p>|<br>|[\r\n]|$)'
    tm = re.search(topicRegex, mainHtml, re.IGNORECASE)
    if tm:
        print("Topic Title:", tm.group(1))
        print("Doc Version File:", tm.group(2))
        
    # Badge
    bm = re.search(r'<span class="badge[^"]*">(.*?)</span>', mainHtml, re.IGNORECASE)
    if bm:
        print("Badge:", bm.group(1))
        
    # Feedback
    feedbackRegex = r'(?:Ý kiến chỉ đạo(?: của Khoa| từ Khoa)?:?|Ghi chú(?: từ GV)?:?|Nhận xét(?: của Giảng viên)?:?|Lý do(?: từ chối)?:?)\s*(?:</strong>)?\s*([\s\S]*?)(?:</p>|<a |$)'
    fm = re.search(feedbackRegex, mainHtml, re.IGNORECASE)
    if fm:
        print("Feedback:", fm.group(1))

sample = '<p><strong>🎉 PGS.TS Khoa CNTT đã phê duyệt Đề cương nghiên cứu chi tiết</strong></p><p>Đề tài: <strong>Xây dựng hệ thống nghiên cứu khoa học</strong> (v2 - BTL - AN NINH BẢO MẬT DỮ LIỆU (1).docx)</p><p>Kết quả cấp Khoa: <span class="badge bg-success">KHOA ĐÃ PHÊ DUYỆT ĐẠT YÊU CẦU</span></p><p>Ý kiến chỉ đạo của Khoa: hghggjhj</p><a href="/student#s-submit" class="btn btn-outline-primary rounded-pill">Xem Hồ sơ Bài nộp</a>'
test_parse(sample)

