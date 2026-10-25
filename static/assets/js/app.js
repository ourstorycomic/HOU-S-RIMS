// static/assets/js/app.js
// ============================================================
// HOU S-RIMS - Application Logic (No hardcoded data)
// ============================================================

// Real-time synchronization state
window._seenNotifIds = new Set();
window._notifInitDone = false;
window._liveSyncTimer = null;

// Group invitation handler (instant DOM update + real-time sync, NO page reload!)
async function handleGroupInvitation(groupId, action) {
    const isAcc = action === 'accepted';
    
    // 1. Optimistic UI update: immediately change button to status badge in dropdown
    const itemEl = document.querySelector(`[data-inv-group-id="${groupId}"]`) || 
                   document.querySelector(`button[onclick*="handleGroupInvitation(${groupId}"]`)?.closest('li, .dropdown-item');
    if (itemEl) {
        const actionsDiv = itemEl.querySelector('.d-flex.gap-2:has(button)') || itemEl.querySelector('.d-flex.gap-2');
        if (actionsDiv) {
            actionsDiv.outerHTML = isAcc ? 
                `<div class="text-success small fw-semibold mt-1" style="font-size: 11px;"><i class="fa-solid fa-circle-check me-1"></i> Đã chấp nhận lời mời tham gia nhóm.</div>` :
                `<div class="text-muted small fst-italic mt-1" style="font-size: 11px;"><i class="fa-solid fa-ban me-1"></i> Đã từ chối lời mời này.</div>`;
        }
        const badgeEl = itemEl.querySelector('.badge');
        if (badgeEl) {
            badgeEl.className = isAcc ? 'badge bg-success-subtle text-success border border-success-subtle rounded-pill' : 'badge bg-secondary-subtle text-secondary rounded-pill';
            badgeEl.innerHTML = isAcc ? '<i class="fa-solid fa-check me-1"></i>Đã chấp nhận' : 'Đã từ chối';
        }
        itemEl.classList.remove('bg-warning-subtle');
        itemEl.classList.add('bg-white');
    }

    // Hide any pending dashboard banner smoothly
    document.querySelectorAll('.alert.bg-warning').forEach(alertBox => {
        if (alertBox.textContent.includes('LỜI MỜI THAM GIA NHÓM')) {
            alertBox.style.transition = 'all 0.35s ease';
            alertBox.style.opacity = '0';
            setTimeout(() => alertBox.remove(), 350);
        }
    });

    try {
        const resp = await fetch('/api/topics/invitation', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({group_id: groupId, action: action})
        });
        const data = await resp.json().catch(() => ({}));
        if (resp.ok) {
            const msg = isAcc ? 'Đã tham gia nhóm nghiên cứu thành công!' : 'Đã từ chối lời mời tham gia nhóm.';
            if (typeof Swal !== 'undefined') {
                Swal.mixin({
                    toast: true,
                    position: 'top-end',
                    showConfirmButton: false,
                    timer: 3000,
                    timerProgressBar: true
                }).fire({
                    icon: isAcc ? 'success' : 'info',
                    title: msg
                });
            }
            // Trigger immediate sync across all badge counters and lists
            if (typeof syncNotificationsLive === 'function') {
                syncNotificationsLive(true);
            }
        } else {
            if (typeof Swal !== 'undefined') {
                Swal.fire('Thông báo', data.error || 'Có lỗi xảy ra', 'warning');
            }
        }
    } catch(e) {
        console.error("handleGroupInvitation error:", e);
    }
}

// ===================== DATE INPUT CONSTRAINTS =====================
document.addEventListener('DOMContentLoaded', () => {
    const today = new Date().toISOString().split('T')[0];
    
    const dateInputPairs = [
        { start: 'createBatchStart', end: 'createBatchEnd' },
        { start: 'batch-start-date', end: 'batch-end-date' },
        { start: 'batchStartDate', end: 'batchEndDate' }
    ];
    
    dateInputPairs.forEach(pair => {
        const startEl = document.getElementById(pair.start);
        const endEl = document.getElementById(pair.end);
        
        if (startEl) {
            startEl.min = today;
            startEl.addEventListener('change', function() {
                if (endEl) {
                    endEl.min = this.value || today;
                    if (endEl.value && endEl.value < this.value) {
                        endEl.value = this.value;
                    }
                }
            });
        }
        if (endEl) {
            endEl.min = today;
        }
    });
});

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

function showTopicDetail(name, desc, students) {
    Swal.fire({
        title: name,
        html: `<strong>Mô tả:</strong> ${desc || 'Không có mô tả chi tiết.'}<br><br><strong>Sinh viên thực hiện:</strong> ${students || 'Chưa rõ'}`,
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
                    body: JSON.stringify({ name, description: desc, batch_id: parseInt(batchId), mentor_id: parseInt(mentorId), group_id: finalGroupId, members: window.selectedMembersForGroup || [] })
                });
                const data = await resp.json();
                if (resp.ok || resp.status === 201) {
                    // Close modal if open
                    const modalConfirm = (typeof bootstrap !== 'undefined') ? (
                        bootstrap.Modal.getInstance(document.getElementById('modalConfirmRegister')) ||
                        bootstrap.Modal.getInstance(document.getElementById('modalRegisterTopic'))
                    ) : null;
                    if (modalConfirm) modalConfirm.hide();

                    await Swal.fire({
                        icon: 'success', title: 'Đăng ký thành công!',
                        text: 'Đề tài đã được gửi và đang chờ giảng viên duyệt.',
                        timer: 2000, showConfirmButton: false
                    });

                    if (typeof checkAndLoadMyTopic === 'function') {
                        await checkAndLoadMyTopic();
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                    } else {
                        location.reload();
                    }
                } else {
                    Swal.fire('Lỗi', data.error || 'Đăng ký thất bại.', 'error');
                }
            } catch (ex) {
                Swal.fire('Lỗi kết nối', ex.message, 'error');
            }
        });
    }
    
    // Cancel topic registration if waiting for members
    window.cancelTopicRegistration = async function(topicId) {
        if (!confirm('Bạn có chắc chắn muốn hủy đăng ký đề tài này? Toàn bộ lời mời tham gia nhóm sẽ bị hủy.')) return;
        
        try {
            const resp = await fetch(`/api/topics/${topicId}`, {
                method: 'DELETE'
            });
            const data = await resp.json();
            if (resp.ok) {
                Swal.fire({icon: 'success', title: 'Đã hủy', text: 'Đã hủy đăng ký đề tài thành công.', timer: 2000, showConfirmButton: false});
                if (typeof renderTopicFormView === 'function') {
                    renderTopicFormView();
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                } else {
                    location.reload();
                }
            } else {
                Swal.fire('Lỗi', data.error || 'Không thể hủy đề tài.', 'error');
            }
        } catch (ex) {
            Swal.fire('Lỗi', ex.message, 'error');
        }
    };
    
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
                    sessionStorage.setItem('active_admin_tab', 'batches');
                    window.location.hash = '#batches';
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

    // ===================== SỬA / XÓA ĐỢT NCKH =====================
    document.querySelectorAll('.btn-delete-batch').forEach(btn => {
        btn.addEventListener('click', async function(e) {
            e.preventDefault();
            const id = this.getAttribute('data-id');
            const result = await Swal.fire({
                title: 'Xóa đợt này?',
                text: "Bạn không thể hoàn tác!",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Đồng ý xóa',
                cancelButtonText: 'Hủy'
            });
            if (result.isConfirmed) {
                try {
                    const res = await fetch(`/api/batches/${id}`, { method: 'DELETE' });
                    if (res.ok) {
                        sessionStorage.setItem('active_admin_tab', 'batches');
                        window.location.hash = '#batches';
                        Swal.fire('Đã xóa!', 'Đợt NCKH đã bị xóa.', 'success').then(() => location.reload());
                    } else {
                        const data = await res.json();
                        Swal.fire('Lỗi', data.error || 'Xóa thất bại', 'error');
                    }
                } catch(e) { Swal.fire('Lỗi', e.message, 'error'); }
            }
        });
    });

    document.querySelectorAll('.btn-edit-batch').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            document.getElementById('editBatchId').value = this.getAttribute('data-id');
            document.getElementById('editBatchName').value = this.getAttribute('data-name');
            document.getElementById('editBatchStart').value = this.getAttribute('data-start');
            document.getElementById('editBatchSubmitDeadline').value = this.getAttribute('data-deadline');
            document.getElementById('editBatchEnd').value = this.getAttribute('data-end');
            
            const year = this.getAttribute('data-year');
            if (year) document.getElementById('editBatchYear').value = year;
            
            const type = this.getAttribute('data-type');
            if (type) document.getElementById('editBatchType').value = type;
            
            const status = this.getAttribute('data-status');
            if (status) document.getElementById('editBatchStatus').value = status;
            
            const descValue = this.getAttribute('data-desc') || '';
            document.getElementById('editBatchDesc').value = descValue;
            if (window.quillEdit) {
                // Remove trailing whitespace but keep html
                window.quillEdit.root.innerHTML = descValue;
            }
            document.getElementById('editBatchDoc').value = '';
            
            const currentDoc = this.getAttribute('data-doc');
            const docLabel = document.getElementById('editBatchDocCurrent');
            if(docLabel) {
                docLabel.textContent = currentDoc ? `Tài liệu hiện tại: ${currentDoc}` : 'Chưa có tài liệu đính kèm.';
            }
        });
    });

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
    const year = document.getElementById('batch-year')?.value?.trim() || '2025-2026';
    const startDate = document.getElementById('batch-start-date')?.value;
    const endDate = document.getElementById('batch-end-date')?.value;
    const type = document.getElementById('batch-type')?.value;
    const description = document.getElementById('batch-description')?.value;
    const fileInput = document.getElementById('batch-file');

    if (!name) {
        Swal.fire('Thiếu thông tin', 'Vui lòng nhập tên đợt triển khai.', 'warning');
        return;
    }

    const formData = new FormData();
    formData.append('name', name);
    formData.append('academic_year', year);
    formData.append('type', type || 'NCKH Standard');
    if (startDate) formData.append('start_date', startDate);
    if (endDate) {
        formData.append('end_date', endDate);
        formData.append('submission_deadline', endDate);
    }
    if (description) formData.append('description', description);
    if (fileInput && fileInput.files && fileInput.files.length > 0) {
        formData.append('guidance_doc', fileInput.files[0]);
    }

    // Close the modal
    const modalEl = document.getElementById('modalCreateBatch');
    if (modalEl) bootstrap.Modal.getInstance(modalEl)?.hide();

    try {
        const resp = await fetch('/api/batches', {
            method: 'POST',
            body: formData
        });
        const data = await resp.json();
        if (resp.ok || resp.status === 201) {
            sessionStorage.setItem('active_admin_tab', 'batches');
            window.location.hash = '#batches';
            await Swal.fire({ icon: 'success', title: 'Đã tạo đợt mới!', text: `"${name}" đã được ban hành.`, timer: 1800, showConfirmButton: false });
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
    const guidanceLink = document.getElementById('guidanceLink');
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
    
    if (guidanceLink && selectedOption) {
        const docName = selectedOption.getAttribute('data-guidance');
        if (docName) {
            guidanceLink.style.display = 'inline-block';
            guidanceLink.href = '/static/uploads/' + encodeURIComponent(docName);
        } else {
            guidanceLink.style.display = 'none';
        }
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

async function submitEditProfile() {
    const id = document.getElementById('editProfileId').value;
    const name = document.getElementById('editProfileName').value;
    const email = document.getElementById('editProfileEmail').value;
    const phone = document.getElementById('editProfilePhone').value;
    const bio = document.getElementById('editProfileBio').value;
    const faculty = document.getElementById('editProfileFaculty').value;

    try {
        const res = await fetch(`/api/profile/${id}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                full_name: name,
                email: email,
                phone: phone,
                bio: bio,
                faculty: faculty
            })
        });
        const data = await res.json();
        if (res.ok) {
            Swal.fire('Thành công', 'Cập nhật hồ sơ thành công!', 'success').then(() => location.reload());
        } else {
            Swal.fire('Lỗi', data.error || 'Cập nhật thất bại', 'error');
        }
    } catch (e) {
        Swal.fire('Lỗi', 'Không thể kết nối đến máy chủ', 'error');
    }
}

// ===================== THÊM ĐỢT NCKH MỚI =====================
async function submitCreateBatch() {
    const name = document.getElementById('createBatchName').value.trim();
    const year = document.getElementById('createBatchYear').value;
    const type = document.getElementById('createBatchType').value;
    const startDate = document.getElementById('createBatchStart').value;
    const submitDeadline = document.getElementById('createBatchSubmitDeadline').value;
    const endDate = document.getElementById('createBatchEnd').value;
    const desc = document.getElementById('createBatchDesc').value.trim();
    const docPath = document.getElementById('createBatchDoc').value;
    const docName = docPath ? docPath.split('\\').pop() : '';
    
    if (!name) return Swal.fire('Lỗi', 'Vui lòng nhập tên đợt triển khai', 'warning');
    if (startDate && endDate && startDate > endDate) return Swal.fire('Lỗi', 'Ngày bắt đầu không thể sau ngày kết thúc đợt', 'warning');
    if (startDate && submitDeadline && startDate > submitDeadline) return Swal.fire('Lỗi', 'Hạn nộp đề tài phải sau ngày bắt đầu', 'warning');
    if (submitDeadline && endDate && submitDeadline > endDate) return Swal.fire('Lỗi', 'Hạn nộp đề tài không thể sau ngày kết thúc đợt', 'warning');
    
    try {
        const formData = new FormData();
        formData.append('name', name);
        formData.append('academic_year', year);
        formData.append('type', type);
        formData.append('start_date', startDate);
        formData.append('submission_deadline', submitDeadline);
        formData.append('end_date', endDate);
        formData.append('description', desc);
        
        const fileInput = document.getElementById('createBatchDoc');
        if (fileInput.files.length > 0) {
            for (let i = 0; i < fileInput.files.length; i++) {
                formData.append('guidance_doc', fileInput.files[i]);
            }
        }
        
        const res = await fetch('/api/batches', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (res.ok) {
            Swal.fire('Thành công', 'Đã tạo đợt mới thành công!', 'success').then(() => location.reload());
        } else {
            Swal.fire('Lỗi', data.error || 'Tạo đợt thất bại', 'error');
        }
    } catch (e) {
        console.error(e);
        Swal.fire('Lỗi kết nối', 'Không thể kết nối đến máy chủ', 'error');
    }
}

async function submitEditBatch() {
    const id = document.getElementById('editBatchId').value;
    const name = document.getElementById('editBatchName').value.trim();
    const year = document.getElementById('editBatchYear').value;
    const type = document.getElementById('editBatchType').value;
    const startDate = document.getElementById('editBatchStart').value;
    const submitDeadline = document.getElementById('editBatchSubmitDeadline').value;
    const endDate = document.getElementById('editBatchEnd').value;
    const status = document.getElementById('editBatchStatus').value;
    const desc = document.getElementById('editBatchDesc').value.trim();
    const docPath = document.getElementById('editBatchDoc').value;
    const docName = docPath ? docPath.split('\\').pop() : '';
    
    if (!name) return Swal.fire('Lỗi', 'Vui lòng nhập tên đợt triển khai', 'warning');
    if (startDate && endDate && startDate > endDate) return Swal.fire('Lỗi', 'Ngày bắt đầu không thể sau ngày kết thúc đợt', 'warning');
    if (startDate && submitDeadline && startDate > submitDeadline) return Swal.fire('Lỗi', 'Hạn nộp đề tài phải sau ngày bắt đầu', 'warning');
    if (submitDeadline && endDate && submitDeadline > endDate) return Swal.fire('Lỗi', 'Hạn nộp đề tài không thể sau ngày kết thúc đợt', 'warning');
    
    try {
        const formData = new FormData();
        formData.append('name', name);
        formData.append('academic_year', year);
        formData.append('type', type);
        formData.append('start_date', startDate);
        formData.append('submission_deadline', submitDeadline);
        formData.append('end_date', endDate);
        formData.append('status', status);
        formData.append('description', desc);
        
        const fileInput = document.getElementById('editBatchDoc');
        if (fileInput.files.length > 0) {
            for (let i = 0; i < fileInput.files.length; i++) {
                formData.append('guidance_doc', fileInput.files[i]);
            }
        }
        
        const res = await fetch(`/api/batches/${id}`, {
            method: 'PUT',
            body: formData
        });
        const data = await res.json();
        if (res.ok) {
            Swal.fire('Thành công', 'Đã cập nhật đợt thành công!', 'success').then(() => location.reload());
        } else {
            Swal.fire('Lỗi', data.error || 'Cập nhật đợt thất bại', 'error');
        }
    } catch (e) {
        console.error(e);
        Swal.fire('Lỗi kết nối', 'Không thể kết nối đến máy chủ', 'error');
    }
}

async function deleteBatch(id, name) {
    const result = await Swal.fire({
        title: 'Xác nhận xóa đợt?',
        text: `Bạn có chắc chắn muốn xóa đợt NCKH "${name}" không? Thao tác này sẽ xóa đợt khỏi hệ thống.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#6c757d',
        confirmButtonText: '<i class="fa-solid fa-trash-can me-1"></i> Xóa vĩnh viễn',
        cancelButtonText: 'Hủy bỏ'
    });

    if (result.isConfirmed) {
        try {
            const res = await fetch(`/api/batches/${id}`, { method: 'DELETE' });
            const data = await res.json();
            if (res.ok) {
                sessionStorage.setItem('active_admin_tab', 'batches');
                window.location.hash = '#batches';
                await Swal.fire({
                    icon: 'success',
                    title: 'Đã xóa!',
                    text: data.message || 'Đợt NCKH đã được xóa thành công.',
                    timer: 1800,
                    showConfirmButton: false
                });
                location.reload();
            } else {
                Swal.fire('Lỗi', data.error || 'Có lỗi xảy ra', 'error');
            }
        } catch(e) {
            Swal.fire('Lỗi', 'Không thể kết nối đến máy chủ', 'error');
        }
    }
}
window.deleteBatch = deleteBatch;

document.addEventListener('DOMContentLoaded', () => {
    const today = new Date().toISOString().split('T')[0];
    
    const startInput = document.getElementById('createBatchStart');
    const submitInput = document.getElementById('createBatchSubmitDeadline');
    const endInput = document.getElementById('createBatchEnd');
    
    if (startInput) {
        startInput.setAttribute('min', today);
        startInput.addEventListener('change', () => {
            if (submitInput) submitInput.setAttribute('min', startInput.value);
            if (endInput) endInput.setAttribute('min', startInput.value);
        });
    }
    
    if (submitInput) {
        submitInput.setAttribute('min', today);
        submitInput.addEventListener('change', () => {
            if (endInput) endInput.setAttribute('min', submitInput.value);
            if (startInput && startInput.value > submitInput.value) {
                startInput.value = submitInput.value;
            }
        });
    }
    
    if (endInput) {
        endInput.setAttribute('min', today);
        endInput.addEventListener('change', () => {
            if (submitInput && submitInput.value > endInput.value) {
                submitInput.value = endInput.value;
            }
            if (startInput && startInput.value > endInput.value) {
                startInput.value = endInput.value;
            }
        });
    }
});

async function readNotification(id, content, fromAll = false) {
    try {
        await fetch(`/api/notifications/${id}/read`, { method: 'PATCH' });
    } catch(e) { console.error(e); }

    let parts = content.split('|||');
    let textHtml = parts[0];
    let htmlContent = `<div class="ql-editor" style="text-align: left; font-size: 14px; padding: 0;">${textHtml}</div>`;
    
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

    Swal.fire({
        title: 'Chi tiết Thông báo',
        html: htmlContent,
        icon: 'info',
        confirmButtonText: 'Đóng'
    }).then(() => {
        if (window._isOpeningMembersModal) {
            // Đang chuyển sang modal thành viên nhóm, không tự mở lại danh sách thông báo
            return;
        }
        if (fromAll) {
            // Reopen the notification list without full page reload
            showAllNotifications();
        } else {
            // Just update badge count without full reload
            _refreshNotifBadge();
        }
    });
}

async function showAllNotifications() {
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
                    onclick="event.preventDefault(); _openNotifDetail(${n.id})">
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
}

// Real-time Live Synchronization for Notifications & Invitee Actions
async function syncNotificationsLive(immediate = false) {
    try {
        const res = await fetch('/api/notifications/sync');
        if (!res.ok) return;
        const data = await res.json();
        
        // 1. Update bell badge counter
        const totalBadge = data.total_badge_count || 0;
        document.querySelectorAll('#notifBellBadge, .notif-badge, [data-notif-count]').forEach(el => {
            el.textContent = totalBadge;
            el.style.display = totalBadge > 0 ? '' : 'none';
        });

        // 2. Check for newly arrived notifications to show live popup toast
        if (data.notifications && data.notifications.length > 0) {
            const newNotifs = [];
            data.notifications.forEach(n => {
                if (!window._seenNotifIds.has(n.id)) {
                    if (window._notifInitDone && !n.is_read) {
                        newNotifs.push(n);
                    }
                    window._seenNotifIds.add(n.id);
                }
            });

            // If new notifications arrived live, trigger toast
            if (newNotifs.length > 0 && typeof Swal !== 'undefined') {
                newNotifs.slice(0, 2).forEach(n => {
                    const temp = document.createElement("div");
                    temp.innerHTML = n.content.split('|||')[0];
                    const cleanText = (temp.textContent || temp.innerText || "Bạn có thông báo mới").trim();
                    Swal.mixin({
                        toast: true,
                        position: 'top-end',
                        showConfirmButton: false,
                        timer: 5000,
                        timerProgressBar: true
                    }).fire({
                        icon: 'info',
                        title: '🔔 Thông báo mới',
                        text: cleanText.length > 120 ? cleanText.substring(0, 120) + '...' : cleanText
                    });
                });
            }
        }
        window._notifInitDone = true;

        // 3. Live update the dropdown list container (#notifDropdownList)
        const listEl = document.getElementById('notifDropdownList');
        if (listEl && (immediate || !listEl.closest('.dropdown-menu.show'))) {
            let itemsHtml = '';
            
            // Render invitations
            if (data.invitations && data.invitations.length > 0) {
                data.invitations.forEach(inv => {
                    const isPending = inv.status === 'pending' || inv.status === 'invited';
                    const isAccepted = inv.status === 'accepted' || inv.status === 'joined';
                    const iconClass = isAccepted ? 'fa-check' : (isPending ? 'fa-users' : 'fa-xmark');
                    const iconBg = isAccepted ? 'bg-success text-white' : (isPending ? 'bg-warning text-dark' : 'bg-secondary-subtle text-secondary');
                    const badgeHtml = isAccepted ? 
                        '<span class="badge bg-success-subtle text-success border border-success-subtle rounded-pill" style="font-size: 10px;"><i class="fa-solid fa-check me-1"></i>Đã chấp nhận</span>' :
                        (isPending ? '<span class="badge bg-warning text-dark rounded-pill" style="font-size: 10px;">Chờ phản hồi</span>' :
                                    '<span class="badge bg-secondary-subtle text-secondary rounded-pill" style="font-size: 10px;">Đã từ chối</span>');

                    let actionHtml = '';
                    if (isPending) {
                        actionHtml = `
                            <div class="d-flex gap-2">
                                <button class="btn btn-sm btn-dark rounded-pill px-3 py-1" style="font-size: 11px;" onclick="handleGroupInvitation(${inv.group_id}, 'accepted')">
                                    <i class="fa-solid fa-check me-1"></i> Đồng ý
                                </button>
                                <button class="btn btn-sm btn-outline-secondary rounded-pill px-3 py-1" style="font-size: 11px;" onclick="handleGroupInvitation(${inv.group_id}, 'rejected')">
                                    <i class="fa-solid fa-xmark me-1"></i> Từ chối
                                </button>
                            </div>
                        `;
                    } else if (isAccepted) {
                        actionHtml = `<div class="text-success small fw-semibold" style="font-size: 11px;"><i class="fa-solid fa-circle-check me-1"></i> Đã chấp nhận lời mời tham gia nhóm.</div>`;
                    } else {
                        actionHtml = `<div class="text-muted small fst-italic" style="font-size: 11px;"><i class="fa-solid fa-ban me-1"></i> Đã từ chối lời mời này.</div>`;
                    }

                    itemsHtml += `
                        <li>
                            <div class="dropdown-item p-3 border-bottom ${isPending ? 'bg-warning-subtle' : 'bg-white'}" data-inv-group-id="${inv.group_id}">
                                <div class="d-flex gap-3 align-items-start">
                                    <div class="${iconBg} rounded-circle d-flex align-items-center justify-content-center flex-shrink-0" style="width: 32px; height: 32px;">
                                        <i class="fa-solid ${iconClass}"></i>
                                    </div>
                                    <div class="flex-grow-1" style="white-space: normal;">
                                        <div class="d-flex justify-content-between align-items-center mb-1">
                                            <span class="fw-bold small text-dark">Lời mời tham gia nhóm NCKH</span>
                                            ${badgeHtml}
                                        </div>
                                        <div class="small text-muted mb-2" style="line-height: 1.4;">
                                            Bạn được mời vào nhóm <strong>${inv.group_name}</strong>
                                            ${inv.topic_title ? ` - Đề tài: <em>${inv.topic_title}</em>` : ''}
                                        </div>
                                        ${actionHtml}
                                    </div>
                                </div>
                            </div>
                        </li>
                    `;
                });
            }

            // Render system notifications
            if (data.notifications && data.notifications.length > 0) {
                data.notifications.forEach(notif => {
                    const temp = document.createElement("div");
                    temp.innerHTML = notif.content.split('|||')[0];
                    const cleanText = (temp.textContent || temp.innerText || "").trim();
                    const snippet = cleanText.length > 80 ? cleanText.substring(0, 80) + '...' : cleanText;
                    const encodedContent = encodeURIComponent(notif.content);

                    itemsHtml += `
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
                    `;
                });
            }

            if (!itemsHtml) {
                itemsHtml = '<li class="p-4 text-center text-muted small">Không có thông báo nào</li>';
            }

            listEl.innerHTML = itemsHtml;
        }

        // 4. Live update group member statuses on the leader's screen
        if (data.group_data && data.group_data.members) {
            data.group_data.members.forEach(member => {
                const row = document.getElementById(`reg-member-row-${member.student_id}`) ||
                            Array.from(document.querySelectorAll('#regMembersTableBody tr')).find(r => 
                                r.textContent.includes(member.code) || r.textContent.includes(member.name)
                            );
                if (row) {
                    const statusTd = row.children[3] || row.querySelector('td:nth-child(4)');
                    if (statusTd) {
                        const isAccepted = member.status === 'accepted' || member.status === 'joined';
                        if (isAccepted && !statusTd.innerHTML.includes('Đã tham gia')) {
                            statusTd.innerHTML = '<span class="badge bg-success-subtle text-success rounded-pill px-2.5 py-1 small"><i class="fa-solid fa-check me-1"></i>Đã tham gia</span>';
                        }
                    }
                }
            });

            // Update topic status if topic was promoted to pending
            if (data.group_data.topic && data.group_data.topic.status) {
                const topicBadge = document.querySelector('#view-s-register .badge.bg-warning-subtle, #view-s-register .badge.bg-primary-subtle');
                if (topicBadge && data.group_data.topic.status_label && topicBadge.textContent !== data.group_data.topic.status_label) {
                    topicBadge.textContent = data.group_data.topic.status_label;
                }
            }
        }
    } catch(err) {
        // Silently catch background sync errors
    }
}

function _refreshNotifBadge() {
    syncNotificationsLive(true);
}

// Automatically start background live polling on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    if (!window._liveSyncTimer) {
        syncNotificationsLive();
        window._liveSyncTimer = setInterval(syncNotificationsLive, 4000);
    }
});

document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        syncNotificationsLive(true);
    }
});

function _openNotifDetail(id) {
    const content = window._allNotifications[id];
    if (content === undefined) return;
    Swal.close();
    setTimeout(() => readNotification(id, content, true), 200);
}

async function deleteAllReadNotifications() {
    try {
        const result = await Swal.fire({
            title: 'Xóa thư đã đọc?',
            text: "Tất cả các thông báo đã đọc sẽ bị xóa vĩnh viễn khỏi hòm thư của bạn.",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Đồng ý',
            cancelButtonText: 'Hủy'
        });

        if (result.isConfirmed) {
            const res = await fetch('/api/notifications/read', { method: 'DELETE' });
            if (res.ok) {
                Swal.fire('Thành công', 'Đã xóa tất cả thông báo đã đọc.', 'success').then(() => location.reload());
            } else {
                Swal.fire('Lỗi', 'Không thể xóa thông báo', 'error');
            }
        }
    } catch (e) {
        Swal.fire('Lỗi', 'Có lỗi kết nối', 'error');
    }
}

// ==========================================
// HIỂN THỊ DANH SÁCH THÀNH VIÊN NHÓM (MODAL)
// ==========================================
window.showGroupMembersModal = async function(groupId) {
    if (typeof Swal === 'undefined') return;
    if (window._loadingGroupMembers) return; // Tránh bấm nhiều lần liên tiếp

    window._loadingGroupMembers = true;
    window._isOpeningMembersModal = true;

    // Hiển thị trạng thái đang tải nhẹ nhàng trên nút nếu có
    const targetBtn = document.activeElement && (document.activeElement.tagName === 'BUTTON' || document.activeElement.tagName === 'A')
        ? document.activeElement
        : null;
    let oldBtnHtml = '';
    if (targetBtn && targetBtn.textContent.includes('thành viên')) {
        oldBtnHtml = targetBtn.innerHTML;
        targetBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> Đang mở...';
        targetBtn.style.pointerEvents = 'none';
    }

    try {
        let url = groupId ? `/api/groups/${groupId}` : '/api/groups/my_group';
        let resp = await fetch(url);
        let data = await resp.json();

        // Fallback sang my_group nếu groupId không tìm thấy
        if ((!data.success || !data.group) && groupId) {
            resp = await fetch('/api/groups/my_group');
            data = await resp.json();
        }

        if (!data.success || !data.group) {
            window._isOpeningMembersModal = false;
            Swal.fire('Thông báo', data.error || 'Chưa tìm thấy thông tin nhóm nghiên cứu.', 'info');
            return;
        }

        const group = data.group;
        const members = group.members || [];
        
        let membersRows = '';
        if (members.length === 0) {
            membersRows = `<tr><td colspan="5" class="text-center text-muted py-3">Chưa có thành viên nào khác.</td></tr>`;
        } else {
            members.forEach((m) => {
                const isLeader = (m.user_id === group.leader_id);
                const roleBadge = isLeader 
                    ? `<span class="badge bg-primary-subtle text-primary border border-primary-subtle rounded-pill px-2.5 py-1 small fw-bold">Trưởng nhóm</span>`
                    : `<span class="badge bg-secondary-subtle text-secondary border rounded-pill px-2.5 py-1 small">Thành viên</span>`;

                let statusBadge = '';
                const st = (m.status || '').toLowerCase();
                if (st === 'accepted' || st === 'joined' || isLeader) {
                    statusBadge = `<span class="badge bg-success-subtle text-success border border-success-subtle rounded-pill px-2.5 py-1 small fw-bold"><i class="fa-solid fa-circle-check me-1"></i>Đã tham gia</span>`;
                } else if (st === 'pending' || st === 'invited') {
                    statusBadge = `<span class="badge bg-warning-subtle text-warning border border-warning-subtle rounded-pill px-2.5 py-1 small fw-bold"><i class="fa-solid fa-clock me-1"></i>Đang chờ xác nhận</span>`;
                } else if (st === 'rejected' || st === 'declined') {
                    statusBadge = `<span class="badge bg-danger-subtle text-danger border border-danger-subtle rounded-pill px-2.5 py-1 small fw-bold"><i class="fa-solid fa-circle-xmark me-1"></i>Đã từ chối</span>`;
                } else {
                    statusBadge = `<span class="badge bg-light text-dark border rounded-pill px-2 py-1 small">${m.status || '-'}</span>`;
                }

                const initials = (m.full_name || 'SV').split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();

                membersRows += `
                    <tr>
                        <td class="text-start">
                            <div class="d-flex align-items-center gap-2">
                                <div class="rounded-circle ${isLeader ? 'bg-primary text-white' : 'bg-primary-subtle text-primary'} d-flex align-items-center justify-content-center fw-bold small" style="width: 32px; height: 32px; min-width: 32px; font-size: 11px;">
                                    ${initials}
                                </div>
                                <div>
                                    <div class="fw-bold text-dark small mb-0">${m.full_name || 'Chưa cập nhật'}</div>
                                    <div class="text-muted" style="font-size: 11px;">${m.email || ''}</div>
                                </div>
                            </div>
                        </td>
                        <td class="font-monospace small fw-semibold text-secondary">${m.student_id || '-'}</td>
                        <td class="small text-muted">${m.faculty || '-'}</td>
                        <td class="text-center">${roleBadge}</td>
                        <td class="text-end">${statusBadge}</td>
                    </tr>
                `;
            });
        }

        const modalHtml = `
            <div class="text-start mb-3 pb-2 border-bottom">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <div>
                        <span class="badge bg-primary text-white rounded-pill px-3 py-1 small mb-1">
                            <i class="fa-solid fa-users me-1"></i> ${group.name}
                        </span>
                        <div class="fw-bold text-dark fs-6 mt-1">${group.topic_title || 'Đề tài NCKH (Chưa đặt tên)'}</div>
                    </div>
                    <span class="badge bg-light text-muted border px-2.5 py-1 small">
                        ${members.length} thành viên
                    </span>
                </div>
                ${group.mentor_name ? `
                    <div class="small text-muted">
                        <i class="fa-solid fa-chalkboard-user text-primary me-1"></i> GVHD: <strong>${group.mentor_name}</strong> 
                        ${group.mentor_faculty ? `<span class="text-secondary">(${group.mentor_faculty})</span>` : ''}
                    </div>
                ` : ''}
            </div>

            <div class="table-responsive rounded-3 border bg-white" style="max-height: 320px; overflow-y: auto;">
                <table class="table table-hover align-middle mb-0 text-start">
                    <thead class="table-light text-muted small position-sticky top-0" style="z-index: 1;">
                        <tr>
                            <th>HỌ & TÊN</th>
                            <th>MSSV</th>
                            <th>KHOA</th>
                            <th class="text-center">VAI TRÒ</th>
                            <th class="text-end">TRẠNG THÁI</th>
                        </tr>
                    </thead>
                    <tbody class="small">
                        ${membersRows}
                    </tbody>
                </table>
            </div>
        `;

        Swal.fire({
            title: 'Danh sách Thành viên Nhóm',
            html: modalHtml,
            width: '680px',
            showCancelButton: true,
            showDenyButton: !!window._lastNotifModal,
            confirmButtonText: '<i class="fa-solid fa-diagram-project me-1"></i> Đi đến Nhóm NCKH',
            denyButtonText: '<i class="fa-solid fa-arrow-left me-1"></i> Quay lại',
            cancelButtonText: 'Đóng',
            confirmButtonColor: '#4f46e5',
            denyButtonColor: '#4b5563',
            cancelButtonColor: '#9ca3af'
        }).then((result) => {
            window._isOpeningMembersModal = false;
            if (result.isConfirmed) {
                if (typeof switchTab === 'function') {
                    const groupNav = document.querySelector('a[href*="s-group"]');
                    switchTab('s-group', groupNav);
                } else {
                    window.location.hash = '#s-group';
                }
            } else if (result.isDenied && window._lastNotifModal) {
                readNotification(window._lastNotifModal.id, window._lastNotifModal.content, window._lastNotifModal.fromAll);
            }
        });

    } catch (err) {
        console.error('Error fetching group members:', err);
        window._isOpeningMembersModal = false;
        Swal.fire('Lỗi', 'Không thể lấy thông tin thành viên nhóm.', 'error');
    } finally {
        window._loadingGroupMembers = false;
        if (targetBtn && oldBtnHtml) {
            targetBtn.innerHTML = oldBtnHtml;
            targetBtn.style.pointerEvents = '';
        }
    }
};

// Global click interceptor bắt sự kiện click nút "Xem thành viên nhóm"
document.addEventListener('click', function (e) {
    const el = e.target.closest('a, button');
    if (!el) return;
    const text = (el.textContent || '').trim();
    if (text.includes('Xem thành viên nhóm') || text.includes('Quản lý nhóm')) {
        const onclickAttr = el.getAttribute('onclick') || '';
        if (onclickAttr.includes('showGroupMembersModal')) {
            // Đã có inline onclick xử lý, không gọi trùng lặp
            return;
        }
        e.preventDefault();
        e.stopPropagation();
        let m = onclickAttr.match(/showGroupMembersModal\((\d+)\)/);
        let gid = m ? parseInt(m[1]) : null;
        window.showGroupMembersModal(gid);
    }
});


