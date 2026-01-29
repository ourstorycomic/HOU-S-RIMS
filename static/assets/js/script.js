// assets/js/script.js
document.addEventListener('DOMContentLoaded', function() {
    console.log("HOU S-RIMS Scripts Loaded Successfully!");
    
    // Khởi tạo tất cả Tooltip của Bootstrap (nếu có sử dụng data-bs-toggle="tooltip")
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // ĐẢM BẢO CHỈ VIEW ĐẦU TIÊN HIỂN THỊ KHI TRANG LOAD
    const contentArea = document.querySelector('.content-area');
    if (contentArea) {
        const allViews = contentArea.querySelectorAll(':scope > div[id^="view-"]');
        console.log('Initializing views, total found:', allViews.length);
        
        // Kiểm tra URL hash để hiển thị view tương ứng
        const hash = window.location.hash.substring(1); // Bỏ dấu #
        let targetViewFound = false;
        
        if (hash) {
            // Tìm view theo ID, không cần kiểm tra parentElement
            const targetView = document.getElementById('view-' + hash);
            if (targetView) {
                targetViewFound = true;
                console.log('Hash found, showing view:', 'view-' + hash);
                
                // Ẩn tất cả views trong document
                const allViewsInDoc = document.querySelectorAll('[id^="view-"]');
                allViewsInDoc.forEach(view => {
                    view.classList.add('hidden');
                    view.classList.remove('fade-in');
                });
                
                // Hiện view từ hash
                targetView.classList.remove('hidden');
                targetView.classList.add('fade-in');
                
                // Active menu item tương ứng
                const sidebar = document.querySelector('.sidebar');
                if (sidebar) {
                    const navLinks = sidebar.querySelectorAll('.nav-link');
                    const menuCategories = sidebar.querySelectorAll('.menu-category');
                    let isStudent = false;
                    let isLecturer = false;
                    
                    menuCategories.forEach(cat => {
                        const text = cat.textContent;
                        if (text.includes('SINH VIÊN')) isStudent = true;
                        if (text.includes('GIẢNG VIÊN')) isLecturer = true;
                    });
                    
                    navLinks.forEach(link => {
                        link.classList.remove('active-main', 'active-purple', 'active-student');
                        const onclick = link.getAttribute('onclick');
                        if (onclick && onclick.includes(hash)) {
                            if (isStudent) {
                                link.classList.add('active-student');
                            } else if (isLecturer) {
                                link.classList.add('active-purple');
                            } else {
                                link.classList.add('active-main');
                            }
                        }
                    });
                }
            }
        }
        
        // Nếu không có hash hoặc hash không hợp lệ, hiển thị view đầu tiên
        if (!targetViewFound) {
            allViews.forEach((view, index) => {
                if (index === 0) {
                    view.classList.remove('hidden');
                    view.classList.add('fade-in');
                    console.log('First view shown:', view.id);
                } else {
                    view.classList.add('hidden');
                    console.log('Other view hidden:', view.id);
                }
            });
        }
    }
});

/**
 * 1. HÀM CHUYỂN TAB (NAVIGATION)
 */
function switchTab(tabName, element) {
    // Lưu vị trí scroll hiện tại của sidebar
    const sidebarMenu = document.querySelector('.sidebar-menu-wrapper');
    const currentScrollPosition = sidebarMenu ? sidebarMenu.scrollTop : 0;
    console.log('=== switchTab START ===');
    console.log('Tab name:', tabName);
    console.log('Element:', element);
    
    // A. Xử lý UI của thanh điều hướng (Sidebar)
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        console.log('Sidebar found');
        // Remove active khỏi tất cả nav-link trong sidebar
        const allNavLinks = sidebar.querySelectorAll('.nav-link');
        console.log('Nav links found:', allNavLinks.length);
        
        allNavLinks.forEach(link => {
            link.classList.remove('active-main', 'active-purple', 'active-student');
        });
        
        // Thêm class active phù hợp cho element được click
        if (element && element.classList && element.classList.contains('nav-link')) {
            // Xác định role dựa vào menu category
            const menuCategories = sidebar.querySelectorAll('.menu-category');
            let isStudent = false;
            let isLecturer = false;
            
            menuCategories.forEach(cat => {
                const text = cat.textContent;
                if (text.includes('SINH VIÊN')) isStudent = true;
                if (text.includes('GIẢNG VIÊN')) isLecturer = true;
            });
            
            console.log('Role detected - Student:', isStudent, 'Lecturer:', isLecturer);
            
            if (isStudent) {
                element.classList.add('active-student');
            } else if (isLecturer) {
                element.classList.add('active-purple');
            } else {
                element.classList.add('active-main');
            }
        }
    }

    // B. Xử lý hiển thị nội dung (Content Views)
    const contentArea = document.querySelector('.content-area');
    console.log('Content area found:', !!contentArea);
    
    if (contentArea) {
        // Tìm tất cả các views - thử nhiều cách
        const allViewsDirect = contentArea.querySelectorAll(':scope > div[id^="view-"]');
        const allViewsAny = document.querySelectorAll('[id^="view-"]');
        
        console.log('Direct children views found:', allViewsDirect.length);
        console.log('All views in document:', allViewsAny.length);
        
        // Sử dụng tất cả views trong document để ẩn
        allViewsAny.forEach((view, index) => {
            console.log(`Hiding view ${index}:`, view.id);
            view.classList.add('hidden');
            view.classList.remove('fade-in');
        });
    }

    // C. Hiện view được chọn
    const viewId = 'view-' + tabName;
    const selectedView = document.getElementById(viewId);
    console.log('Looking for view:', viewId);
    console.log('Selected view found:', !!selectedView);
    
    if (selectedView) {
        selectedView.classList.remove('hidden');
        
        // Reset animation để chạy lại mỗi lần click
        selectedView.classList.remove('fade-in');
        void selectedView.offsetWidth; // Force reflow
        selectedView.classList.add('fade-in');
        
        console.log('View shown:', selectedView.id, 'Classes:', selectedView.className);
    } else {
        console.error('ERROR: View not found -', viewId);
        console.log('Available views:', Array.from(document.querySelectorAll('[id^="view-"]')).map(v => v.id));
    }
    
    // Khôi phục vị trí scroll của sidebar sau khi xử lý xong
    if (sidebarMenu) {
        setTimeout(() => {
            sidebarMenu.scrollTop = currentScrollPosition;
        }, 0);
    }
    
    console.log('=== switchTab END ===');
}

/**
 * 2. HÀM HIỂN THỊ THÔNG BÁO (TOAST)
 */
function showToast(message) {
    const toastElement = document.getElementById('liveToast');
    const toastBody = document.getElementById('toastMessage');
    
    if (toastElement && toastBody) {
        toastBody.innerText = message;
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
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