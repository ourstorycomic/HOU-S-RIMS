// static/assets/js/main.js

/**
 * Hàm hỗ trợ Đăng ký đề tài
 * Gọi API POST /api/topics/register
 * 
 * @param {Object} data - Dữ liệu đăng ký (name, description, batch_id, mentor_id, group_id)
 */
async function registerTopic(data) {
    try {
        const response = await fetch('/api/topics/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            Swal.fire('Thành công', 'Đăng ký đề tài thành công!', 'success');
            return result;
        } else {
            Swal.fire('Lỗi', result.error, 'error');
        }
    } catch (error) {
        console.error('Lỗi khi đăng ký đề tài:', error);
        Swal.fire('Lỗi', 'Đã xảy ra lỗi hệ thống khi đăng ký.', 'error');
    }
}

/**
 * Hàm hỗ trợ Xét duyệt đề tài
 * Gọi API POST /api/topics/{id}/approve
 * 
 * @param {Number} topicId - ID của đề tài
 * @param {String} status - Trạng thái mới (ví dụ: 'approved' hoặc 'rejected')
 */
async function approveTopic(topicId, status) {
    try {
        const response = await fetch(`/api/topics/${topicId}/approve`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: status })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            Swal.fire('Thành công', `Đã cập nhật trạng thái thành: ${status}`, 'success');
            return result;
        } else {
            Swal.fire('Lỗi', result.error, 'error');
        }
    } catch (error) {
        console.error('Lỗi khi xét duyệt:', error);
        Swal.fire('Lỗi', 'Đã xảy ra lỗi hệ thống khi xét duyệt.', 'error');
    }
}

// Khi DOM load xong, gán sự kiện cho các nút nếu có
document.addEventListener('DOMContentLoaded', () => {
    // Gán sự kiện cho nút đăng ký trong student.html
    const btnRegister = document.getElementById('btnSubmitRegister');
    if (btnRegister) {
        btnRegister.addEventListener('click', () => {
            const nameField = document.getElementById('topicName');
            if (!nameField || !nameField.value.trim()) {
                Swal.fire('Lỗi', 'Vui lòng nhập tên đề tài!', 'warning');
                return;
            }

            const topicData = {
                name: document.getElementById('topicName').value.trim(),
                description: document.getElementById('topicDesc').value.trim(),
                batch_id: parseInt(document.getElementById('batchId').value),
                mentor_id: parseInt(document.getElementById('mentorId').value),
                group_id: parseInt(document.getElementById('groupId').value)
            };

            registerTopic(topicData).then((res) => {
                if (res && res.topic_id) {
                    if(typeof showToast === 'function') showToast('Đã gửi hồ sơ đăng ký thành công qua API!');
                }
            });
        });
    }

    // Gán sự kiện cho nút Duyệt trong lecturer.html
    const btnApprove = document.getElementById('btnApproveTopic');
    if (btnApprove) {
        btnApprove.addEventListener('click', () => {
            // Giả sử duyệt topic số 1
            approveTopic(1, 'approved').then(() => {
                if(typeof showToast === 'function') showToast('Đã gọi API xác nhận hướng dẫn đề tài #1!');
            });
        });
    }

    // Gán sự kiện cho nút Từ chối
    const btnReject = document.getElementById('btnRejectTopic');
    if (btnReject) {
        btnReject.addEventListener('click', () => {
            const topicId = parseInt(document.getElementById('currentTopicId')?.value);
            approveTopic(topicId, 'rejected');
        });
    }

    // Gán sự kiện cho nút Nộp báo cáo trong student.html
    const btnUpload = document.getElementById('btnUploadSubmission');
    if (btnUpload) {
        btnUpload.addEventListener('click', async () => {
            const fileInput = document.getElementById('submissionFile');
            if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
                Swal.fire('Lỗi', 'Vui lòng chọn file để nộp!', 'warning');
                return;
            }

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('type', document.getElementById('submissionType').value);
            formData.append('topic_id', document.getElementById('submissionTopicId').value);
            formData.append('uploader_id', document.getElementById('submissionUploaderId').value);

            try {
                const response = await fetch('/api/submissions/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                if (response.ok) {
                    Swal.fire('Thành công', 'Nộp báo cáo/tài liệu thành công!', 'success');
                } else {
                    Swal.fire('Lỗi', result.error, 'error');
                }
            } catch (error) {
                console.error('Lỗi khi nộp bài:', error);
                Swal.fire('Lỗi', 'Đã xảy ra lỗi hệ thống khi nộp bài.', 'error');
            }
        });
    }
});
