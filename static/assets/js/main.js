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
            alert('Đăng ký đề tài thành công!');
            // Reload trang hoặc đóng Modal tại đây
            // $('#registerModal').modal('hide');
            // location.reload();
            return result;
        } else {
            alert('Lỗi: ' + result.error);
        }
    } catch (error) {
        console.error('Lỗi khi đăng ký đề tài:', error);
        alert('Đã xảy ra lỗi hệ thống khi đăng ký.');
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
            alert(`Đã cập nhật trạng thái thành: ${status}`);
            // Reload hoặc đóng Modal
            // location.reload();
            return result;
        } else {
            alert('Lỗi: ' + result.error);
        }
    } catch (error) {
        console.error('Lỗi khi xét duyệt:', error);
        alert('Đã xảy ra lỗi hệ thống khi xét duyệt.');
    }
}

// Khi DOM load xong, gán sự kiện cho các nút nếu có
document.addEventListener('DOMContentLoaded', () => {
    // Ví dụ gán sự kiện cho form đăng ký
    const btnRegister = document.getElementById('btnSubmitRegister');
    if (btnRegister) {
        btnRegister.addEventListener('click', () => {
            const topicData = {
                name: document.getElementById('topicName')?.value,
                description: document.getElementById('topicDesc')?.value,
                batch_id: parseInt(document.getElementById('batchId')?.value),
                mentor_id: parseInt(document.getElementById('mentorId')?.value),
                group_id: parseInt(document.getElementById('groupId')?.value) // Lấy từ auth user
            };
            registerTopic(topicData);
        });
    }

    // Ví dụ gán sự kiện cho nút Duyệt
    const btnApprove = document.getElementById('btnApproveTopic');
    if (btnApprove) {
        btnApprove.addEventListener('click', () => {
            const topicId = parseInt(document.getElementById('currentTopicId')?.value);
            approveTopic(topicId, 'approved');
        });
    }

    // Ví dụ gán sự kiện cho nút Từ chối
    const btnReject = document.getElementById('btnRejectTopic');
    if (btnReject) {
        btnReject.addEventListener('click', () => {
            const topicId = parseInt(document.getElementById('currentTopicId')?.value);
            approveTopic(topicId, 'rejected');
        });
    }
});
