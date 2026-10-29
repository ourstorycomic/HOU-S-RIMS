// static/assets/js/submissions.js
// ============================================================
// HOU S-RIMS - Module Nộp Đề cương & Báo cáo Nghiên cứu
// ============================================================

let currentSubmissionType = 'outline';
let selectedSubmissionFile = null;

const SUBMISSION_TYPE_CONFIG = {
    'outline': {
        title: 'Nộp Đề cương nghiên cứu chi tiết',
        badge: 'Đề cương chi tiết',
        desc: 'Bản thuyết minh chi tiết gồm: Mục tiêu, đối tượng, phương pháp nghiên cứu, kế hoạch triển khai và dự toán kinh phí. Định dạng: PDF hoặc DOCX.',
        icon: 'fa-solid fa-scroll',
        color: '#6366f1'
    },
    'progress': {
        title: 'Nộp Báo cáo tiến độ theo cột mốc',
        badge: 'Báo cáo tiến độ',
        desc: 'Báo cáo khối lượng công việc đã hoàn thành, dữ liệu thu thập được hoặc sản phẩm trung gian theo từng mốc quy định.',
        icon: 'fa-solid fa-chart-line',
        color: '#0ea5e9'
    },
    'final': {
        title: 'Nộp Báo cáo tổng kết & Nghiệm thu',
        badge: 'Báo cáo tổng kết',
        desc: 'Báo cáo toàn văn hoàn chỉnh kết quả NCKH, bản tóm tắt kết quả nghiên cứu và sản phẩm ứng dụng sẵn sàng nghiệm thu.',
        icon: 'fa-solid fa-award',
        color: '#10b981'
    },
    'slide': {
        title: 'Nộp Slide thuyết trình bảo vệ',
        badge: 'Slide thuyết trình',
        desc: 'File slide thuyết trình (.pptx hoặc .pdf) để trình chiếu và bảo vệ trước Hội đồng nghiệm thu cấp Khoa/Trường.',
        icon: 'fa-solid fa-file-powerpoint',
        color: '#f59e0b'
    }
};

function selectSubmissionType(type) {
    currentSubmissionType = type;
    
    // Update pills UI
    document.querySelectorAll('.submission-type-pill, [data-type]').forEach(pill => {
        if (pill.getAttribute('data-type') === type) {
            pill.classList.remove('btn-light', 'text-muted');
            pill.classList.add('btn-primary', 'active', 'shadow-sm');
        } else {
            pill.classList.remove('btn-primary', 'active', 'shadow-sm');
            pill.classList.add('btn-light', 'text-muted');
        }
    });

    // Update banner & descriptions
    const config = SUBMISSION_TYPE_CONFIG[type] || SUBMISSION_TYPE_CONFIG['outline'];
    const titleEl = document.getElementById('submission-type-title') || document.getElementById('submission-form-title');
    const descEl = document.getElementById('submission-type-desc');
    const badgeEl = document.getElementById('submission-type-badge') || document.getElementById('submission-active-type-badge');
    const milestoneWrap = document.getElementById('submission-milestone-wrap') || document.getElementById('milestone-container');

    if (titleEl) titleEl.textContent = config.title;
    if (descEl) descEl.textContent = config.desc;
    if (badgeEl) {
        badgeEl.textContent = config.badge;
        badgeEl.style.backgroundColor = config.color;
    }

    // Show milestone select only for progress
    if (milestoneWrap) {
        if (type === 'progress') {
            milestoneWrap.classList.remove('d-none');
        } else {
            milestoneWrap.classList.add('d-none');
        }
    }

    // Reload history list for current topic and type
    const topicIdInput = document.getElementById('submission-topic-id');
    if (topicIdInput && topicIdInput.value) {
        renderSubmissionHistory(parseInt(topicIdInput.value), type);
    }
}

function handleFileSelect(file) {
    if (!file) return;
    
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (file.size > maxSize) {
        Swal.fire('File quá lớn', 'Kích thước tệp vượt quá 50MB. Vui lòng chọn tệp nhỏ hơn.', 'warning');
        return;
    }

    selectedSubmissionFile = file;
    const preview = document.getElementById('submission-file-preview');
    const nameEl = document.getElementById('submission-file-name');
    const sizeEl = document.getElementById('submission-file-size');
    const iconEl = document.getElementById('submission-file-icon');
    const dropzoneContent = document.getElementById('submission-dropzone-content');
    const filenameDisplay = document.getElementById('submission-filename-display');

    if (nameEl) nameEl.textContent = file.name;
    if (sizeEl) sizeEl.textContent = (file.size / (1024 * 1024)).toFixed(2) + ' MB';
    if (filenameDisplay) filenameDisplay.innerHTML = `<span class="text-primary fw-bold"><i class="fa-solid fa-file me-1"></i> ${file.name}</span>`;
    
    const ext = file.name.split('.').pop().toLowerCase();
    let iconClass = 'fa-solid fa-file';
    if (['pdf'].includes(ext)) iconClass = 'fa-solid fa-file-pdf text-danger';
    else if (['doc', 'docx'].includes(ext)) iconClass = 'fa-solid fa-file-word text-primary';
    else if (['ppt', 'pptx'].includes(ext)) iconClass = 'fa-solid fa-file-powerpoint text-warning';
    else if (['zip', 'rar', '7z'].includes(ext)) iconClass = 'fa-solid fa-file-zipper text-secondary';
    else if (['xls', 'xlsx', 'csv'].includes(ext)) iconClass = 'fa-solid fa-file-excel text-success';
    
    if (iconEl) iconEl.innerHTML = `<i class="${iconClass} fs-2"></i>`;
    if (preview) preview.classList.remove('d-none');
    if (dropzoneContent) dropzoneContent.classList.add('d-none');

    // Sync input[type="file"]
    const fileInput = document.getElementById('submission-file-input');
    if (fileInput) {
        try {
            const dt = new DataTransfer();
            dt.items.add(file);
            fileInput.files = dt.files;
        } catch (e) {}
    }
}

function clearSubmissionFile() {
    selectedSubmissionFile = null;
    const fileInput = document.getElementById('submission-file-input');
    if (fileInput) fileInput.value = '';
    
    const preview = document.getElementById('submission-file-preview');
    const dropzoneContent = document.getElementById('submission-dropzone-content');
    const filenameDisplay = document.getElementById('submission-filename-display');

    if (preview) preview.classList.add('d-none');
    if (dropzoneContent) dropzoneContent.classList.remove('d-none');
    if (filenameDisplay) filenameDisplay.innerHTML = `Kéo thả tệp hoặc <span class="text-primary text-decoration-underline" style="pointer-events: auto;">nhấn để chọn</span>`;

    // Clear Word-like editor content
    const notesEditor = document.getElementById('submissionNotesEditor');
    if (notesEditor) notesEditor.innerHTML = '';
    const notesInput = document.getElementById('submission-notes');
    if (notesInput) notesInput.value = '';
    const wordCount = document.getElementById('submissionNotesWordCount');
    if (wordCount) wordCount.textContent = '0 từ • 0 ký tự';
}

async function submitCurrentReport() {
    const topicIdEl = document.getElementById('submission-topic-id');
    const topicId = topicIdEl ? topicIdEl.value : null;

    if (!topicId) {
        Swal.fire('Chưa có đề tài', 'Nhóm của bạn chưa có đề tài nghiên cứu hợp lệ để nộp bài.', 'warning');
        return;
    }

    if (!selectedSubmissionFile) {
        Swal.fire('Chưa chọn file', 'Vui lòng kéo thả hoặc chọn tệp đề cương/báo cáo cần nộp!', 'warning');
        return;
    }

    const milestoneSelect = document.getElementById('submission-milestone-select');
    const milestoneId = (currentSubmissionType === 'progress' && milestoneSelect) ? milestoneSelect.value : '';
    const externalLink = (document.getElementById('submission-external-link')?.value || '').trim();
    
    // Đồng bộ nội dung ghi chú phong phú từ Word editor
    if (typeof syncSubmissionNotesFromEditor === 'function') {
        syncSubmissionNotesFromEditor();
    }
    const notes = (document.getElementById('submission-notes')?.value || '').trim();

    const config = SUBMISSION_TYPE_CONFIG[currentSubmissionType] || {};
    const confirmResult = await Swal.fire({
        title: 'Xác nhận nộp tài liệu?',
        text: `Bạn chuẩn bị nộp file "${selectedSubmissionFile.name}" cho mục [${config.badge || 'Báo cáo'}]. Giảng viên hướng dẫn sẽ nhận được thông báo để kiểm tra và nhận xét.`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Đồng ý nộp',
        cancelButtonText: 'Kiểm tra lại',
        confirmButtonColor: '#6366f1'
    });

    if (!confirmResult.isConfirmed) return;

    const submitBtn = document.getElementById('btn-submit-report');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i> Đang tải lên và gửi thông báo...';
    }

    const formData = new FormData();
    formData.append('file', selectedSubmissionFile);
    formData.append('topic_id', topicId);
    formData.append('type', currentSubmissionType);
    if (milestoneId) formData.append('milestone_id', milestoneId);
    if (externalLink) formData.append('external_link', externalLink);
    if (notes) formData.append('notes', notes);

    try {
        const resp = await fetch('/api/submissions/upload', {
            method: 'POST',
            body: formData
        });

        const resData = await resp.json();

        if (resp.ok && resData.success) {
            Swal.fire({
                title: 'Nộp thành công!',
                text: resData.message || 'Tài liệu đã được ghi nhận. Giảng viên hướng dẫn đã nhận được thông báo.',
                icon: 'success',
                confirmButtonColor: '#6366f1'
            });

            // Reset form inputs
            clearSubmissionFile();
            if (document.getElementById('submission-external-link')) document.getElementById('submission-external-link').value = '';
            if (document.getElementById('submission-notes')) document.getElementById('submission-notes').value = '';

            // Reload history list
            renderSubmissionHistory(parseInt(topicId), currentSubmissionType);
        } else {
            Swal.fire('Lỗi khi nộp bài', resData.message || 'Không thể tải tệp lên máy chủ.', 'error');
        }
    } catch (err) {
        console.error('Submission upload error:', err);
        Swal.fire('Lỗi hệ thống', 'Đã xảy ra lỗi kết nối với máy chủ khi nộp bài.', 'error');
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fa-solid fa-paper-plane me-2"></i> Xác nhận Nộp tài liệu';
        }
    }
}

let cachedSubmissions = [];

async function renderSubmissionHistory(topicId, filterType = null) {
    const listEl = document.getElementById('submission-history-list');
    if (!listEl) return;

    listEl.innerHTML = `
        <div class="text-center py-5 text-muted">
            <div class="spinner-border spinner-border-sm text-primary me-2"></div>
            Đang tải lịch sử nộp bài...
        </div>
    `;

    try {
        const url = `/api/submissions/topic/${topicId}` + (filterType ? `?type=${filterType}` : '');
        const resp = await fetch(url);
        const data = await resp.json();

        if (!resp.ok || !data.success) {
            listEl.innerHTML = '<div class="text-center text-muted py-4 small">Chưa thể tải dữ liệu lịch sử nộp bài.</div>';
            return;
        }

        const items = data.submissions || [];
        cachedSubmissions = items;

        if (items.length === 0) {
            const config = SUBMISSION_TYPE_CONFIG[filterType] || {};
            listEl.innerHTML = `
                <div class="text-center py-5 px-3 text-muted">
                    <div class="bg-light rounded-circle d-inline-flex p-3 mb-3 text-secondary">
                        <i class="fa-solid fa-folder-open fs-2 opacity-50"></i>
                    </div>
                    <h6 class="fw-bold text-dark mb-1">Chưa có bài nộp nào</h6>
                    <p class="small text-muted mb-0">Chưa có tệp nào được nộp cho mục <strong>${config.badge || 'này'}</strong>. Bạn có thể sử dụng khung nộp bài bên trái để nộp phiên bản đầu tiên.</p>
                </div>
            `;
            return;
        }

        function formatFacultyFeedback(feedback) {
            if (!feedback) return 'Khoa đã phê duyệt chính thức thông qua báo cáo/đề cương này.';
            // Clean repeated blocks, dates, and separator dashes
            const rawLines = feedback.split(/\n+/);
            const cleanedLines = [];
            const seenSentences = new Set();

            for (let line of rawLines) {
                line = line.trim();
                if (!line || /^---\s*[\d\/: ]+\s*---$/.test(line) || line === '---') continue;

                // Strip timestamp prefixes like [02:45:44 26/10/2026]
                const core = line.replace(/^\[[\d\/: ]+\]\s*/, '').trim();
                if (!core) continue;

                if (!seenSentences.has(core)) {
                    seenSentences.add(core);
                    cleanedLines.push(line);
                }
            }

            return cleanedLines.length > 0 ? cleanedLines.join('\n') : feedback.trim();
        }

        function renderSubmissionCard(sub, isLatest) {
            let statusBadge = '';
            let borderClass = isLatest ? 'border-primary' : 'border-light-subtle';

            if (sub.status === 'approved') {
                statusBadge = '<span class="badge bg-success-subtle text-success border border-success-subtle rounded-pill px-2.5 py-1 small"><i class="fa-solid fa-circle-check me-1"></i>GVHD: ĐÃ DUYỆT</span>';
                if (sub.faculty_status === 'approved') {
                    statusBadge += ' <span class="badge bg-primary text-white rounded-pill px-2.5 py-1 small ms-1"><i class="fa-solid fa-stamp me-1"></i>KHOA ĐÃ DUYỆT</span>';
                } else if (sub.faculty_status === 'revision_required') {
                    statusBadge += ' <span class="badge bg-danger text-white rounded-pill px-2.5 py-1 small ms-1"><i class="fa-solid fa-triangle-exclamation me-1"></i>KHOA: YÊU CẦU SỬA</span>';
                }
                borderClass = isLatest ? 'border-success' : 'border-light-subtle';
            } else if (sub.status === 'revision_required') {
                statusBadge = '<span class="badge bg-danger-subtle text-danger border border-danger-subtle rounded-pill px-2.5 py-1 small"><i class="fa-solid fa-triangle-exclamation me-1"></i>CẦN CHỈNH SỬA LẠI</span>';
                borderClass = isLatest ? 'border-danger' : 'border-light-subtle';
            } else {
                statusBadge = '<span class="badge bg-warning-subtle text-warning-emphasis border border-warning-subtle rounded-pill px-2.5 py-1 small"><i class="fa-regular fa-clock me-1"></i>CHỜ GVHD XEM XÉT</span>';
                borderClass = isLatest ? 'border-warning' : 'border-light-subtle';
            }

            const typeLabel = SUBMISSION_TYPE_CONFIG[sub.type]?.badge || sub.type;
            const cleanFeedback = formatFacultyFeedback(sub.faculty_feedback);

            return `
                <div class="card border ${borderClass} shadow-xs rounded-3 p-3 position-relative ${isLatest ? 'bg-white shadow-sm' : 'bg-light bg-opacity-75'}">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <div class="d-flex align-items-center gap-1.5 flex-wrap">
                            <span class="badge ${isLatest ? 'bg-primary' : 'bg-secondary'} rounded-pill fw-bold" style="font-size: 11px;">v${sub.version}</span>
                            <span class="badge bg-primary-subtle text-primary rounded-pill small">${typeLabel}</span>
                            ${isLatest ? '<span class="badge bg-success-subtle text-success border border-success-subtle rounded-pill px-2 py-0.5 fw-bold" style="font-size: 10px;"><i class="fa-solid fa-star me-1"></i>Hiện tại</span>' : ''}
                            ${sub.milestone_name ? `<span class="badge bg-info-subtle text-info-emphasis rounded-pill small">${sub.milestone_name}</span>` : ''}
                        </div>
                        <div>${statusBadge}</div>
                    </div>

                    <div class="d-flex align-items-center justify-content-between p-2 rounded-2 bg-light border mb-2">
                        <div class="d-flex align-items-center gap-2 overflow-hidden me-2">
                            <i class="fa-solid fa-file-pdf text-danger fs-5 flex-shrink-0"></i>
                            <span class="small fw-bold text-dark text-truncate" title="${sub.file_name}">${sub.file_name}</span>
                        </div>
                        <a href="/api/submissions/download/${sub.id}" class="btn btn-sm btn-outline-primary rounded-pill px-3 py-1 flex-shrink-0 fw-bold" style="font-size: 11px;">
                            <i class="fa-solid fa-download me-1"></i> Tải về
                        </a>
                    </div>

                    ${sub.external_link ? `
                    <div class="mb-2">
                        <a href="${sub.external_link}" target="_blank" class="small text-decoration-none fw-bold text-primary text-truncate d-inline-block" style="max-width: 100%;">
                            <i class="fa-solid fa-arrow-up-right-from-square me-1"></i> ${sub.external_link}
                        </a>
                    </div>` : ''}

                    ${sub.notes ? `
                    <div class="small text-muted mb-2 bg-white p-2.5 rounded-3 border border-dashed" style="font-size: 12px;">
                        <div class="d-flex align-items-center gap-1.5 fw-bold text-dark mb-1 pb-1 border-bottom" style="font-size: 11px;">
                            <i class="fa-solid fa-file-word text-primary"></i> Ghi chú & tóm tắt từ nhóm:
                        </div>
                        <div class="ql-editor p-0 rich-content-display" style="min-height: auto; font-size: 12px; line-height: 1.5; color: #334155;">
                            ${sub.notes}
                        </div>
                    </div>` : ''}

                    <div class="d-flex justify-content-between align-items-center text-muted mb-1" style="font-size: 11px;">
                        <span><i class="fa-regular fa-user me-1"></i> Nộp bởi: ${sub.uploader_name || 'Sinh viên'}</span>
                        <span><i class="fa-regular fa-clock me-1"></i> ${sub.submitted_at}</span>
                    </div>

                    <!-- Mentor feedback box -->
                    ${sub.feedback ? `
                    <div class="mt-2 pt-2 border-top">
                        <div class="d-flex align-items-center justify-content-between mb-1">
                            <div class="small fw-bold text-primary d-flex align-items-center gap-1">
                                <i class="fa-solid fa-comment-dots text-primary"></i>
                                Nhận xét của Giảng viên hướng dẫn:
                            </div>
                            ${sub.feedback_at ? `<small class="text-muted" style="font-size: 10px;">${sub.feedback_at}</small>` : ''}
                        </div>
                        <div class="p-2 rounded-2 ${sub.status === 'revision_required' ? 'bg-danger-subtle text-danger-emphasis border border-danger-subtle' : 'bg-warning-subtle text-dark border border-warning-subtle'} small" style="white-space: pre-wrap; font-size: 11.5px; line-height: 1.4;">
                            ${sub.feedback}
                        </div>
                        ${sub.status === 'revision_required' && isLatest ? `
                        <div class="alert alert-warning py-1.5 px-2 mt-1.5 mb-0 small border-0 d-flex align-items-center gap-2" style="font-size: 11px;">
                            <i class="fa-solid fa-circle-exclamation flex-shrink-0"></i>
                            <span>Giảng viên yêu cầu sửa đổi. Nhóm vui lòng chỉnh sửa và gửi lại phiên bản <strong>v${sub.version + 1}</strong> ở form bên cạnh.</span>
                        </div>` : ''}
                    </div>` : ''}

                    <!-- Faculty approval & directive box -->
                    ${sub.faculty_status === 'approved' ? `
                    <div class="mt-2 pt-2 border-top">
                        <div class="d-flex align-items-center justify-content-between mb-1">
                            <div class="small fw-bold text-success d-flex align-items-center gap-1">
                                <i class="fa-solid fa-stamp text-success"></i>
                                Quyết định phê duyệt của Cấp Khoa:
                            </div>
                            ${sub.faculty_reviewed_at ? `<small class="text-muted" style="font-size: 10px;">${sub.faculty_reviewed_at}</small>` : ''}
                        </div>
                        <div class="p-2 rounded-2 bg-success-subtle text-success-emphasis border border-success-subtle small" style="white-space: pre-wrap; font-size: 11.5px; line-height: 1.4;">
                            ${cleanFeedback}
                        </div>
                    </div>` : (sub.faculty_status === 'revision_required' ? `
                    <div class="mt-2 pt-2 border-top">
                        <div class="d-flex align-items-center justify-content-between mb-1">
                            <div class="small fw-bold text-danger d-flex align-items-center gap-1">
                                <i class="fa-solid fa-triangle-exclamation text-danger"></i>
                                Ý kiến chỉ đạo từ Cấp Khoa:
                            </div>
                            ${sub.faculty_reviewed_at ? `<small class="text-muted" style="font-size: 10px;">${sub.faculty_reviewed_at}</small>` : ''}
                        </div>
                        <div class="p-2 rounded-2 bg-danger-subtle text-danger-emphasis border border-danger-subtle small" style="white-space: pre-wrap; font-size: 11.5px; line-height: 1.4;">
                            ${cleanFeedback || 'Khoa yêu cầu nhóm chỉnh sửa và bổ sung thêm nội dung báo cáo.'}
                        </div>
                    </div>` : '')}
                </div>
            `;
        }

        const latestSub = items[0];
        const olderSubs = items.slice(1);
        window._olderSubsCount = olderSubs.length;

        let html = '<div class="d-flex flex-column gap-2.5">';

        // 1. Latest Submission Card (Prominently displayed)
        html += `
            <div>
                <div class="d-flex align-items-center justify-content-between mb-1.5">
                    <span class="small fw-bold text-dark" style="font-size: 12px;">
                        <i class="fa-solid fa-flag-checkered text-primary me-1"></i> BẢN NỘP HIỆN TẠI (v${latestSub.version}):
                    </span>
                    <span class="badge bg-light text-muted border rounded-pill small">Tổng: ${items.length} phiên bản</span>
                </div>
                ${renderSubmissionCard(latestSub, true)}
            </div>
        `;

        // 2. Older Submissions if any (Collapsible with prominent Xem thêm button)
        if (olderSubs.length > 0) {
            const olderCards = olderSubs.map(s => renderSubmissionCard(s, false)).join('');
            html += `
                <div class="pt-1">
                    <button type="button" class="btn btn-outline-primary btn-sm w-100 rounded-pill py-2 fw-bold shadow-xs transition-all d-flex align-items-center justify-content-center gap-2" 
                            id="btn-toggle-older-subs" onclick="toggleOlderSubmissions()" style="background-color: #f8faff; border-style: dashed;">
                        <i class="fa-solid fa-clock-rotate-left text-primary"></i>
                        <span id="btn-toggle-older-text">Xem thêm lịch sử (${olderSubs.length} phiên bản cũ hơn)</span>
                        <i class="fa-solid fa-chevron-down" id="btn-toggle-older-icon"></i>
                    </button>
                </div>

                <div id="older-submissions-container" class="d-none d-flex flex-column gap-2.5 pt-2">
                    <div class="small fw-bold text-muted border-bottom pb-1 d-flex align-items-center justify-content-between">
                        <span><i class="fa-solid fa-history me-1 text-primary"></i> Các phiên bản đã nộp trước đây:</span>
                        <span class="badge bg-secondary-subtle text-secondary rounded-pill">${olderSubs.length} bản cũ</span>
                    </div>
                    ${olderCards}
                </div>
            `;
        }

        html += '</div>';
        listEl.innerHTML = html;

    } catch (err) {
        console.error('Error fetching submissions history:', err);
        listEl.innerHTML = '<div class="text-center text-muted py-4 small">Lỗi kết nối khi tải lịch sử bài nộp.</div>';
    }
}

function initSubmissionsUI() {
    const dropzone = document.getElementById('submission-dropzone');
    const fileInput = document.getElementById('submission-file-input');

    if (dropzone && fileInput && !dropzone.dataset.bound) {
        dropzone.dataset.bound = 'true';

        // Ngăn browser mở file trực tiếp khi kéo thả ra ngoài dropzone
        ['dragover', 'drop'].forEach(evt => {
            window.addEventListener(evt, (e) => {
                if (!e.target.closest('#submission-dropzone')) {
                    e.preventDefault();
                }
            }, false);
        });

        // Click to open file dialog (trừ khi click vào nút Xóa file)
        dropzone.addEventListener('click', (e) => {
            if (e.target.closest('.btn-outline-danger') || e.target.closest('[onclick*="clearSubmissionFile"]')) {
                return;
            }
            fileInput.click();
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files.length > 0) {
                handleFileSelect(e.target.files[0]);
            }
        });

        let dragCounter = 0;

        dropzone.addEventListener('dragenter', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dragCounter++;
            dropzone.classList.add('border-primary', 'bg-primary-subtle', 'bg-opacity-10');
            dropzone.style.borderColor = '#4f46e5';
            dropzone.style.backgroundColor = '#eef2ff';
        });

        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (e.dataTransfer) {
                e.dataTransfer.dropEffect = 'copy';
            }
            dropzone.classList.add('border-primary', 'bg-primary-subtle', 'bg-opacity-10');
            dropzone.style.borderColor = '#4f46e5';
            dropzone.style.backgroundColor = '#eef2ff';
        });

        dropzone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dragCounter--;
            if (dragCounter <= 0) {
                dragCounter = 0;
                dropzone.classList.remove('border-primary', 'bg-primary-subtle', 'bg-opacity-10');
                dropzone.style.borderColor = '#cbd5e1';
                dropzone.style.backgroundColor = '#f8fafc';
            }
        });

        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dragCounter = 0;
            dropzone.classList.remove('border-primary', 'bg-primary-subtle', 'bg-opacity-10');
            dropzone.style.borderColor = '#cbd5e1';
            dropzone.style.backgroundColor = '#f8fafc';

            if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                const file = e.dataTransfer.files[0];
                handleFileSelect(file);
            }
        });
    }

    // Chỉ kích hoạt loại mặc định nếu chưa có loại nào được chọn
    if (!document.querySelector('.submission-type-pill.active, [data-type].active')) {
        selectSubmissionType(currentSubmissionType || 'outline');
    }
}

window.loadSubmissionsData = function() {
    initSubmissionsUI();
    const topicIdInput = document.getElementById('submission-topic-id');
    if (topicIdInput && topicIdInput.value) {
        renderSubmissionHistory(parseInt(topicIdInput.value), currentSubmissionType);
    }
};

// Tự động khởi tạo ngay khi trang load nếu dropzone có trong DOM
document.addEventListener('DOMContentLoaded', () => {
    initSubmissionsUI();
    const hash = window.location.hash.substring(1);
    if (hash === 's-submit') {
        const topicIdInput = document.getElementById('submission-topic-id');
        if (topicIdInput && topicIdInput.value) {
            renderSubmissionHistory(parseInt(topicIdInput.value), currentSubmissionType);
        }
    }
});

window.toggleOlderSubmissions = function() {
    const container = document.getElementById('older-submissions-container');
    const textEl = document.getElementById('btn-toggle-older-text');
    const iconEl = document.getElementById('btn-toggle-older-icon');
    if (!container) return;

    const isHidden = container.classList.contains('d-none');
    if (isHidden) {
        container.classList.remove('d-none');
        if (textEl) textEl.textContent = 'Thu gọn lịch sử các phiên bản cũ';
        if (iconEl) {
            iconEl.classList.remove('fa-chevron-down');
            iconEl.classList.add('fa-chevron-up');
        }
    } else {
        container.classList.add('d-none');
        const count = window._olderSubsCount || 1;
        if (textEl) textEl.textContent = `Xem thêm lịch sử (${count} phiên bản cũ hơn)`;
        if (iconEl) {
            iconEl.classList.remove('fa-chevron-up');
            iconEl.classList.add('fa-chevron-down');
        }
    }
};

window.selectSubmissionType = selectSubmissionType;
window.clearSubmissionFile = clearSubmissionFile;
window.submitCurrentReport = submitCurrentReport;
window.renderSubmissionHistory = renderSubmissionHistory;
window.handleFileSelect = handleFileSelect;
