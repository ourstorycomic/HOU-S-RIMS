// assets/js/script.js

// Hàm đóng/mở sidebar trên mobile
function toggleSidebar() {
    document.body.classList.toggle('sidebar-open');
}

document.addEventListener('DOMContentLoaded', function() {
    console.log("HOU S-RIMS Scripts Loaded Successfully!");
    
    // Khởi tạo tất cả Tooltip của Bootstrap (nếu có sử dụng data-bs-toggle="tooltip")
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
});

/**
 * 2. HÀM HIỂN THỊ THÔNG BÁO (TOAST)
 */
function showToast(message, type = 'success') {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            title: message,
            icon: type,
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true
        });
    } else {
        alert(message);
    }
}

/**
 * 3. HÀM LỌC BẢNG DỮ LIỆU (FILTER TABLE)
 */

function filterTable(type, btn) {
    updateFilterButtonState(btn);

    const rowsPending = document.querySelectorAll('.row-pending');
    const rowsApproved = document.querySelectorAll('.row-approved');

    if (type === 'pending') {
        rowsPending.forEach(r => r.classList.remove('d-none'));
        rowsApproved.forEach(r => r.classList.add('d-none'));
    } else if (type === 'approved') {
        rowsPending.forEach(r => r.classList.add('d-none'));
        rowsApproved.forEach(r => r.classList.remove('d-none'));
    } else {
        // 'all'
        rowsPending.forEach(r => r.classList.remove('d-none'));
        rowsApproved.forEach(r => r.classList.remove('d-none'));
    }
}

// Hàm dùng riêng cho Faculty
function filterTopics(status, btn) {
    updateFilterButtonState(btn);

    const pending = document.querySelectorAll('.status-pending');
    const approved = document.querySelectorAll('.status-approved');

    if (status === 'pending') {
        pending.forEach(el => el.classList.remove('d-none'));
        approved.forEach(el => el.classList.add('d-none'));
    } else if (status === 'approved') {
        pending.forEach(el => el.classList.add('d-none'));
        approved.forEach(el => el.classList.remove('d-none'));
    } else {
        // 'all'
        pending.forEach(el => el.classList.remove('d-none'));
        approved.forEach(el => el.classList.remove('d-none'));
    }
}

// Helper: Cập nhật trạng thái active của nút lọc
function updateFilterButtonState(clickedBtn) {
    const container = clickedBtn.parentElement;
    const allBtns = container.querySelectorAll('.btn-filter');

    allBtns.forEach(b => {
        b.classList.remove('btn-primary', 'active');
        b.classList.add('btn-light', 'text-muted');
    });

    clickedBtn.classList.remove('btn-light', 'text-muted');
    clickedBtn.classList.add('btn-primary', 'active');
}

/**
 * 4. HÀM THÊM DÒNG RUBRIC (DOM MANIPULATION)
 */
function addRubricCriteria() {
    const container = document.getElementById('rubricContainer');
    if (!container) return;

    const count = container.children.length + 1;
    
    const html = `
        <div class="d-flex align-items-center justify-content-between bg-white border p-3 rounded-3 mb-3 fade-in-up">
            <div class="d-flex align-items-center gap-3 w-100 me-3">
                <div class="bg-secondary text-white rounded-circle d-flex align-items-center justify-content-center fw-bold flex-shrink-0" style="width: 32px; height: 32px;">${count}</div>
                <div class="w-100">
                    <input type="text" class="form-control border-0 p-0 fw-bold mb-1" placeholder="Nhập tên tiêu chí mới..." style="background: transparent;">
                    <textarea class="form-control border-0 p-0 small text-muted" rows="1" placeholder="Mô tả chi tiết tiêu chí đánh giá..." style="background: transparent; resize: none;"></textarea>
                </div>
            </div>
            <div class="text-end" style="min-width: 80px;">
                <input type="number" class="form-control form-control-sm text-end fw-bold mb-1" placeholder="Max" value="1.0">
                <div class="input-group input-group-sm">
                    <input type="number" class="form-control text-end p-1" placeholder="%">
                    <span class="input-group-text p-1">%</span>
                </div>
            </div>
        </div>`;

    container.insertAdjacentHTML('beforeend', html);
    showToast('Đã thêm dòng tiêu chí mới! Hãy nhập nội dung.');
    
    container.lastElementChild.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}