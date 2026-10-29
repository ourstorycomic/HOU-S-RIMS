with open('static/assets/js/app.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Marker 1: readNotification start
start_str = "async function readNotification(id, content, fromAll = false) {"
# Marker 2: syncNotificationsLive start
end_str = "// Real-time Live Synchronization for Notifications & Invitee Actions\nasync function syncNotificationsLive(immediate = false) {"

p1 = text.find(start_str)
p2 = text.find(end_str)

print("p1:", p1, "p2:", p2)
if p1 == -1 or p2 == -1:
    print("Failed to find boundaries!")
    exit(1)

new_notif_system = '''// ====================================================================
// HỆ THỐNG MODAL CHI TIẾT THÔNG BÁO HIỆN ĐẠI (CHUNG CHO SINH VIÊN, GIẢNG VIÊN & KHOA)
// ====================================================================
window.handleNotifActionClick = function(href) {
    if (typeof Swal !== 'undefined') Swal.close();
    if (!href) return;

    // Xử lý chuyển tab trực tiếp nếu đang ở trang Sinh viên
    if (href.includes('#s-') || href.startsWith('/student#s-')) {
        const parts = href.split('#');
        const tabId = parts[1];
        if (typeof switchTab === 'function') {
            const navLink = document.querySelector(`a[href*="${tabId}"]`);
            if (navLink) {
                switchTab(tabId, navLink);
            } else {
                window.location.hash = '#' + tabId;
            }
            return;
        }
    }

    if (href.startsWith('/lecturer') && window.location.pathname.startsWith('/lecturer')) {
        window.location.href = href;
        return;
    }

    window.location.href = href;
};

window.goBackToAllNotifications = function() {
    if (typeof Swal !== 'undefined') Swal.close();
    setTimeout(() => {
        if (typeof showAllNotifications === 'function') {
            showAllNotifications();
        }
    }, 200);
};

function buildModernNotificationHtml(id, content, fromAll) {
    const parts = (content || '').split('|||');
    const mainHtml = parts[0] || '';
    const attachments = parts.slice(1).map(s => s.trim()).filter(Boolean);

    // 1. Phân tích Link hành động (Button hành động chính ở footer)
    let actionUrl = '';
    let actionText = '';
    let actionIcon = 'fa-solid fa-arrow-up-right-from-square';

    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = mainHtml;

    const linkEl = tempDiv.querySelector('a[href]');
    if (linkEl) {
        actionUrl = linkEl.getAttribute('href') || '';
        actionText = linkEl.textContent.trim() || 'Xem chi tiết';
        linkEl.remove();
    }

    const cleanHtml = tempDiv.innerHTML.trim();
    const textContent = tempDiv.textContent || tempDiv.innerText || '';

    // 2. Xác định Loại thông báo & Theme màu sắc
    let theme = {
        gradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        categoryTag: 'THÔNG BÁO HỆ THỐNG',
        icon: 'fa-solid fa-bell',
        headline: 'Thông báo từ Hệ thống NCKH',
        isApproval: false,
        isRevision: false
    };

    const isFacultyApproval = textContent.includes('Khoa') && (textContent.includes('phê duyệt') || textContent.includes('ĐÃ PHÊ DUYỆT'));
    const isFacultyRevision = textContent.includes('Khoa') && (textContent.includes('chỉnh sửa') || textContent.includes('YÊU CẦU CHỈNH SỬA') || textContent.includes('YÊU CẦU'));
    const isLecturerApproved = (textContent.includes('Giảng viên') || textContent.includes('GVHD') || textContent.includes('TS.')) && (textContent.includes('phê duyệt') || textContent.includes('ĐÃ DUYỆT'));
    const isLecturerRevision = (textContent.includes('Giảng viên') || textContent.includes('GVHD') || textContent.includes('TS.')) && (textContent.includes('yêu cầu') || textContent.includes('chỉnh sửa'));
    const isLecturerReview = (textContent.includes('Giảng viên') || textContent.includes('GVHD') || textContent.includes('TS.')) && (textContent.includes('đánh giá') || textContent.includes('ghi chú') || textContent.includes('nhận xét'));
    const isStudentSubmission = textContent.includes('Bài nộp mới từ nhóm') || textContent.includes('vừa nộp');
    const isTopicWaitingFaculty = textContent.includes('Đề tài mới chờ Khoa phê duyệt') || (textContent.includes('chờ Hội đồng Khoa') && textContent.includes('thẩm định'));
    const isGroupInvitation = textContent.includes('Lời mời tham gia') || textContent.includes('mời vào nhóm') || textContent.includes('mời tham gia nhóm');
    const isTopicApproval = textContent.includes('phê duyệt đề tài') || (textContent.includes('Đề tài NCKH') && textContent.includes('chính thức phê duyệt'));
    const isBatchAnnouncement = textContent.includes('Đợt NCKH:') || textContent.includes('NCKH 20') || textContent.includes('Kế hoạch NCKH');
    const isCalendarMeeting = textContent.includes('Lịch hẹn') || textContent.includes('lịch hẹn');
    const isCouncil = textContent.includes('Hội đồng') || textContent.includes('hội đồng');

    if (isFacultyApproval) {
        theme.gradient = 'linear-gradient(135deg, #065f46 0%, #059669 100%)';
        theme.categoryTag = 'KHOA CÔNG NGHỆ THÔNG TIN • ĐÃ PHÊ DUYỆT';
        theme.icon = 'fa-solid fa-stamp';
        theme.headline = 'Khoa CNTT đã phê duyệt Đạt yêu cầu';
        theme.isApproval = true;
    } else if (isFacultyRevision) {
        theme.gradient = 'linear-gradient(135deg, #991b1b 0%, #dc2626 100%)';
        theme.categoryTag = 'KHOA CÔNG NGHỆ THÔNG TIN • YÊU CẦU CHỈNH SỬA';
        theme.icon = 'fa-solid fa-triangle-exclamation';
        theme.headline = 'Khoa CNTT yêu cầu chỉnh sửa bài nộp';
        theme.isRevision = true;
    } else if (isLecturerApproved) {
        theme.gradient = 'linear-gradient(135deg, #1e40af 0%, #2563eb 100%)';
        theme.categoryTag = 'GIẢNG VIÊN HƯỚNG DẪN • ĐÃ DUYỆT';
        theme.icon = 'fa-solid fa-circle-check';
        theme.headline = 'Giảng viên hướng dẫn đã duyệt Đạt';
        theme.isApproval = true;
    } else if (isLecturerRevision) {
        theme.gradient = 'linear-gradient(135deg, #b45309 0%, #d97706 100%)';
        theme.categoryTag = 'GIẢNG VIÊN HƯỚNG DẪN • YÊU CẦU SỬA';
        theme.icon = 'fa-solid fa-triangle-exclamation';
        theme.headline = 'Giảng viên yêu cầu chỉnh sửa bài nộp';
        theme.isRevision = true;
    } else if (isLecturerReview) {
        theme.gradient = 'linear-gradient(135deg, #0369a1 0%, #0284c7 100%)';
        theme.categoryTag = 'GIẢNG VIÊN HƯỚNG DẪN • ĐÁNH GIÁ';
        theme.icon = 'fa-solid fa-chalkboard-user';
        theme.headline = 'Giảng viên đã nhận xét & đánh giá bài nộp';
    } else if (isTopicWaitingFaculty) {
        theme.gradient = 'linear-gradient(135deg, #854d0e 0%, #d97706 100%)';
        theme.categoryTag = 'HỘI ĐỒNG KHOA • THẨM ĐỊNH ĐỀ TÀI';
        theme.icon = 'fa-solid fa-building-columns';
        theme.headline = 'Đề tài NCKH mới chờ Khoa thẩm định';
        if (!actionUrl) actionUrl = '/faculty/topics';
    } else if (isStudentSubmission) {
        theme.gradient = 'linear-gradient(135deg, #312e81 0%, #4f46e5 100%)';
        theme.categoryTag = 'BÀI NỘP MỚI TỪ SINH VIÊN';
        theme.icon = 'fa-solid fa-file-arrow-up';
        theme.headline = 'Sinh viên nộp hồ sơ / bài báo cáo mới';
        if (!actionUrl) actionUrl = '/lecturer/progress';
    } else if (isGroupInvitation) {
        theme.gradient = 'linear-gradient(135deg, #0f766e 0%, #0d9488 100%)';
        theme.categoryTag = 'LỜI MỜI THAM GIA NHÓM NCKH';
        theme.icon = 'fa-solid fa-user-plus';
        theme.headline = 'Lời mời tham gia nhóm Nghiên cứu khoa học';
        if (!actionUrl) actionUrl = '/student#s-group';
    } else if (isTopicApproval) {
        theme.gradient = 'linear-gradient(135deg, #3730a3 0%, #6366f1 100%)';
        theme.categoryTag = 'PHÊ DUYỆT ĐỀ TÀI NCKH CHÍNH THỨC';
        theme.icon = 'fa-solid fa-award';
        theme.headline = '🎉 Đề tài NCKH đã được phê duyệt chính thức';
        theme.isApproval = true;
    } else if (isBatchAnnouncement) {
        theme.gradient = 'linear-gradient(135deg, #312e81 0%, #4338ca 100%)';
        theme.categoryTag = 'KẾ HOẠCH & HƯỚNG DẪN ĐỢT NCKH';
        theme.icon = 'fa-solid fa-bullhorn';
        theme.headline = 'Thông báo Đợt Nghiên cứu khoa học';
    } else if (isCalendarMeeting) {
        theme.gradient = 'linear-gradient(135deg, #0e7490 0%, #0891b2 100%)';
        theme.categoryTag = 'LỊCH HẸN & TRAO ĐỔI NCKH';
        theme.icon = 'fa-solid fa-calendar-check';
        theme.headline = 'Cập nhật trạng thái lịch hẹn';
    } else if (isCouncil) {
        theme.gradient = 'linear-gradient(135deg, #701a75 0%, #a21caf 100%)';
        theme.categoryTag = 'HỘI ĐỒNG ĐÁNH GIÁ NGHIỆM THU';
        theme.icon = 'fa-solid fa-users-rectangle';
        theme.headline = 'Phân công Hội đồng đánh giá NCKH';
    }

    // 3. Phân tách các trường dữ liệu chi tiết
    let topicTitle = '';
    let docVersionFile = '';
    let statusLabel = '';
    let feedbackText = '';

    // Tìm tên Đề tài & Tệp
    const topicRegex = /Đề tài:\\s*(?:<strong>)?(.*?)(?:<\\/strong>)?(?:\\s*\\((.*?)\\))?(?:<\\/p>|<br>|[\\r\\n]|$)/i;
    const topicMatch = mainHtml.match(topicRegex) 
                    || mainHtml.match(/đề tài\\s*(?:NCKH)?(?:\\s*<strong>)?:\\s*(.*?)(?:<\\/strong>)?(?:<\\/p>|<br>|[\\r\\n]|$)/i)
                    || mainHtml.match(/đề tài\\s*(?:<strong>)?["'“]?([^"'”<]+)["'”]?/i);
    if (topicMatch) {
        topicTitle = topicMatch[1] ? topicMatch[1].replace(/<\\/?[^>]+(>|$)/g, "").trim() : '';
        if (topicMatch[2]) {
            docVersionFile = topicMatch[2].replace(/<\\/?[^>]+(>|$)/g, "").trim();
        }
    }

    // Tìm kết quả thẩm định
    const badgeMatch = mainHtml.match(/<span class="badge[^"]*">(.*?)<\\/span>/i);
    if (badgeMatch) {
        statusLabel = badgeMatch[1].replace(/<\\/?[^>]+(>|$)/g, "").trim();
    }

    // Tìm ý kiến chỉ đạo / ghi chú / mô tả
    const feedbackRegex = /(?:Ý kiến chỉ đạo(?: của Khoa| từ Khoa)?:?|Ghi chú(?: từ GV)?:?|Nhận xét(?: của Giảng viên)?:?|Lý do(?: từ chối)?:?|Mô tả(?:\\s*\\/\\s*Ý tưởng nghiên cứu)?:?)\\s*(?:<\\/strong>)?\\s*([\\s\\S]*?)(?:<\\/p>|<a |$)/i;
    const feedbackMatch = mainHtml.match(feedbackRegex);
    if (feedbackMatch) {
        feedbackText = feedbackMatch[1].replace(/<\\/?[^>]+(>|$)/g, "").trim();
    }

    // Tìm dòng tiêu đề đầu tiên nếu có
    const strongHeaderMatch = mainHtml.match(/<p>\\s*<strong>(.*?)<\\/strong>\\s*<\\/p>/i) || mainHtml.match(/<strong>(.*?)<\\/strong>/i);
    if (strongHeaderMatch) {
        const hText = strongHeaderMatch[1].replace(/<\\/?[^>]+(>|$)/g, "").trim();
        if (hText.length > 5 && !hText.includes('Đề tài:') && !hText.includes('Kết quả') && !hText.includes('Ý kiến') && !hText.includes('Mô tả')) {
            theme.headline = hText;
        }
    }

    // Tinh chỉnh nút hành động và icon
    if (actionUrl) {
        if (actionUrl.includes('submit')) {
            actionIcon = 'fa-solid fa-file-arrow-up';
            actionText = 'Xem Hồ sơ Bài nộp';
        } else if (actionUrl.includes('faculty/topics')) {
            actionIcon = 'fa-solid fa-check-double';
            actionText = 'Xem & Phê duyệt Đề tài';
        } else if (actionUrl.includes('lecturer/progress') || actionUrl.includes('progress')) {
            actionIcon = 'fa-solid fa-clipboard-check';
            actionText = actionText && actionText !== 'Xem chi tiết' ? actionText : 'Xem Tiến độ Đề tài';
        } else if (actionUrl.includes('group')) {
            actionIcon = 'fa-solid fa-users';
            actionText = 'Quản lý Nhóm NCKH';
        } else if (actionUrl.includes('calendar')) {
            actionIcon = 'fa-solid fa-calendar-check';
            actionText = 'Xem Lịch làm việc';
        } else if (actionUrl.includes('chat')) {
            actionIcon = 'fa-solid fa-comments';
            actionText = 'Vào phòng Chat Nhóm';
        }
    }

    // 4. Xây dựng khối HTML giao diện hiện đại
    let bodyCardsHtml = '';

    if (topicTitle || statusLabel || feedbackText) {
        // Cấu trúc dạng thẻ bài nộp / đề tài
        if (topicTitle) {
            bodyCardsHtml += `
                <!-- Khối thông tin Đề tài & Bài nộp -->
                <div class="p-3.5 rounded-4 bg-white border border-slate-200 shadow-xs mb-3">
                    <div class="d-flex align-items-center justify-content-between mb-2 flex-wrap gap-1">
                        <span class="badge bg-primary-subtle text-primary border border-primary-subtle rounded-pill px-2.5 py-1 fw-bold" style="font-size: 11px;">
                            <i class="fa-solid fa-book-bookmark me-1"></i> Đề tài NCKH
                        </span>
                        ${docVersionFile ? `<span class="badge bg-secondary-subtle text-secondary rounded-pill px-2.5 py-1 fw-semibold" style="font-size: 11px;"><i class="fa-solid fa-file-lines me-1"></i> ${docVersionFile}</span>` : ''}
                    </div>
                    <div class="fw-bold text-dark fs-6" style="line-height: 1.45;">
                        ${topicTitle}
                    </div>
                </div>
            `;
        }

        if (statusLabel) {
            let sBg = '#ecfdf5', sBorder = '#a7f3d0', sText = '#065f46', sIcon = 'fa-solid fa-circle-check', sIconBg = '#d1fae5';
            if (theme.isRevision || statusLabel.includes('YÊU CẦU') || statusLabel.includes('TỪ CHỐI')) {
                sBg = '#fef2f2'; sBorder = '#fecaca'; sText = '#991b1b'; sIcon = 'fa-solid fa-triangle-exclamation'; sIconBg = '#fee2e2';
            } else if (statusLabel.includes('CHỜ') || statusLabel.includes('ĐANG')) {
                sBg = '#fffbeb'; sBorder = '#fde68a'; sText = '#b45309'; sIcon = 'fa-solid fa-clock'; sIconBg = '#fef3c7';
            }

            bodyCardsHtml += `
                <!-- Khối Quyết định thẩm định -->
                <div class="p-3.5 rounded-4 mb-3 d-flex align-items-center gap-3 shadow-xs" style="background: ${sBg}; border: 1.5px solid ${sBorder};">
                    <div class="rounded-circle d-flex align-items-center justify-content-center flex-shrink-0" style="width: 44px; height: 44px; background: ${sIconBg}; color: ${sText}; font-size: 20px;">
                        <i class="${sIcon}"></i>
                    </div>
                    <div>
                        <div class="text-uppercase fw-bold" style="font-size: 10.5px; letter-spacing: 0.5px; color: ${sText}; opacity: 0.85;">Quyết định & Kết quả thẩm định:</div>
                        <div class="fw-bold" style="font-size: 15px; color: ${sText};">
                            ${statusLabel}
                        </div>
                    </div>
                </div>
            `;
        }

        if (feedbackText) {
            bodyCardsHtml += `
                <!-- Khối Ý kiến chỉ đạo / Nhận xét -->
                <div class="p-3.5 rounded-4 mb-3" style="background: #fffbeb; border: 1px solid #fde68a; border-left: 5px solid #f59e0b;">
                    <div class="fw-bold mb-1.5 d-flex align-items-center gap-1.5" style="color: #b45309; font-size: 13px;">
                        <i class="fa-solid fa-comment-dots fs-6"></i> Ý kiến chỉ đạo / Ghi chú phản hồi:
                    </div>
                    <div style="font-size: 13.5px; color: #334155; line-height: 1.55; white-space: pre-wrap;">
                        ${feedbackText}
                    </div>
                </div>
            `;
        }
    } else {
        // Thông báo văn bản tự do / đợt nckh / lịch hẹn
        bodyCardsHtml += `
            <div class="p-3.5 rounded-4 bg-white border border-slate-200 shadow-xs mb-3">
                <div class="ql-editor rich-content-display p-0" style="font-size: 13.5px; line-height: 1.6; color: #1e293b;">
                    ${cleanHtml}
                </div>
            </div>
        `;
    }

    // Khối tệp đính kèm (nếu có)
    let attachmentsHtml = '';
    if (attachments.length > 0) {
        attachmentsHtml = `
            <div class="p-3.5 rounded-4 bg-white border border-slate-200 shadow-xs mb-3">
                <div class="small fw-bold text-dark mb-2.5 d-flex align-items-center gap-1.5">
                    <i class="fa-solid fa-paperclip text-primary"></i> Tài liệu đính kèm (${attachments.length}):
                </div>
                <div class="d-flex flex-column gap-2">
                    ${attachments.map(f => `
                        <a href="/static/uploads/batches/${encodeURIComponent(f)}" target="_blank" class="btn btn-outline-primary rounded-pill d-flex align-items-center justify-content-between p-2.5 px-3.5 text-decoration-none fw-bold small text-start">
                            <span class="text-truncate me-2"><i class="fa-solid fa-file-pdf me-2 text-danger"></i>${f}</span>
                            <span class="badge bg-primary text-white rounded-pill px-2.5 py-1"><i class="fa-solid fa-download me-1"></i> Tải về</span>
                        </a>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // Khối nút hành động đáy (Footer Action Bar)
    const backBtn = fromAll ? `
        <button type="button" class="btn btn-outline-secondary rounded-pill px-3.5 py-2 fw-bold small d-inline-flex align-items-center gap-1.5" onclick="window.goBackToAllNotifications()">
            <i class="fa-solid fa-arrow-left"></i> Quay lại danh sách
        </button>
    ` : `
        <span class="badge bg-light text-secondary border rounded-pill px-3 py-1.5 small fw-semibold" style="font-size: 11px;">
            <i class="fa-solid fa-shield-halved text-primary me-1"></i> HOU S-RIMS
        </span>
    `;

    const actionBtn = actionUrl ? `
        <button type="button" class="btn btn-primary rounded-pill px-4 py-2 fw-bold shadow-sm d-inline-flex align-items-center gap-2 small" onclick="window.handleNotifActionClick('${actionUrl}')">
            <i class="${actionIcon}"></i> ${actionText}
        </button>
    ` : '';

    return `
        <div class="notif-detail-modal-card text-start" style="font-family: inherit;">
            <!-- Header Banner -->
            <div class="p-4 text-white position-relative" style="background: ${theme.gradient}; border-radius: 18px 18px 0 0;">
                <div class="d-flex align-items-center justify-content-between mb-2">
                    <span class="badge rounded-pill px-3 py-1 fw-bold text-uppercase" style="background: rgba(255,255,255,0.22); backdrop-filter: blur(6px); font-size: 10.5px; letter-spacing: 0.5px;">
                        <i class="${theme.icon} me-1"></i> ${theme.categoryTag}
                    </span>
                    <button type="button" class="btn-close btn-close-white" onclick="Swal.close()" aria-label="Close" style="opacity: 0.85; filter: invert(1);"></button>
                </div>
                <h5 class="fw-bold mb-0 text-white" style="line-height: 1.4; font-size: 17px;">
                    ${theme.headline}
                </h5>
            </div>

            <!-- Body Content -->
            <div class="p-3.5 p-md-4" style="background: #f8fafc; max-height: 60vh; overflow-y: auto;">
                ${bodyCardsHtml}
                ${attachmentsHtml}
            </div>

            <!-- Footer Action Bar -->
            <div class="p-3 px-4 bg-white border-top d-flex align-items-center justify-content-between" style="border-radius: 0 0 18px 18px;">
                <div>${backBtn}</div>
                <div class="d-flex align-items-center gap-2">
                    <button type="button" class="btn btn-light rounded-pill px-3.5 py-2 fw-bold text-secondary border small" onclick="Swal.close()">
                        Đóng
                    </button>
                    ${actionBtn}
                </div>
            </div>
        </div>
    `;
}

let _readingNotifLock = false;
async function readNotification(id, content, fromAll = false) {
    if (_readingNotifLock) return;
    _readingNotifLock = true;
    setTimeout(() => { _readingNotifLock = false; }, 400);

    // Lưu lại thông báo để có thể quay lại từ sub-modal nếu cần
    window._lastNotifModal = { id, content, fromAll };

    // Đánh dấu đã thấy ngay lập tức để sync không coi là mới
    if (window._seenNotifIds) {
        window._seenNotifIds.add(id);
        window._seenNotifIds.add(Number(id));
        window._seenNotifIds.add(String(id));
    }

    // Gửi request đánh dấu đã đọc trên server
    fetch(`/api/notifications/${id}/read`, { method: 'PATCH' })
        .then(() => {
            document.querySelectorAll('#notifBellBadge, .notif-badge, [data-notif-count]').forEach(el => {
                let count = parseInt(el.textContent) || 0;
                if (count > 0) {
                    count--;
                    el.textContent = count;
                    if (count === 0) el.style.display = 'none';
                }
            });
        })
        .catch(console.error);

    // Lấy nội dung nếu chưa có
    if (!content && window._allNotifications && window._allNotifications[id]) {
        content = window._allNotifications[id];
    }
    if (!content) {
        try {
            const res = await fetch('/api/notifications');
            const data = await res.json();
            const found = (data || []).find(n => String(n.id) === String(id));
            if (found) {
                content = found.content;
                window._allNotifications = window._allNotifications || {};
                window._allNotifications[id] = content;
            }
        } catch (e) {}
    }
    if (!content) content = 'Thông báo hệ thống';

    const isFromAll = Boolean(fromAll);
    const htmlModal = buildModernNotificationHtml(id, content, isFromAll);

    Swal.fire({
        html: htmlModal,
        showConfirmButton: false,
        showCloseButton: false,
        width: 580,
        padding: '0',
        background: '#ffffff',
        customClass: {
            popup: 'rounded-4 shadow-lg border-0 overflow-hidden p-0'
        }
    }).then(() => {
        if (typeof _refreshNotifBadge === 'function') {
            _refreshNotifBadge();
        }
    });
}

let _showingAllNotifs = false;
async function showAllNotifications() {
    if (_showingAllNotifs) return;
    _showingAllNotifs = true;
    setTimeout(() => { _showingAllNotifs = false; }, 400);

    try {
        const res = await fetch('/api/notifications');
        const data = await res.json();
        
        if (!data || data.length === 0) {
            Swal.fire({
                icon: 'info',
                title: 'Hộp thư Thông báo',
                text: 'Bạn không có thông báo nào.',
                confirmButtonText: 'Đóng',
                confirmButtonColor: '#2563eb',
                customClass: { popup: 'rounded-4' }
            });
            return;
        }

        window._allNotifications = {};
        data.forEach(n => { window._allNotifications[n.id] = n.content; });

        const unreadCount = data.filter(n => !n.is_read).length;

        // Render card items
        let listItems = data.map(n => {
            const raw = n.content.split('|||')[0];
            const temp = document.createElement("div");
            temp.innerHTML = raw;
            const cleanText = (temp.textContent || temp.innerText || "").trim();
            const snippet = cleanText.length > 95 ? cleanText.substring(0, 95) + '...' : cleanText;

            const isFacultyApproved = n.content.includes('Khoa') && (n.content.includes('phê duyệt') || n.content.includes('ĐÃ PHÊ DUYỆT'));
            const isFacultyRevision = n.content.includes('Khoa') && (n.content.includes('chỉnh sửa') || n.content.includes('YÊU CẦU'));
            const isLecturerReview = n.content.includes('Giảng viên') || n.content.includes('GV') || n.content.includes('đánh giá') || n.content.includes('hướng dẫn');

            let badgeHtml = '<span class="badge bg-secondary-subtle text-secondary rounded-pill px-2.5 py-1 small">Hệ thống</span>';
            let iconClass = 'fa-solid fa-bell text-secondary';

            if (isFacultyApproved) {
                badgeHtml = '<span class="badge bg-success-subtle text-success border border-success-subtle rounded-pill px-2.5 py-1 small"><i class="fa-solid fa-stamp me-1"></i>Khoa đã duyệt</span>';
                iconClass = 'fa-solid fa-stamp text-success';
            } else if (isFacultyRevision) {
                badgeHtml = '<span class="badge bg-danger-subtle text-danger border border-danger-subtle rounded-pill px-2.5 py-1 small"><i class="fa-solid fa-triangle-exclamation me-1"></i>Khoa yêu cầu sửa</span>';
                iconClass = 'fa-solid fa-triangle-exclamation text-danger';
            } else if (isLecturerReview) {
                badgeHtml = '<span class="badge bg-primary-subtle text-primary border border-primary-subtle rounded-pill px-2.5 py-1 small"><i class="fa-solid fa-chalkboard-user me-1"></i>GVHD đánh giá</span>';
                iconClass = 'fa-solid fa-chalkboard-user text-primary';
            }

            return `
                <div class="list-group-item list-group-item-action p-3 mb-2 rounded-4 border ${!n.is_read ? 'border-primary-subtle bg-white shadow-xs' : 'bg-light bg-opacity-75'}"
                    style="cursor: pointer; transition: all 0.2s;"
                    onclick="event.preventDefault(); readNotification(${n.id}, window._allNotifications[${n.id}], true)">
                    <div class="d-flex align-items-start gap-3">
                        <div class="rounded-circle d-flex align-items-center justify-content-center flex-shrink-0" style="width: 38px; height: 38px; background: rgba(0,0,0,0.04);">
                            <i class="${iconClass}"></i>
                        </div>
                        <div class="flex-grow-1" style="min-width: 0;">
                            <div class="d-flex align-items-center justify-content-between mb-1">
                                <div>
                                    ${badgeHtml}
                                    ${!n.is_read ? '<span class="badge bg-danger rounded-circle p-1 ms-1" style="width:8px; height:8px; display:inline-block;"></span>' : ''}
                                </div>
                                <span class="text-muted small" style="font-size: 11px;">${n.created_at}</span>
                            </div>
                            <p class="mb-0 text-dark small" style="line-height: 1.45; font-size: 13px;">${snippet}</p>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        let modalHtml = `
            <div class="text-start" style="font-family: inherit;">
                <!-- Header -->
                <div class="p-4 text-white position-relative" style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); border-radius: 16px 16px 0 0;">
                    <div class="d-flex align-items-center justify-content-between mb-1">
                        <span class="badge rounded-pill px-3 py-1 fw-bold text-uppercase" style="background: rgba(255,255,255,0.22); font-size: 10.5px;">
                            <i class="fa-solid fa-inbox me-1"></i> HỘP THƯ HỆ THỐNG
                        </span>
                        <button type="button" class="btn-close btn-close-white" onclick="Swal.close()" aria-label="Close" style="opacity: 0.85; filter: invert(1);"></button>
                    </div>
                    <div class="d-flex align-items-baseline justify-content-between">
                        <div>
                            <h5 class="fw-bold mb-0 text-white">Tất cả Thông báo</h5>
                            <small class="text-white-50">Tổng số: ${data.length} thông báo ${unreadCount > 0 ? `• <span class="text-warning fw-bold">${unreadCount} chưa đọc</span>` : ''}</small>
                        </div>
                        <button class="btn btn-sm btn-outline-light rounded-pill px-3 py-1 fw-bold small" onclick="deleteAllReadNotifications()">
                            <i class="fa-solid fa-trash me-1"></i> Xóa đã đọc
                        </button>
                    </div>
                </div>

                <!-- List Content -->
                <div class="p-3.5 p-md-4" style="background: #f8fafc; max-height: 58vh; overflow-y: auto;">
                    <div class="list-group list-group-flush border-0">
                        ${listItems}
                    </div>
                </div>

                <!-- Footer -->
                <div class="p-3 px-4 bg-white border-top text-end" style="border-radius: 0 0 16px 16px;">
                    <button type="button" class="btn btn-light rounded-pill px-4 py-2 fw-bold text-secondary border small" onclick="Swal.close()">
                        Đóng
                    </button>
                </div>
            </div>
        `;

        Swal.fire({
            html: modalHtml,
            showConfirmButton: false,
            showCloseButton: false,
            width: 620,
            padding: '0',
            background: '#ffffff',
            customClass: {
                popup: 'rounded-4 shadow-lg border-0 overflow-hidden p-0'
            }
        });

    } catch (e) {
        console.error("Error showAllNotifications:", e);
        Swal.fire('Lỗi', 'Không thể lấy danh sách thông báo.', 'error');
    }
}

'''

text = text[:p1] + new_notif_system + text[p2:]

# Now check if window globals and handleNotifItemClick are attached
if "window.handleNotifItemClick =" not in text:
    # Add right before window.showGroupMembersModal
    anchor = "// ==========================================\n// HIỂN THỊ DANH SÁCH THÀNH VIÊN NHÓM (MODAL)\n// =========================================="
    idx_anchor = text.find(anchor)
    if idx_anchor != -1:
        globals_code = '''// Đảm bảo các hàm thông báo luôn khả dụng trên window phạm vi toàn cục
window.readNotification = readNotification;
window.showAllNotifications = showAllNotifications;
window._openNotifDetail = _openNotifDetail;
window.deleteAllReadNotifications = deleteAllReadNotifications;
window.handleNotifItemClick = function(el, e) {
    if (e) {
        e.preventDefault();
        e.stopPropagation();
    }
    const id = el.getAttribute('data-notif-id');
    let content = el.getAttribute('data-notif-content');
    if (!content && window._allNotifications && window._allNotifications[id]) {
        content = window._allNotifications[id];
    }
    if (id) {
        window.readNotification(id, content, false);
    }
};

'''
        text = text[:idx_anchor] + globals_code + text[idx_anchor:]

# Update the dropdown rendering in syncNotificationsLive
old_sync_render = """                    itemsHtml += `
                        <li>
                            <a class="dropdown-item p-3 border-bottom d-flex gap-3 align-items-start ${!notif.is_read ? 'bg-light' : ''}" href="#" onclick="readNotification(${notif.id}, decodeURIComponent('${encodedContent}'), false)">
                                <div class="bg-primary-subtle text-primary rounded-circle d-flex align-items-center justify-content-center flex-shrink-0" style="width: 32px; height: 32px;"><i class="fa-regular fa-bell"></i></div>
                                <div>
                                    <div class="fw-bold small text-dark mb-1 d-flex align-items-center justify-content-between">
                                        <span>Thông báo hệ thống</span>
                                        ${!notif.is_read ? '<span class="badge bg-danger rounded-circle p-1" style="width:8px; height:8px;"></span>' : ''}
                                    </div>
                                    <div class="small text-muted mb-1" style="line-height: 1.4; white-space: normal;">${snippet}</div>
                                    <div class="text-muted" style="font-size: 10px;">${notif.created_at}</div>
                                </div>
                            </a>
                        </li>
                    `;"""

new_sync_render = """                    window._allNotifications = window._allNotifications || {};
                    window._allNotifications[notif.id] = notif.content;

                    const isFacultyApproved = notif.content.includes('Khoa') && (notif.content.includes('phê duyệt') || notif.content.includes('ĐÃ PHÊ DUYỆT'));
                    const isFacultyRevision = notif.content.includes('Khoa') && (notif.content.includes('chỉnh sửa') || notif.content.includes('YÊU CẦU'));
                    const isLecturerReview = notif.content.includes('Giảng viên') || notif.content.includes('GV') || notif.content.includes('đánh giá') || notif.content.includes('hướng dẫn');

                    let iconClass = 'fa-regular fa-bell';
                    let iconBg = 'bg-secondary-subtle text-secondary';
                    let titleHtml = '<span class="text-dark">Thông báo hệ thống</span>';

                    if (isFacultyApproved) {
                        iconClass = 'fa-solid fa-stamp';
                        iconBg = 'bg-success-subtle text-success';
                        titleHtml = '<span class="text-success fw-bold"><i class="fa-solid fa-circle-check me-1"></i>Khoa đã phê duyệt</span>';
                    } else if (isFacultyRevision) {
                        iconClass = 'fa-solid fa-triangle-exclamation';
                        iconBg = 'bg-danger-subtle text-danger';
                        titleHtml = '<span class="text-danger fw-bold"><i class="fa-solid fa-triangle-exclamation me-1"></i>Khoa yêu cầu sửa</span>';
                    } else if (isLecturerReview) {
                        iconClass = 'fa-solid fa-chalkboard-user';
                        iconBg = 'bg-primary-subtle text-primary';
                        titleHtml = '<span class="text-primary fw-bold"><i class="fa-solid fa-user-tie me-1"></i>Đánh giá từ GVHD</span>';
                    }

                    itemsHtml += `
                        <li>
                            <a class="dropdown-item p-3 border-bottom d-flex gap-3 align-items-start notif-dropdown-item ${!notif.is_read ? 'bg-light' : ''}" 
                               href="javascript:void(0)" 
                               data-notif-id="${notif.id}"
                               onclick="event.preventDefault(); readNotification(${notif.id}, null, false)">
                                <div class="${iconBg} rounded-circle d-flex align-items-center justify-content-center flex-shrink-0" style="width: 32px; height: 32px;">
                                    <i class="${iconClass}"></i>
                                </div>
                                <div class="flex-grow-1" style="min-width: 0;">
                                    <div class="fw-bold small mb-1 d-flex align-items-center justify-content-between">
                                        ${titleHtml}
                                        ${!notif.is_read ? '<span class="badge bg-danger rounded-circle p-1" style="width:8px; height:8px;"></span>' : ''}
                                    </div>
                                    <div class="small text-muted mb-1" style="line-height: 1.4; white-space: normal;">${snippet}</div>
                                    <div class="text-muted" style="font-size: 10px;">${notif.created_at}</div>
                                </div>
                            </a>
                        </li>
                    `;"""

if old_sync_render in text:
    text = text.replace(old_sync_render, new_sync_render)
    print("SUCCESS: Updated dropdown item renderer in syncNotificationsLive!")

with open('static/assets/js/app.js', 'w', encoding='utf-8') as f:
    f.write(text)

print("SUCCESS: static/assets/js/app.js updated completely!")

