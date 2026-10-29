# scratch/redesign_notif_system.py
import re

print("=== 1. Redesigning readNotification and showAllNotifications in static/assets/js/app.js ===")

with open('static/assets/js/app.js', 'r', encoding='utf-8') as f:
    app_js = f.read()

app_js_norm = app_js.replace('\r\n', '\n')

old_read_and_show = """let _readingNotifLock = false;
async function readNotification(id, content, fromAll = false) {
    if (_readingNotifLock) return;
    _readingNotifLock = true;
    setTimeout(() => { _readingNotifLock = false; }, 400);

    // Mark as seen immediately so background sync never considers it new
    if (window._seenNotifIds) {
        window._seenNotifIds.add(id);
        window._seenNotifIds.add(Number(id));
        window._seenNotifIds.add(String(id));
    }

    // Call API patch in background without blocking modal presentation
    fetch(`/api/notifications/${id}/read`, { method: 'PATCH' })
        .then(() => {
            // Decrement badge count locally on screen
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

    let parts = (content || '').split('|||');
    let textHtml = parts[0];
    let htmlContent = `<div class="ql-editor rich-content-display" style="text-align: left; font-size: 14px; padding: 0;">${textHtml}</div>`;
    
    if (parts.length > 1) {
        htmlContent += `<hr><div style="text-align:center; display: flex; flex-direction: column; gap: 8px;">`;
        for (let i = 1; i < parts.length; i++) {
            if (parts[i].trim() !== '') {
                let fileName = parts[i].trim();
                htmlContent += `<a href="/static/uploads/batches/${encodeURIComponent(fileName)}" target="_blank" class="btn btn-outline-primary rounded-pill fw-bold"><i class="fa-solid fa-download me-2"></i>Tải về ${fileName}</a>`;
            }
        }
        htmlContent += `</div>`;
    }

    window._lastNotifModal = { id, content, fromAll };

    const isFromAll = Boolean(fromAll);

    Swal.fire({
        title: 'Chi tiết Thông báo',
        html: htmlContent,
        icon: 'info',
        showCloseButton: true,
        showCancelButton: isFromAll,
        confirmButtonText: isFromAll ? '<i class="fa-solid fa-arrow-left me-1"></i> Quay lại' : 'Đóng',
        cancelButtonText: 'Đóng',
        confirmButtonColor: '#2563eb',
        cancelButtonColor: '#64748b',
        customClass: {
            popup: 'p-4 rounded-4'
        },
        didOpen: (popup) => {
            const links = popup.querySelectorAll('a[href]');
            links.forEach(a => {
                a.addEventListener('click', (e) => {
                    const href = a.getAttribute('href');
                    if (href) {
                        e.preventDefault();
                        Swal.close();
                        if (href.includes('#s-') || (href.startsWith('/student#'))) {
                            const tabTarget = href.split('#')[1] || 's-chat';
                            window.refreshStudentViewsLive(() => {
                                if (typeof switchTab === 'function') {
                                    switchTab(tabTarget, document.querySelector(`a[href*="${tabTarget}"]`));
                                }
                            });
                        } else {
                            window.location.href = href;
                        }
                    }
                });
            });
        }
    }).then((result) => {
        _refreshNotifBadge();
        if (window._isOpeningMembersModal) {
            // Đang chuyển sang modal thành viên nhóm, không tự mở lại danh sách thông báo
            return;
        }
        if (isFromAll && result.isConfirmed) {
            // Reopen the notification list without full page reload
            showAllNotifications();
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
            Swal.fire('Thông báo', 'Bạn không có thông báo nào.', 'info');
            return;
        }

        // Store notifications globally so onclick can access by id
        window._allNotifications = {};
        data.forEach(n => { window._allNotifications[n.id] = n.content; });

        let html = `
        <div class="d-flex justify-content-between align-items-center mb-2">
            <span class="text-muted small fw-bold"><i class="fa-solid fa-list me-1"></i>Danh sách thông báo</span>
            <button class="btn btn-sm btn-outline-danger py-0 px-2 rounded-pill" onclick="Swal.close(); setTimeout(() => deleteAllReadNotifications(), 300)"><i class="fa-solid fa-trash me-1"></i>Xóa đã đọc</button>
        </div>
        <div class="list-group text-start" style="max-height: 400px; overflow-y: auto;">`;

        data.forEach(n => {
            let badge = !n.is_read ? '<span class="badge bg-danger rounded-circle p-1 ms-1" style="width:8px; height:8px; display:inline-block;"></span>' : '';
            let temp = document.createElement("div");
            temp.innerHTML = n.content.split('|||')[0];
            let cleanText = temp.textContent || temp.innerText || "";
            if (cleanText.length > 100) cleanText = cleanText.substring(0, 100) + '...';
            // Escape for HTML attribute
            let safeText = cleanText.replace(/"/g, '&quot;').replace(/'/g, '&#39;');

            html += `
                <a href="#" class="list-group-item list-group-item-action py-3 ${!n.is_read ? 'bg-light' : ''}"
                    data-notif-id="${n.id}"
                    onclick="event.preventDefault(); _openNotifDetail(${n.id})"
                    ondblclick="event.preventDefault(); return false;">
                    <div class="d-flex w-100 justify-content-between align-items-center">
                        <strong class="mb-1 text-primary small"><i class="fa-solid fa-envelope me-2"></i>Hệ thống ${badge}</strong>
                        <small class="text-muted" style="font-size:10px;">${n.created_at}</small>
                    </div>
                    <p class="mb-0 small text-muted mt-1" style="white-space: normal; line-height: 1.4;">${safeText}</p>
                </a>
            `;
        });
        html += '</div>';

        Swal.fire({
            title: 'Tất cả Thông báo',
            html: html,
            showConfirmButton: false,
            showCloseButton: true,
            width: 620,
            customClass: {
                popup: 'p-4 rounded-4'
            }
        }).then(() => {
            // Just refresh the badge count without full page reload
            _refreshNotifBadge();
        });

    } catch (e) {
        Swal.fire('Lỗi', 'Không thể lấy danh sách thông báo.', 'error');
    }
}"""

new_read_and_show = """// ====================================================================
// MODAL CHI TIẾT THÔNG BÁO HIỆN ĐẠI (CHUNG CHO SINH VIÊN, GIẢNG VIÊN & KHOA)
// ====================================================================
window.handleNotifActionClick = function(href) {
    if (!href) return;
    if (typeof Swal !== 'undefined') Swal.close();

    // Xử lý chuyển tab trực tiếp nếu đang ở trang Sinh viên
    if (href.includes('#s-') || href.startsWith('/student#')) {
        const tabTarget = href.split('#')[1] || 's-submit';
        if (window.location.pathname.startsWith('/student') || window.location.pathname === '/') {
            if (typeof switchTab === 'function') {
                const navLink = document.querySelector(`a[href*="${tabTarget}"]`);
                switchTab(tabTarget, navLink);
            }
            if (tabTarget === 's-submit') {
                const topicIdInput = document.getElementById('submission-topic-id');
                if (topicIdInput && topicIdInput.value && typeof window.renderSubmissionHistory === 'function') {
                    window.renderSubmissionHistory(parseInt(topicIdInput.value));
                }
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

    // 1. Phân tích Link hành động (Button hành động chính)
    let actionUrl = '';
    let actionText = '';
    let actionIcon = 'fa-solid fa-arrow-up-right-from-square';

    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = mainHtml;

    const linkEl = tempDiv.querySelector('a[href]');
    if (linkEl) {
        actionUrl = linkEl.getAttribute('href') || '';
        actionText = linkEl.textContent.trim() || 'Xem chi tiết';
        if (actionUrl.includes('submit')) {
            actionIcon = 'fa-solid fa-file-arrow-up';
            actionText = 'Xem Hồ sơ Bài nộp';
        } else if (actionUrl.includes('chat')) {
            actionIcon = 'fa-solid fa-comments';
            actionText = 'Vào phòng Chat Nhóm';
        } else if (actionUrl.includes('progress')) {
            actionIcon = 'fa-solid fa-chart-line';
            actionText = 'Xem Tiến độ Đề tài';
        } else if (actionUrl.includes('calendar')) {
            actionIcon = 'fa-solid fa-calendar-check';
            actionText = 'Xem Lịch làm việc';
        }
        linkEl.remove();
    }

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
    const isFacultyRevision = textContent.includes('Khoa') && (textContent.includes('chỉnh sửa') || textContent.includes('YÊU CẦU CHỈNH SỬA'));
    const isLecturerApproved = (textContent.includes('Giảng viên') || textContent.includes('GVHD') || textContent.includes('TS.')) && (textContent.includes('phê duyệt') || textContent.includes('ĐÃ DUYỆT'));
    const isLecturerRevision = (textContent.includes('Giảng viên') || textContent.includes('GVHD') || textContent.includes('TS.')) && (textContent.includes('yêu cầu') || textContent.includes('chỉnh sửa'));
    const isLecturerReview = (textContent.includes('Giảng viên') || textContent.includes('GVHD') || textContent.includes('TS.')) && (textContent.includes('đánh giá') || textContent.includes('ghi chú'));
    const isTopicApproval = textContent.includes('phê duyệt đề tài') || (textContent.includes('Đề tài NCKH') && textContent.includes('chính thức phê duyệt'));
    const isBatchAnnouncement = textContent.includes('Đợt NCKH:') || textContent.includes('NCKH 20');
    const isCalendarMeeting = textContent.includes('Lịch hẹn') || textContent.includes('lịch hẹn');
    const isCouncil = textContent.includes('Hội đồng') || textContent.includes('hội đồng');

    if (isFacultyApproval) {
        theme.gradient = 'linear-gradient(135deg, #065f46 0%, #059669 100%)';
        theme.categoryTag = 'KHOA CÔNG NGHỆ THÔNG TIN • PHÊ DUYỆT';
        theme.icon = 'fa-solid fa-stamp';
        theme.headline = 'Khoa CNTT đã phê duyệt Đạt yêu cầu';
        theme.isApproval = true;
    } else if (isFacultyRevision) {
        theme.gradient = 'linear-gradient(135deg, #991b1b 0%, #dc2626 100%)';
        theme.categoryTag = 'KHOA CÔNG NGHỆ THÔNG TIN • YÊU CẦU SỬA';
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
    const topicRegex = /Đề tài:\s*(?:<strong>)?(.*?)(?:<\/strong>)?(?:\s*\((.*?)\))?(?:<\/p>|<br>|\n|$)/i;
    const topicMatch = mainHtml.match(topicRegex) 
                    || mainHtml.match(/đề tài NCKH(?:\s*<strong>)?:\s*(.*?)(?:<\/strong>)?(?:<\/p>|<br>|\n|$)/i)
                    || mainHtml.match(/đề tài\s*(?:<strong>)?["'“]?([^"'”<]+)["'”]?/i);
    if (topicMatch) {
        topicTitle = topicMatch[1] ? topicMatch[1].replace(/<\/?[^>]+(>|$)/g, "").trim() : '';
        if (topicMatch[2]) {
            docVersionFile = topicMatch[2].replace(/<\/?[^>]+(>|$)/g, "").trim();
        }
    }

    // Tìm kết quả thẩm định
    const badgeMatch = mainHtml.match(/<span class="badge[^"]*">(.*?)<\/span>/i);
    if (badgeMatch) {
        statusLabel = badgeMatch[1].replace(/<\/?[^>]+(>|$)/g, "").trim();
    }

    // Tìm ý kiến chỉ đạo / ghi chú
    const feedbackRegex = /(?:Ý kiến chỉ đạo(?: của Khoa| từ Khoa)?:?|Ghi chú(?: từ GV)?:?|Nhận xét(?: của Giảng viên)?:?|Lý do(?: từ chối)?:?)\s*(?:<\/strong>)?\s*([\s\S]*?)(?:<\/p>|<a |$)/i;
    const feedbackMatch = mainHtml.match(feedbackRegex);
    if (feedbackMatch) {
        feedbackText = feedbackMatch[1].replace(/<\/?[^>]+(>|$)/g, "").trim();
    }

    // Tìm dòng tiêu đề đầu tiên nếu có
    const strongHeaderMatch = mainHtml.match(/<p><strong>(.*?)<\/strong><\/p>/i) || mainHtml.match(/<strong>(.*?)<\/strong>/i);
    if (strongHeaderMatch) {
        const hText = strongHeaderMatch[1].replace(/<\/?[^>]+(>|$)/g, "").trim();
        if (hText.length > 5 && !hText.includes('Đề tài:') && !hText.includes('Kết quả') && !hText.includes('Ý kiến')) {
            theme.headline = hText;
        }
    }

    // 4. Xây dựng khối HTML giao diện hiện đại
    let bodyCardsHtml = '';

    if (topicTitle || statusLabel) {
        // Cấu trúc dạng thẻ bài nộp / đề tài
        bodyCardsHtml += `
            <!-- Khối thông tin Đề tài & Bài nộp -->
            <div class="p-3 rounded-4 bg-white border border-slate-200 shadow-xs mb-3">
                <div class="d-flex align-items-center justify-content-between mb-1.5 flex-wrap gap-1">
                    <span class="badge bg-primary-subtle text-primary border border-primary-subtle rounded-pill px-2.5 py-1 fw-bold" style="font-size: 11px;">
                        <i class="fa-solid fa-book-bookmark me-1"></i> Đề tài NCKH
                    </span>
                    ${docVersionFile ? `<span class="badge bg-secondary-subtle text-secondary rounded-pill px-2.5 py-1" style="font-size: 11px;"><i class="fa-solid fa-file-lines me-1"></i> ${docVersionFile}</span>` : ''}
                </div>
                <div class="fw-bold text-dark fs-6" style="line-height: 1.45;">
                    ${topicTitle || 'Nghiên cứu khoa học sinh viên'}
                </div>
            </div>
        `;

        if (statusLabel) {
            let sBg = '#ecfdf5', sBorder = '#a7f3d0', sText = '#065f46', sIcon = 'fa-solid fa-circle-check', sIconColor = '#059669', sIconBg = '#d1fae5';
            if (theme.isRevision || statusLabel.includes('YÊU CẦU') || statusLabel.includes('TỪ CHỐI')) {
                sBg = '#fef2f2'; sBorder = '#fecaca'; sText = '#991b1b'; sIcon = 'fa-solid fa-triangle-exclamation'; sIconColor = '#dc2626'; sIconBg = '#fee2e2';
            } else if (statusLabel.includes('CHỜ') || statusLabel.includes('ĐANG')) {
                sBg = '#fffbeb'; sBorder = '#fde68a'; sText = '#b45309'; sIcon = 'fa-solid fa-clock'; sIconColor = '#d97706'; sIconBg = '#fef3c7';
            }

            bodyCardsHtml += `
                <!-- Khối Quyết định thẩm định -->
                <div class="p-3 rounded-4 mb-3 d-flex align-items-center gap-3 shadow-xs" style="background: ${sBg}; border: 1.5px solid ${sBorder};">
                    <div class="rounded-circle d-flex align-items-center justify-content-center flex-shrink-0" style="width: 42px; height: 42px; background: ${sIconBg}; color: ${sIconColor}; font-size: 20px;">
                        <i class="${sIcon}"></i>
                    </div>
                    <div>
                        <div class="text-uppercase fw-bold" style="font-size: 10.5px; letter-spacing: 0.5px; color: ${sText}; opacity: 0.85;">Quyết định & Kết quả thẩm định:</div>
                        <div class="fw-bold" style="font-size: 14.5px; color: ${sText};">
                            ${statusLabel}
                        </div>
                    </div>
                </div>
            `;
        }

        if (feedbackText) {
            bodyCardsHtml += `
                <!-- Khối Ý kiến chỉ đạo / Nhận xét -->
                <div class="p-3 rounded-4 mb-3" style="background: #fffbeb; border: 1px solid #fde68a; border-left: 5px solid #f59e0b;">
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
            <div class="p-3 rounded-4 bg-white border border-slate-200 shadow-xs mb-3">
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
            <div class="p-3 rounded-4 bg-white border border-slate-200 shadow-xs mb-3">
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
        <span class="text-muted small" style="font-size: 11.5px;">
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
            <div class="p-4 text-white position-relative" style="background: ${theme.gradient}; border-radius: 16px 16px 0 0;">
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
            <div class="p-3.5 p-md-4" style="background: #f8fafc; max-height: 62vh; overflow-y: auto;">
                ${bodyCardsHtml}
                ${attachmentsHtml}
            </div>

            <!-- Footer Action Bar -->
            <div class="p-3 px-4 bg-white border-top d-flex align-items-center justify-content-between" style="border-radius: 0 0 16px 16px;">
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

    // Mark as seen immediately so background sync never considers it new
    if (window._seenNotifIds) {
        window._seenNotifIds.add(id);
        window._seenNotifIds.add(Number(id));
        window._seenNotifIds.add(String(id));
    }

    // Call API patch in background without blocking modal presentation
    fetch(`/api/notifications/${id}/read`, { method: 'PATCH' })
        .then(() => {
            // Decrement badge count locally on screen
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
        _refreshNotifBadge();
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

        // Render clean card list items
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
                    <div class="d-flex align-items-center justify-content-between">
                        <div>
                            <h5 class="fw-bold mb-0 text-white" style="font-size: 18px;">Tất cả Thông báo</h5>
                            <small class="text-white-50">Tổng số: ${data.length} thông báo ${unreadCount > 0 ? `• <span class="text-warning fw-bold">${unreadCount} chưa đọc</span>` : ''}</small>
                        </div>
                        <button class="btn btn-sm btn-light rounded-pill px-3 py-1.5 fw-bold shadow-xs text-danger" onclick="Swal.close(); setTimeout(() => deleteAllReadNotifications(), 250)">
                            <i class="fa-solid fa-trash me-1"></i> Xóa đã đọc
                        </button>
                    </div>
                </div>

                <!-- Body List -->
                <div class="p-3.5" style="background: #f8fafc; max-height: 60vh; overflow-y: auto;">
                    ${listItems}
                </div>

                <!-- Footer -->
                <div class="p-3 px-4 bg-white border-top d-flex align-items-center justify-content-end" style="border-radius: 0 0 16px 16px;">
                    <button type="button" class="btn btn-light rounded-pill px-4 py-1.5 fw-bold text-secondary border small" onclick="Swal.close()">
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
        }).then(() => {
            _refreshNotifBadge();
        });

    } catch (e) {
        Swal.fire('Lỗi', 'Không thể lấy danh sách thông báo.', 'error');
    }
}"""

assert old_read_and_show in app_js_norm, "old_read_and_show not found in app.js"
app_js_norm = app_js_norm.replace(old_read_and_show, new_read_and_show, 1)

with open('static/assets/js/app.js', 'w', encoding='utf-8') as f:
    f.write(app_js_norm)

print("Updated static/assets/js/app.js successfully!")


print("\n=== 2. Updating templates/layouts/lecturer_layout.html dropdown ===")
with open('templates/layouts/lecturer_layout.html', 'r', encoding='utf-8') as f:
    lec_html = f.read()

lec_html_norm = lec_html.replace('\r\n', '\n')

old_lec_dropdown = """                        <div style="max-height: 360px; overflow-y: auto;">
                            {% if notifications %}
                                {% for notif in notifications %}
                                <li>
                                    <a class="dropdown-item p-3 border-bottom d-flex gap-3 align-items-start notif-dropdown-item {% if not notif.is_read %}bg-light{% endif %}" 
                                       href="javascript:void(0)" 
                                       data-notif-id="{{ notif.id }}" 
                                       data-notif-content="{{ notif.content | e }}" 
                                       onclick="event.preventDefault(); window.handleNotifItemClick(this, event)">
                                        <div class="bg-primary-subtle text-primary rounded-circle d-flex align-items-center justify-content-center flex-shrink-0" style="width: 32px; height: 32px;"><i class="fa-regular fa-bell"></i></div>
                                        <div>
                                            <div class="fw-bold small text-dark mb-1 d-flex align-items-center justify-content-between">
                                                <span>Thông báo hệ thống</span>
                                                {% if not notif.is_read %}
                                                    <span class="badge bg-danger rounded-circle p-1" style="width:8px; height:8px;"></span>
                                                {% endif %}
                                            </div>
                                            <div class="small text-muted mb-1" style="line-height: 1.4; white-space: normal;">{{ notif.content.split('|||')[0] | striptags | truncate(80) }}</div>
                                            <div class="text-muted" style="font-size: 10px;">{{ notif.created_at.strftime('%d/%m/%Y %H:%M') if notif.created_at else '' }}</div>
                                        </div>
                                    </a>
                                </li>
                                {% endfor %}
                            {% else %}
                                <li class="p-3 text-center text-muted small">Không có thông báo nào</li>
                            {% endif %}
                        </div>"""

new_lec_dropdown = """                        <div style="max-height: 360px; overflow-y: auto;">
                            {% if notifications %}
                                {% for notif in notifications %}
                                {% set is_faculty_approved = 'Khoa' in notif.content and ('phê duyệt' in notif.content or 'ĐÃ PHÊ DUYỆT' in notif.content) %}
                                {% set is_faculty_revision = 'Khoa' in notif.content and ('chỉnh sửa' in notif.content or 'YÊU CẦU' in notif.content) %}
                                {% set is_lecturer_review = 'Giảng viên' in notif.content or 'GV' in notif.content or 'đánh giá' in notif.content or 'hướng dẫn' in notif.content %}
                                <li>
                                    <a class="dropdown-item p-3 border-bottom d-flex gap-3 align-items-start notif-dropdown-item {% if not notif.is_read %}bg-light{% endif %}" 
                                       href="javascript:void(0)" 
                                       data-notif-id="{{ notif.id }}" 
                                       data-notif-content="{{ notif.content | e }}" 
                                       onclick="event.preventDefault(); window.handleNotifItemClick(this, event)">
                                        <div class="{% if is_faculty_approved %}bg-success-subtle text-success{% elif is_faculty_revision %}bg-danger-subtle text-danger{% elif is_lecturer_review %}bg-primary-subtle text-primary{% else %}bg-secondary-subtle text-secondary{% endif %} rounded-circle d-flex align-items-center justify-content-center flex-shrink-0" style="width: 32px; height: 32px;">
                                            <i class="{% if is_faculty_approved %}fa-solid fa-stamp{% elif is_faculty_revision %}fa-solid fa-triangle-exclamation{% elif is_lecturer_review %}fa-solid fa-chalkboard-user{% else %}fa-regular fa-bell{% endif %}"></i>
                                        </div>
                                        <div class="flex-grow-1" style="min-width: 0;">
                                            <div class="fw-bold small mb-1 d-flex align-items-center justify-content-between">
                                                <span class="{% if is_faculty_approved %}text-success{% elif is_faculty_revision %}text-danger{% elif is_lecturer_review %}text-primary{% else %}text-dark{% endif %}">
                                                    {% if is_faculty_approved %}
                                                        <i class="fa-solid fa-circle-check me-1"></i>Khoa đã phê duyệt
                                                    {% elif is_faculty_revision %}
                                                        <i class="fa-solid fa-triangle-exclamation me-1"></i>Khoa yêu cầu sửa
                                                    {% elif is_lecturer_review %}
                                                        <i class="fa-solid fa-user-tie me-1"></i>Đánh giá bài nộp
                                                    {% else %}
                                                        Thông báo hệ thống
                                                    {% endif %}
                                                </span>
                                                {% if not notif.is_read %}
                                                    <span class="badge bg-danger rounded-circle p-1" style="width:8px; height:8px;"></span>
                                                {% endif %}
                                            </div>
                                            <div class="small text-muted mb-1" style="line-height: 1.4; white-space: normal;">{{ notif.content.split('|||')[0] | striptags | replace('\n', ' ') | truncate(85) }}</div>
                                            <div class="text-muted" style="font-size: 10px;">{{ notif.created_at.strftime('%d/%m/%Y %H:%M') if notif.created_at else '' }}</div>
                                        </div>
                                    </a>
                                </li>
                                {% endfor %}
                            {% else %}
                                <li class="p-3 text-center text-muted small">Không có thông báo nào</li>
                            {% endif %}
                        </div>"""

assert old_lec_dropdown in lec_html_norm, "old_lec_dropdown not found in lecturer_layout.html"
lec_html_norm = lec_html_norm.replace(old_lec_dropdown, new_lec_dropdown, 1)

with open('templates/layouts/lecturer_layout.html', 'w', encoding='utf-8') as f:
    f.write(lec_html_norm)

print("Updated templates/layouts/lecturer_layout.html successfully!")


print("\n=== 3. Updating templates/layouts/faculty_layout.html dropdown ===")
with open('templates/layouts/faculty_layout.html', 'r', encoding='utf-8') as f:
    fac_html = f.read()

fac_html_norm = fac_html.replace('\r\n', '\n')

assert old_lec_dropdown in fac_html_norm, "old_lec_dropdown not found in faculty_layout.html"
fac_html_norm = fac_html_norm.replace(old_lec_dropdown, new_lec_dropdown, 1)

with open('templates/layouts/faculty_layout.html', 'w', encoding='utf-8') as f:
    f.write(fac_html_norm)

print("Updated templates/layouts/faculty_layout.html successfully!")

