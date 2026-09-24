// static/assets/js/app.js
// ============================================================
// HOU S-RIMS - Application Logic (No hardcoded data)
// ============================================================

// ===================== APPROVE TOPIC (Giảng viên) =====================
let _approveTopicId = null;
let _rejectTopicId = null;

function openApproveModal(topicId, topicName) {
    _approveTopicId = topicId;
    const nameEl = document.getElementById('approveTopicId');
    const labelEl = document.getElementById('approveTopicName');
    if (nameEl) nameEl.value = topicId;
    if (labelEl) labelEl.textContent = '"' + topicName + '"';
    const modal = new bootstrap.Modal(document.getElementById('modalConfirmGuide'));
    modal.show();
}

function openRejectModal(topicId) {
    _rejectTopicId = topicId;
    const input = document.getElementById('rejectTopicId');
    if (input) input.value = topicId;
    const modal = new bootstrap.Modal(document.getElementById('modalRejectGuide'));
    modal.show();
}

function showTopicDetail(name, desc) {
    Swal.fire({
        title: name,
        text: desc || 'Không có mô tả.',
        icon: 'info',
        confirmButtonColor: '#6366f1',
        confirmButtonText: 'Đóng'
    });
}

async function doApprove() {
    const topicId = _approveTopicId || document.getElementById('approveTopicId')?.value;
    if (!topicId) { Swal.fire('Lỗi', 'Không tìm thấy đề tài.', 'error'); return; }

    // Close modal
    bootstrap.Modal.getInstance(document.getElementById('modalConfirmGuide'))?.hide();

    try {
        const resp = await fetch(`/api/topics/${topicId}/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'faculty_pending' })
        });
        const data = await resp.json();
        if (resp.ok) {
            await Swal.fire({
                icon: 'success',
                title: 'Đã duyệt!',
                text: 'Đề tài đã được chấp nhận hướng dẫn.',
                timer: 1800,
                showConfirmButton: false
            });
            location.reload();
        } else {
            Swal.fire('Lỗi', data.error || 'Không thể duyệt.', 'error');
        }
    } catch (e) {
        Swal.fire('Lỗi kết nối', e.message, 'error');
    }
}

async function doReject() {
    const topicId = _rejectTopicId || document.getElementById('rejectTopicId')?.value;
    const reason = document.getElementById('rejectNote')?.value?.trim();
    if (!topicId) { Swal.fire('Lỗi', 'Không tìm thấy đề tài.', 'error'); return; }
    if (!reason) { Swal.fire('Thiếu thông tin', 'Vui lòng nhập lý do từ chối.', 'warning'); return; }

    bootstrap.Modal.getInstance(document.getElementById('modalRejectGuide'))?.hide();

    try {
        const resp = await fetch(`/api/topics/${topicId}/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'rejected' })
        });
        const data = await resp.json();
        if (resp.ok) {
            await Swal.fire({
                icon: 'info',
                title: 'Đã từ chối',
                text: 'Đã gửi phản hồi từ chối đến sinh viên.',
                timer: 1800,
                showConfirmButton: false
            });
            location.reload();
        } else {
            Swal.fire('Lỗi', data.error || 'Không thể từ chối.', 'error');
        }
    } catch (e) {
        Swal.fire('Lỗi kết nối', e.message, 'error');
    }
}

async function facultyApprove(topicId) {
    try {
        const resp = await fetch(`/api/topics/${topicId}/faculty-approve`, {
            method: 'POST'
        });
        const data = await resp.json();
        if (resp.ok) {
            await Swal.fire({
                icon: 'success',
                title: 'Duyệt thành công',
                text: 'Đề tài đã được Khoa phê duyệt.',
                timer: 1800,
                showConfirmButton: false
            });
            location.reload();
        } else {
            Swal.fire('Lỗi', data.error || 'Không thể phê duyệt.', 'error');
        }
    } catch (e) {
        Swal.fire('Lỗi kết nối', e.message, 'error');
    }
}

// ===================== ĐĂNG KÝ ĐỀ TÀI (Sinh viên) =====================
document.addEventListener('DOMContentLoaded', function () {
    const btnSubmit = document.getElementById('btnSubmitRegister');
    if (btnSubmit) {
        btnSubmit.addEventListener('click', async function (e) {
            e.stopPropagation();
            const name = document.getElementById('topicName')?.value?.trim();
            const desc = document.getElementById('topicDesc')?.value?.trim();
            const batchId = document.getElementById('batchId')?.value;
            const mentorId = document.getElementById('mentor_id')?.value || document.getElementById('mentorId')?.value;
            const groupId = document.getElementById('groupId')?.value;

            if (!name || !batchId || !mentorId) {
                Swal.fire('Thiếu thông tin', 'Vui lòng điền đầy đủ tên đề tài, đợt và giảng viên.', 'warning');
                return;
            }
            
            const batchSelect = document.getElementById('batchId');
            const selectedOption = batchSelect.options[batchSelect.selectedIndex];
            if (selectedOption && selectedOption.getAttribute('data-expired') === 'true') {
                Swal.fire('Đã hết hạn', 'Đợt đăng ký này đã hết hạn. Bạn không thể đăng ký đề tài.', 'error');
                return;
            }

            
            // Nếu chưa có group, truyền 0 để server tự tạo
            const finalGroupId = groupId ? parseInt(groupId) : 0;

            try {
                const resp = await fetch('/api/topics/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, description: desc, batch_id: parseInt(batchId), mentor_id: parseInt(mentorId), group_id: finalGroupId })
                });
                const data = await resp.json();
                if (resp.ok || resp.status === 201) {
                    // Close modal if open
                    const modal = bootstrap.Modal.getInstance(document.getElementById('modalRegisterTopic'));
                    if (modal) modal.hide();
                    await Swal.fire({
                        icon: 'success', title: 'Đăng ký thành công!',
                        text: 'Đề tài đã được gửi và đang chờ giảng viên duyệt.',
                        timer: 2000, showConfirmButton: false
                    });
                    location.reload();
                } else {
                    Swal.fire('Lỗi', data.error || 'Đăng ký thất bại.', 'error');
                }
            } catch (ex) {
                Swal.fire('Lỗi kết nối', ex.message, 'error');
            }
        });
    }
    
    // Check batch expiration on page load
    const batchSelect = document.getElementById('batchId');
    if (batchSelect) {
        checkBatchExpiration(batchSelect);
    }

    // ===================== NỘP FILE (Sinh viên) =====================
    const btnUpload = document.getElementById('btnUploadSubmission');
    if (btnUpload) {
        btnUpload.addEventListener('click', async function (e) {
            e.stopPropagation();
            const fileInput = document.getElementById('submissionFile');
            const topicId = document.getElementById('submissionTopicId')?.value;
            const uploaderId = document.getElementById('submissionUploaderId')?.value;
            const type = document.getElementById('submissionType')?.value;

            if (!fileInput?.files?.length) { Swal.fire('Chưa chọn file', 'Vui lòng chọn file trước khi nộp.', 'warning'); return; }
            if (!topicId) { Swal.fire('Thiếu thông tin', 'Không xác định được đề tài.', 'warning'); return; }

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('topic_id', topicId);
            formData.append('uploader_id', uploaderId);
            formData.append('type', type || 'report');

            try {
                const resp = await fetch('/api/submissions/upload', { method: 'POST', body: formData });
                const data = await resp.json();
                if (resp.ok || resp.status === 201) {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('modalConfirmSubmit'));
                    if (modal) modal.hide();
                    await Swal.fire({ icon: 'success', title: 'Nộp thành công!', timer: 1800, showConfirmButton: false });
                    location.reload();
                } else {
                    Swal.fire('Lỗi', data.error || 'Nộp file thất bại.', 'error');
                }
            } catch (ex) {
                Swal.fire('Lỗi kết nối', ex.message, 'error');
            }
        });
    }

    // ===================== TẠO ĐỢT NCKH (API) =====================
    const btnCreateBatch = document.getElementById('btnCreateBatch');
    if (btnCreateBatch) {
        btnCreateBatch.addEventListener('click', async function () {
            const name = document.getElementById('batchName')?.value?.trim();
            const startDate = document.getElementById('batchStartDate')?.value;
            const endDate = document.getElementById('batchEndDate')?.value;
            if (!name || !startDate || !endDate) {
                Swal.fire('Thiếu thông tin', 'Vui lòng điền đủ tên đợt và ngày.', 'warning'); return;
            }
            try {
                const resp = await fetch('/api/batches', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, start_date: startDate, end_date: endDate, status: 'active' })
                });
                const data = await resp.json();
                if (resp.ok || resp.status === 201) {
                    await Swal.fire({ icon: 'success', title: 'Tạo đợt thành công!', timer: 1600, showConfirmButton: false });
                    location.reload();
                } else {
                    Swal.fire('Lỗi', data.error || 'Tạo đợt thất bại.', 'error');
                }
            } catch (ex) {
                Swal.fire('Lỗi kết nối', ex.message, 'error');
            }
        });
    }

    // ===================== TẠO NHÓM (API) =====================
    const btnCreateGroup = document.getElementById('btnCreateGroup');
    if (btnCreateGroup) {
        btnCreateGroup.addEventListener('click', async function () {
            const name = document.getElementById('groupName')?.value?.trim();
            const batchId = document.getElementById('groupBatchId')?.value;
            const leaderId = document.getElementById('groupLeaderId')?.value;
            if (!name || !batchId || !leaderId) {
                Swal.fire('Thiếu thông tin', 'Vui lòng điền đủ thông tin nhóm.', 'warning'); return;
            }
            try {
                const resp = await fetch('/api/groups', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, batch_id: parseInt(batchId), leader_id: parseInt(leaderId) })
                });
                const data = await resp.json();
                if (resp.ok || resp.status === 201) {
                    await Swal.fire({ icon: 'success', title: 'Tạo nhóm thành công!', timer: 1600, showConfirmButton: false });
                    location.reload();
                } else {
                    Swal.fire('Lỗi', data.error || 'Tạo nhóm thất bại.', 'error');
                }
            } catch (ex) {
                Swal.fire('Lỗi kết nối', ex.message, 'error');
            }
        });
    }
});

// ===================== SAVE BATCH (standalone, called by onclick) =====================
async function saveBatch() {
    const name = document.getElementById('batch-name')?.value?.trim();
    const startDate = document.getElementById('batch-start-date')?.value;
    const endDate = document.getElementById('batch-end-date')?.value;
    const type = document.getElementById('batch-type')?.value;
    const description = document.getElementById('batch-description')?.value;

    if (!name) {
        Swal.fire('Thiếu thông tin', 'Vui lòng nhập tên đợt triển khai.', 'warning');
        return;
    }

    // Close the modal
    const modalEl = document.getElementById('modalCreateBatch');
    if (modalEl) bootstrap.Modal.getInstance(modalEl)?.hide();

    try {
        const resp = await fetch('/api/batches', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name,
                type: type || 'NCKH Standard',
                start_date: startDate || null,
                end_date: endDate || null,
                submission_deadline: endDate || null,
                description: description || ''
            })
        });
        const data = await resp.json();
        if (resp.ok || resp.status === 201) {
            await Swal.fire({ icon: 'success', title: 'Đã tạo đợt mới!', text: `"${name}" đã được ban hành.`, timer: 2000, showConfirmButton: false });
            location.reload();
        } else {
            Swal.fire('Lỗi', data.error || 'Tạo đợt thất bại.', 'error');
        }
    } catch (ex) {
        Swal.fire('Lỗi kết nối', ex.message, 'error');
    }
}

// ===================== ĐẶT LỊCH HẸN =====================
document.addEventListener('DOMContentLoaded', function () {
    const btnSubmitMeeting = document.getElementById('btnSubmitMeeting');
    if (btnSubmitMeeting) {
        btnSubmitMeeting.addEventListener('click', async function() {
            const title = document.getElementById('meetingTitle')?.value?.trim();
            const desc = document.getElementById('meetingDesc')?.value?.trim();
            const time = document.getElementById('meetingTime')?.value;
            const topicId = document.getElementById('meetingTopicId')?.value;

            if (!title || !time) {
                Swal.fire('Thiếu thông tin', 'Vui lòng điền tiêu đề và thời gian.', 'warning');
                return;
            }

            try {
                const resp = await fetch('/api/calendar/events', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        title: title,
                        description: desc,
                        start_time: time,
                        topic_id: topicId ? parseInt(topicId) : null
                    })
                });
                const data = await resp.json();
                if (resp.ok || resp.status === 201) {
                    bootstrap.Modal.getInstance(document.getElementById('modalScheduleMeeting'))?.hide();
                    await Swal.fire({
                        icon: 'success', title: 'Đặt lịch thành công!',
                        text: 'Lịch họp đã được lưu vào hệ thống.',
                        timer: 2000, showConfirmButton: false
                    });
                    location.reload();
                } else {
                    Swal.fire('Lỗi', data.error || 'Đặt lịch thất bại.', 'error');
                }
            } catch (e) {
                Swal.fire('Lỗi kết nối', e.message, 'error');
            }
        });
    }
});

// ===================== NỘP FILE BÁO CÁO =====================
document.addEventListener('DOMContentLoaded', function () {
    const btnUpload = document.getElementById('btnUploadSubmission');
    if (btnUpload) {
        btnUpload.addEventListener('click', async function() {
            const fileInput = document.getElementById('submissionFile');
            const type = document.getElementById('submissionType')?.value;
            const topicId = document.getElementById('submissionTopicId')?.value;
            const uploaderId = document.getElementById('submissionUploaderId')?.value;

            if (!fileInput || !fileInput.files.length) {
                Swal.fire('Chưa chọn file', 'Vui lòng chọn file để nộp.', 'warning');
                return;
            }
            if (!topicId) {
                Swal.fire('Lỗi', 'Không tìm thấy đề tài. Hãy đăng ký đề tài trước.', 'error');
                return;
            }

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('topic_id', topicId);
            formData.append('uploader_id', uploaderId || '');
            formData.append('type', type || 'report');

            btnUpload.disabled = true;
            btnUpload.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Đang nộp...';

            try {
                const resp = await fetch('/api/submissions/upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await resp.json();
                if (resp.ok || resp.status === 201) {
                    bootstrap.Modal.getInstance(document.getElementById('modalConfirmSubmit'))?.hide();
                    await Swal.fire({
                        icon: 'success', title: 'Nộp thành công!',
                        text: 'File báo cáo đã được lưu vào hệ thống.',
                        timer: 2000, showConfirmButton: false
                    });
                    fileInput.value = '';
                } else {
                    Swal.fire('Lỗi', data.error || 'Nộp file thất bại.', 'error');
                }
            } catch (e) {
                Swal.fire('Lỗi kết nối', e.message, 'error');
            } finally {
                btnUpload.disabled = false;
                btnUpload.innerHTML = 'Nộp ngay';
            }
        });
    }
});

// ===================== LỊCH ĐỘNG (DYNAMIC CALENDAR) =====================
let currentCalDate = new Date();
const monthNames = ["Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4", "Tháng 5", "Tháng 6", "Tháng 7", "Tháng 8", "Tháng 9", "Tháng 10", "Tháng 11", "Tháng 12"];

document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('calendar-grid')) {
        renderCalendar();
        document.getElementById('prev-month-btn')?.addEventListener('click', () => {
            currentCalDate.setMonth(currentCalDate.getMonth() - 1);
            renderCalendar();
        });
        document.getElementById('next-month-btn')?.addEventListener('click', () => {
            currentCalDate.setMonth(currentCalDate.getMonth() + 1);
            renderCalendar();
        });
    }
});

async function renderCalendar() {
    const grid = document.getElementById('calendar-grid');
    const monthYearText = document.getElementById('calendar-month-year');
    if (!grid || !monthYearText) return;

    monthYearText.textContent = `${monthNames[currentCalDate.getMonth()]}, ${currentCalDate.getFullYear()}`;

    // Get first day of month
    const firstDayIndex = new Date(currentCalDate.getFullYear(), currentCalDate.getMonth(), 1).getDay();
    // Get total days in month
    const lastDay = new Date(currentCalDate.getFullYear(), currentCalDate.getMonth() + 1, 0).getDate();
    // Get prev month last days
    const prevLastDay = new Date(currentCalDate.getFullYear(), currentCalDate.getMonth(), 0).getDate();

    // Setup HTML string
    let html = '';
    
    // Fetch events from API
    let events = [];
    try {
        const resp = await fetch('/api/calendar/events');
        if (resp.ok) events = await resp.json();
    } catch (e) { console.error('Error fetching events:', e); }

    // Map events by date (DD)
    const eventMap = {};
    events.forEach(ev => {
        if (!ev.start_time) return;
        const d = new Date(ev.start_time);
        if (d.getMonth() === currentCalDate.getMonth() && d.getFullYear() === currentCalDate.getFullYear()) {
            const day = d.getDate();
            if (!eventMap[day]) eventMap[day] = [];
            eventMap[day].push(ev);
        }
    });

    let dayCount = 1;
    let nextDayCount = 1;

    for (let row = 0; row < 6; row++) {
        html += '<tr>';
        for (let col = 0; col < 7; col++) {
            if (row === 0 && col < firstDayIndex) {
                // Prev month days
                html += `<td class="opacity-25">${prevLastDay - firstDayIndex + col + 1}</td>`;
            } else if (dayCount > lastDay) {
                // Next month days
                html += `<td class="opacity-25">${nextDayCount++}</td>`;
            } else {
                // Current month days
                const todayClass = (dayCount === new Date().getDate() && currentCalDate.getMonth() === new Date().getMonth() && currentCalDate.getFullYear() === new Date().getFullYear()) ? 'calendar-today bg-light' : '';
                
                let dayEventsHtml = '';
                if (eventMap[dayCount]) {
                    eventMap[dayCount].forEach(e => {
                        dayEventsHtml += `<div class="event-chip bg-primary text-white mt-1 p-1 rounded small text-truncate" style="font-size:10px;" title="${e.title}">${e.title}</div>`;
                    });
                }
                
                html += `<td class="${todayClass} position-relative align-top" style="height:80px;">
                            <div class="d-flex justify-content-between"><span class="fw-bold">${dayCount}</span></div>
                            ${dayEventsHtml}
                         </td>`;
                dayCount++;
            }
        }
        html += '</tr>';
        if (dayCount > lastDay && row >= 4) break;
    }
    grid.innerHTML = html;
}

// ===================== UPDATE TOPIC (Faculty) =====================
function openEditTopicModal(id, title, desc, mentorId, batchId, status) {
    document.getElementById('editTopicId').value = id;
    document.getElementById('editTopicTitle').value = title;
    document.getElementById('editTopicDesc').value = desc;
    if (mentorId) {
        document.getElementById('editTopicMentor').value = mentorId;
    } else {
        document.getElementById('editTopicMentor').value = '';
    }
    if (batchId) {
        document.getElementById('editTopicBatch').value = batchId;
    } else {
        document.getElementById('editTopicBatch').value = '';
    }
    if (status) {
        document.getElementById('editTopicStatus').value = status;
    }
    
    const modal = new bootstrap.Modal(document.getElementById('modalEditTopic'));
    modal.show();
}

async function submitEditTopic() {
    const id = document.getElementById('editTopicId').value;
    const title = document.getElementById('editTopicTitle').value;
    const desc = document.getElementById('editTopicDesc').value;
    const mentorId = document.getElementById('editTopicMentor').value;
    const batchId = document.getElementById('editTopicBatch').value;
    const status = document.getElementById('editTopicStatus').value;

    try {
        const resp = await fetch(`/api/topics/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: title,
                description: desc,
                mentor_id: mentorId || null,
                batch_id: batchId || null,
                status: status || null
            })
        });
        const data = await resp.json();
        if (resp.ok) {
            await Swal.fire({
                icon: 'success',
                title: 'Thành công',
                text: 'Cập nhật đề tài thành công!',
                timer: 1500,
                showConfirmButton: false
            });
            location.reload();
        } else {
            Swal.fire('Lỗi', data.error || 'Cập nhật thất bại.', 'error');
        }
    } catch (e) {
        Swal.fire('Lỗi kết nối', e.message, 'error');
    }
}

function checkBatchExpiration(selectElement) {
    const btnSubmit = document.getElementById('btnSubmitRegister');
    if (!selectElement || !btnSubmit) return;
    
    const selectedOption = selectElement.options[selectElement.selectedIndex];
    if (selectedOption && selectedOption.getAttribute('data-expired') === 'true') {
        btnSubmit.disabled = true;
        btnSubmit.classList.add('opacity-50');
        btnSubmit.innerHTML = 'ĐỢT ĐĂNG KÝ ĐÃ KHÓA';
    } else {
        btnSubmit.disabled = false;
        btnSubmit.classList.remove('opacity-50');
        btnSubmit.innerHTML = 'GỬI HỒ SƠ ĐĂNG KÝ PHÊ DUYỆT';
    }
}

// ===================== PORTFOLIO (Hồ sơ năng lực) =====================
async function submitAddSkill() {
    const name = document.getElementById('skillName')?.value?.trim();
    if (!name) return Swal.fire('Lỗi', 'Vui lòng nhập tên kỹ năng.', 'warning');
    try {
        const res = await fetch('/api/profile/skills', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name})
        });
        if (res.ok) location.reload();
        else Swal.fire('Lỗi', 'Thêm thất bại.', 'error');
    } catch (e) { console.error(e); }
}

async function submitAddAchievement() {
    const name = document.getElementById('achName')?.value?.trim();
    const year = document.getElementById('achYear')?.value?.trim();
    const desc = document.getElementById('achDesc')?.value?.trim();
    if (!name) return Swal.fire('Lỗi', 'Vui lòng nhập tên giải thưởng.', 'warning');
    try {
        const res = await fetch('/api/profile/achievements', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name, year, description: desc})
        });
        if (res.ok) location.reload();
        else Swal.fire('Lỗi', 'Thêm thất bại.', 'error');
    } catch (e) { console.error(e); }
}

async function submitAddExperience() {
    const project_name = document.getElementById('expName')?.value?.trim();
    const role = document.getElementById('expRole')?.value?.trim();
    const duration = document.getElementById('expDuration')?.value?.trim();
    const desc = document.getElementById('expDesc')?.value?.trim();
    if (!project_name) return Swal.fire('Lỗi', 'Vui lòng nhập tên dự án.', 'warning');
    try {
        const res = await fetch('/api/profile/experiences', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({project_name, role, duration, description: desc})
        });
        if (res.ok) location.reload();
        else Swal.fire('Lỗi', 'Thêm thất bại.', 'error');
    } catch (e) { console.error(e); }
}

async function deletePortfolioItem(type, id) {
    if (!confirm('Bạn có chắc chắn muốn xóa mục này?')) return;
    try {
        const res = await fetch(`/api/profile/${type}/${id}`, {
            method: 'DELETE'
        });
        if (res.ok) location.reload();
        else Swal.fire('Lỗi', 'Xóa thất bại.', 'error');
    } catch (e) { console.error(e); }
}

async function viewPublicProfile(userId) {
    const modal = new bootstrap.Modal(document.getElementById('modalPublicProfile'));
    modal.show();
    
    const content = document.getElementById('publicProfileContent');
    content.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status"></div>
            <div class="mt-2 text-muted">Đang tải hồ sơ...</div>
        </div>
    `;
    
    try {
        const res = await fetch(`/api/profile/${userId}`);
        if (!res.ok) throw new Error('Không thể tải hồ sơ');
        const data = await res.json();
        
        let skillsHtml = data.skills?.length ? data.skills.map(s => `<span class="badge bg-primary-subtle text-primary px-3 py-2 rounded-pill">${s.name}</span>`).join(' ') : '<span class="text-muted small">Chưa có kỹ năng</span>';
        let achHtml = data.achievements?.length ? data.achievements.map(a => `
            <div class="p-2 border rounded-3 mb-2">
                <div class="fw-bold small">${a.name}</div>
                <div class="text-muted" style="font-size: 11px;">${a.year || ''} - ${a.description || ''}</div>
            </div>
        `).join('') : '<span class="text-muted small">Chưa có giải thưởng</span>';
        let expHtml = data.experiences?.length ? data.experiences.map(e => `
            <div class="p-2 border rounded-3 mb-2">
                <div class="fw-bold small">${e.project_name}</div>
                <div class="text-muted" style="font-size: 11px;">Vai trò: ${e.role || ''} | ${e.duration || ''}</div>
                <div class="text-muted mt-1" style="font-size: 11px;">${e.description || ''}</div>
            </div>
        `).join('') : '<span class="text-muted small">Chưa có kinh nghiệm dự án</span>';

        content.innerHTML = `
            <div class="text-center mb-4">
                <div class="bg-primary text-white rounded-circle d-flex align-items-center justify-content-center mx-auto shadow mb-3" style="width: 80px; height: 80px; font-size: 32px; background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);">
                    ${data.full_name ? data.full_name.substring(0, 2).toUpperCase() : 'US'}
                </div>
                <h4 class="fw-bold mb-1">${data.full_name || 'N/A'}</h4>
                <div class="text-muted small mb-2">${data.role === 'Student' ? 'Sinh viên' : 'Giảng viên'} ${data.student_id ? '• ' + data.student_id : ''}</div>
                <div class="text-muted small">${data.email || ''}</div>
                ${data.bio ? `<div class="mt-3 fst-italic small">"${data.bio}"</div>` : ''}
            </div>
            
            <div class="row g-4">
                <div class="col-md-6">
                    <h6 class="fw-bold text-primary mb-3"><i class="fa-solid fa-wand-magic-sparkles me-2"></i> Kỹ năng</h6>
                    <div class="d-flex flex-wrap gap-2 mb-4">${skillsHtml}</div>
                    
                    <h6 class="fw-bold text-warning mb-3"><i class="fa-solid fa-medal me-2"></i> Chứng nhận & Giải thưởng</h6>
                    <div>${achHtml}</div>
                </div>
                <div class="col-md-6">
                    <h6 class="fw-bold text-success mb-3"><i class="fa-solid fa-briefcase me-2"></i> Kinh nghiệm dự án</h6>
                    <div>${expHtml}</div>
                </div>
            </div>
        `;
    } catch (e) {
        content.innerHTML = `<div class="text-center text-danger py-4"><i class="fa-solid fa-triangle-exclamation mb-2 fs-2"></i><br>${e.message}</div>`;
    }
}

// ===================== LECTURER PROGRESS TRACKING =====================
function openAddMilestoneModal(topicId) {
    document.getElementById('milestoneTopicId').value = topicId;
    document.getElementById('milestoneName').value = '';
    document.getElementById('milestoneDeadline').value = '';
    new bootstrap.Modal(document.getElementById('modalAddMilestone')).show();
}

async function submitAddMilestone() {
    const topicId = document.getElementById('milestoneTopicId').value;
    const name = document.getElementById('milestoneName').value.trim();
    const deadline = document.getElementById('milestoneDeadline').value;
    if (!name || !deadline) return Swal.fire('Lỗi', 'Vui lòng điền đủ thông tin', 'warning');
    
    try {
        const res = await fetch(`/api/topics/${topicId}/milestones`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name, deadline})
        });
        if (res.ok) {
            Swal.fire('Thành công', 'Đã thêm cột mốc!', 'success').then(() => location.reload());
        } else {
            Swal.fire('Lỗi', 'Thêm thất bại', 'error');
        }
    } catch (e) { console.error(e); }
}

function updateMilestoneProgress(milestoneId, currentPct, name) {
    document.getElementById('updateMilestoneId').value = milestoneId;
    document.getElementById('updateMilestoneNameLabel').innerText = name;
    document.getElementById('updateMilestonePct').value = currentPct;
    document.getElementById('pctDisplay').innerText = currentPct + '%';
    new bootstrap.Modal(document.getElementById('modalUpdateProgress')).show();
}

async function submitUpdateProgress() {
    const milestoneId = document.getElementById('updateMilestoneId').value;
    const pct = document.getElementById('updateMilestonePct').value;
    
    try {
        const res = await fetch(`/api/topics/0/progress`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({milestone_id: parseInt(milestoneId), percentage: parseInt(pct)})
        });
        if (res.ok) {
            Swal.fire('Thành công', 'Đã cập nhật tiến độ!', 'success').then(() => location.reload());
        } else {
            Swal.fire('Lỗi', 'Cập nhật thất bại', 'error');
        }
    } catch (e) { console.error(e); }
}
