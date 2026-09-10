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
    // Gán sự kiện cho nút đăng ký trong student.html
    const btnRegister = document.getElementById('btnSubmitRegister');
    if (btnRegister) {
        btnRegister.addEventListener('click', () => {
            // Thay vì lấy dữ liệu từ input không tồn tại, mock dữ liệu để test luồng
            const topicData = {
                name: "Đề tài Test Đăng ký từ Giao diện Sinh viên",
                description: "Nội dung mô tả đề tài được gửi từ UI.",
                batch_id: 1,
                mentor_id: 2,
                group_id: 1
            };
            registerTopic(topicData).then(() => {
                if(typeof showToast === 'function') showToast('Đã gửi hồ sơ đăng ký thành công qua API!');
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

    // Ví dụ gán sự kiện cho nút Từ chối
    const btnReject = document.getElementById('btnRejectTopic');
    if (btnReject) {
        btnReject.addEventListener('click', () => {
            const topicId = parseInt(document.getElementById('currentTopicId')?.value);
            approveTopic(topicId, 'rejected');
        });
    }
});
