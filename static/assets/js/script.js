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
    
    // ĐẢM BẢO CHỈ VIEW ĐẦU TIÊN HIỂN THỊ KHI TRANG LOAD (HOẶC THEO HASH / SESSION)
    const contentArea = document.querySelector('.content-area');
    if (contentArea) {
        const allViews = contentArea.querySelectorAll(':scope > div[id^="view-"]');
        console.log('Initializing views, total found:', allViews.length);
        
        // Kiểm tra URL hash hoặc sessionStorage để hiển thị view tương ứng
        let rawHash = window.location.hash.substring(1); // Bỏ dấu #
        let hash = rawHash.split('?')[0];
        if (!hash) {
            hash = sessionStorage.getItem('active_admin_tab') || '';
        }
        let targetViewFound = false;
        
        if (hash) {
            const tabAliases = {
                'batches': 'deployment',
                'deployment': 'deployment',
                'approvals': 'approval',
                'approval': 'approval',
                'councils': 'council',
                'council': 'council'
            };
            const resolvedHash = tabAliases[hash] || hash;
            const targetView = document.getElementById('view-' + resolvedHash) || document.getElementById('view-' + hash);
            if (targetView) {
                targetViewFound = true;
                console.log('Hash/Session found, showing view:', targetView.id);
                
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
                        const onclick = link.getAttribute('onclick') || '';
                        const href = link.getAttribute('href') || '';
                        if (onclick.includes(`'${hash}'`) || onclick.includes(`'${resolvedHash}'`) || href.includes(`#${hash}`)) {
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
            if (hash === 's-chat') {
                if (typeof initChatUI === 'function') initChatUI();
                setTimeout(() => {
                    const urlParams = new URLSearchParams(rawHash.includes('?') ? rawHash.split('?')[1] : window.location.search);
                    const mentorReq = urlParams.get('mentor');
                    if (mentorReq && typeof chatWithMentorByName === 'function') {
                        chatWithMentorByName(mentorReq);
                        return;
                    }

                    const firstGroup = document.querySelector('#groups-pane .chat-group-item');
                    if (firstGroup) {
                        if (!window.activeChatId || window.activeChatType !== 'group') {
                            firstGroup.click();
                        }
                    } else {
                        // Chưa có nhóm đề tài được Khoa duyệt -> Chuyển sang tab Cá nhân trao đổi với Mentor
                        const privateTab = document.getElementById('private-tab');
                        if (privateTab) {
                            if (typeof bootstrap !== 'undefined' && bootstrap.Tab) {
                                bootstrap.Tab.getOrCreateInstance(privateTab).show();
                            } else {
                                privateTab.click();
                            }
                        }
                        if (typeof loadPrivateConversations === 'function') {
                            loadPrivateConversations().then(() => {
                                const activeItem = document.querySelector('#private-chat-list .list-group-item.active') ||
                                                   (window.activeChatId ? document.querySelector(`#private-chat-list .list-group-item[data-user-id="${window.activeChatId}"]`) : null);
                                if (!activeItem && !window.activeChatId) {
                                    const firstPrivate = document.querySelector('#private-chat-list .list-group-item');
                                    if (firstPrivate) {
                                        firstPrivate.click();
                                    }
                                }
                            });
                        }
                    }
                }, 100);
            }
            if (hash === 's-submit') {
                if (typeof window.loadSubmissionsData === 'function') {
                    window.loadSubmissionsData();
                }
            }
        }
        
        // Nếu không có hash hoặc hash không hợp lệ, chỉ xử lý ẩn/hiện nếu trang có nhiều view tabs
        if (!targetViewFound) {
            if (allViews.length > 1) {
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

            const sidebar = document.querySelector('.sidebar');
            if (sidebar) {
                const currentPath = window.location.pathname;
                const menuCategories = sidebar.querySelectorAll('.menu-category');
                let isStudent = false;
                let isLecturer = false;
                menuCategories.forEach(cat => {
                    const text = cat.textContent;
                    if (text.includes('SINH VIÊN')) isStudent = true;
                    if (text.includes('GIẢNG VIÊN')) isLecturer = true;
                });
                const roleActiveClass = isStudent ? 'active-student' : (isLecturer ? 'active-purple' : 'active-main');

                // 1. Kiểm tra xem có mục nav-link nào có href trùng khớp với URL hiện tại không
                let exactMatchingLink = null;
                if (currentPath && currentPath !== '/' && currentPath !== '') {
                    exactMatchingLink = sidebar.querySelector(`.nav-link[href="${currentPath}"]`);
                }

                if (exactMatchingLink) {
                    sidebar.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active-main', 'active-purple', 'active-student'));
                    exactMatchingLink.classList.add(roleActiveClass);
                } else {
                    // 2. Nếu không có link khớp URL, kiểm tra xem server (Jinja request.endpoint) đã set active chưa
                    const existingActive = sidebar.querySelector('.nav-link.active-main, .nav-link.active-purple, .nav-link.active-student');
                    if (!existingActive && allViews.length > 1) {
                        // Chỉ fallback về mục đầu tiên khi trang là single-page tab và chưa có mục nào active
                        const firstLink = sidebar.querySelector('.nav-link');
                        if (firstLink) {
                            firstLink.classList.add(roleActiveClass);
                        }
                    }
                }
            }
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
    
    // Tự động tìm element nếu chưa truyền
    if (!element) {
        element = document.querySelector(`.sidebar .nav-link[onclick*="'${tabName}'"]`) || 
                  document.querySelector(`.sidebar .nav-link[href*="#${tabName}"]`);
    }

    // A. Xử lý UI của thanh điều hướng (Sidebar)
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        // Remove active khỏi tất cả nav-link trong sidebar
        const allNavLinks = sidebar.querySelectorAll('.nav-link');
        allNavLinks.forEach(link => {
            link.classList.remove('active-main', 'active-purple', 'active-student');
        });
        
        // Thêm class active phù hợp cho element được click
        if (element && element.classList && element.classList.contains('nav-link')) {
            const menuCategories = sidebar.querySelectorAll('.menu-category');
            let isStudent = false;
            let isLecturer = false;
            
            menuCategories.forEach(cat => {
                const text = cat.textContent;
                if (text.includes('SINH VIÊN')) isStudent = true;
                if (text.includes('GIẢNG VIÊN')) isLecturer = true;
            });
            
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
    const allViewsInDoc = document.querySelectorAll('[id^="view-"]');
    allViewsInDoc.forEach(view => {
        view.classList.add('hidden');
        view.classList.remove('fade-in');
    });

    // C. Hiện view được chọn (hỗ trợ alias mapping tự động)
    const tabAliases = {
        'batches': 'deployment',
        'deployment': 'deployment',
        'approvals': 'approval',
        'approval': 'approval',
        'councils': 'council',
        'council': 'council',
        's-group-registration': 's-register'
    };
    if (tabName === 's-group-registration') {
        tabName = 's-register';
    }
    const resolvedTab = tabAliases[tabName] || tabName;
    let selectedView = document.getElementById('view-' + resolvedTab) || document.getElementById('view-' + tabName);
    
    if (selectedView) {
        selectedView.classList.remove('hidden');
        
        // Reset animation để chạy lại mỗi lần click
        selectedView.classList.remove('fade-in');
        void selectedView.offsetWidth; // Force reflow
        selectedView.classList.add('fade-in');

        if (tabName === 's-register' && typeof checkAndLoadMyTopic === 'function') {
            checkAndLoadMyTopic();
        }
        if (tabName === 's-mentors' && typeof hideStudentMentorDetail === 'function') {
            hideStudentMentorDetail();
        }
        if (tabName === 's-submit') {
            if (typeof window.refreshStudentViewsLive === 'function' && document.querySelector('#view-s-submit .fa-folder-open')) {
                window.refreshStudentViewsLive();
            } else if (typeof window.loadSubmissionsData === 'function') {
                window.loadSubmissionsData();
            }
        }
        if (tabName === 's-chat') {
            if (typeof window.refreshStudentViewsLive === 'function' && document.querySelector('#groups-pane .fa-users-slash')) {
                window.refreshStudentViewsLive();
            }
            if (typeof initChatUI === 'function') initChatUI();
            setTimeout(() => {
                const firstGroup = document.querySelector('#groups-pane .chat-group-item');
                if (firstGroup) {
                    if (!window.activeChatId || window.activeChatType !== 'group') {
                        firstGroup.click();
                    }
                } else {
                    // Chưa có nhóm đề tài được Khoa duyệt -> Chuyển sang tab Cá nhân trao đổi với Mentor
                    const privateTab = document.getElementById('private-tab');
                    if (privateTab) {
                        if (typeof bootstrap !== 'undefined' && bootstrap.Tab) {
                            bootstrap.Tab.getOrCreateInstance(privateTab).show();
                        } else {
                            privateTab.click();
                        }
                    }
                    if (typeof loadPrivateConversations === 'function') {
                        loadPrivateConversations().then(() => {
                            const firstPrivate = document.querySelector('#private-chat-list .list-group-item');
                            if (firstPrivate && !window.activeChatId) {
                                firstPrivate.click();
                            }
                        });
                    }
                }
            }, 80);
        }
    }

    // D. Cập nhật URL hash và sessionStorage để khi reload vẫn ở đúng tab
    try {
        history.replaceState(null, '', '#' + tabName);
        sessionStorage.setItem('active_admin_tab', tabName);
    } catch(e) {}
    
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
function showToast(message, type = 'success') {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            title: message,
            icon: type,
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 3500,
            timerProgressBar: true,
            customClass: {
                popup: 'notif-toast-custom'
            }
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

let currentTopicFilterStatus = 'all';

// Hàm lọc đề tài dùng chung cho Faculty và các trang quản lý đề tài
function filterTopics(status, btn) {
    currentTopicFilterStatus = status || 'all';

    if (btn) {
        updateFilterButtonState(btn);
    }

    applyTopicFiltering();
}

function searchTopics(query) {
    applyTopicFiltering();
}

function applyTopicFiltering() {
    const searchInput = document.getElementById('topicSearchInput');
    const query = searchInput ? searchInput.value.trim().toLowerCase() : '';
    const rows = document.querySelectorAll('tbody tr');
    let visibleCount = 0;
    let emptyRow = document.getElementById('noFilterResultsRow');

    rows.forEach(row => {
        // Bỏ qua hàng thông báo trống ban đầu nếu có
        if (row.id === 'noFilterResultsRow' || row.querySelector('td[colspan]')) return;

        let statusMatch = false;
        if (currentTopicFilterStatus === 'all') {
            statusMatch = true;
        } else if (currentTopicFilterStatus === 'faculty_pending') {
            statusMatch = row.classList.contains('status-faculty_pending') || row.classList.contains('status-pending');
        } else if (currentTopicFilterStatus === 'pending') {
            statusMatch = row.classList.contains('status-pending') || row.classList.contains('status-faculty_pending');
        } else {
            statusMatch = row.classList.contains('status-' + currentTopicFilterStatus);
        }

        let searchMatch = true;
        if (query) {
            const text = row.textContent.toLowerCase();
            searchMatch = text.includes(query);
        }

        if (statusMatch && searchMatch) {
            row.classList.remove('d-none');
            row.style.display = '';
            visibleCount++;
        } else {
            row.classList.add('d-none');
            row.style.display = 'none';
        }
    });

    const tbody = document.querySelector('tbody');
    if (tbody) {
        if (visibleCount === 0) {
            if (!emptyRow) {
                emptyRow = document.createElement('tr');
                emptyRow.id = 'noFilterResultsRow';
                emptyRow.innerHTML = '<td colspan="6" class="text-center text-muted py-4"><i class="fa-regular fa-folder-open me-2"></i>Không tìm thấy đề tài nào phù hợp</td>';
                tbody.appendChild(emptyRow);
            } else {
                emptyRow.style.display = '';
                emptyRow.classList.remove('d-none');
            }
        } else if (emptyRow) {
            emptyRow.style.display = 'none';
            emptyRow.classList.add('d-none');
        }
    }
}

// Helper: Cập nhật trạng thái active của nút lọc
function updateFilterButtonState(clickedBtn) {
    if (!clickedBtn) return;
    const container = clickedBtn.parentElement;
    const allBtns = container ? container.querySelectorAll('.btn-filter') : document.querySelectorAll('.btn-filter');

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

/**
 * 5. BỘ CÔNG CỤ SOẠN THẢO VĂN BẢN KIỂU WORD (WORD-LIKE RICH TEXT EDITOR HELPERS)
 */
window.formatWordDoc = function (cmd, value = null, targetEditorId = 'registerTopicDescEditor') {
    const editor = document.getElementById(targetEditorId);
    if (editor) editor.focus();
    document.execCommand(cmd, false, value);
    if (targetEditorId === 'submissionNotesEditor' && typeof window.syncSubmissionNotesFromEditor === 'function') {
        window.syncSubmissionNotesFromEditor();
    } else if (targetEditorId === 'feedbackTextEditor' && typeof window.syncFeedbackTextFromEditor === 'function') {
        window.syncFeedbackTextFromEditor();
    } else if (typeof window.syncTopicDescFromEditor === 'function') {
        window.syncTopicDescFromEditor();
    }
};

window.formatWordDocFontSize = function (size, targetEditorId = 'registerTopicDescEditor') {
    if (!size) return;
    const editor = document.getElementById(targetEditorId);
    if (editor) editor.focus();
    
    const selection = window.getSelection();
    if (selection && selection.rangeCount > 0 && !selection.isCollapsed) {
        const range = selection.getRangeAt(0);
        const span = document.createElement('span');
        span.style.fontSize = size;
        span.appendChild(range.extractContents());
        range.insertNode(span);
        selection.removeAllRanges();
        const newRange = document.createRange();
        newRange.selectNodeContents(span);
        selection.addRange(newRange);
    } else {
        document.execCommand('fontSize', false, '3');
    }

    if (targetEditorId === 'submissionNotesEditor' && typeof window.syncSubmissionNotesFromEditor === 'function') {
        window.syncSubmissionNotesFromEditor();
    } else if (targetEditorId === 'feedbackTextEditor' && typeof window.syncFeedbackTextFromEditor === 'function') {
        window.syncFeedbackTextFromEditor();
    } else if (typeof window.syncTopicDescFromEditor === 'function') {
        window.syncTopicDescFromEditor();
    }
};

window.formatDoc = function (cmd, value = null) {
    window.formatWordDoc(cmd, value, 'registerTopicDescEditor');
};

window.formatDocFontSize = function (size) {
    window.formatWordDocFontSize(size, 'registerTopicDescEditor');
};

document.addEventListener('keydown', function (e) {
    const active = document.activeElement;
    if (!active || !active.classList.contains('word-editor-content')) return;
    if (e.ctrlKey || e.metaKey) {
        const k = e.key.toLowerCase();
        const targetId = active.id;
        if (k === 'b') {
            e.preventDefault();
            window.formatWordDoc('bold', null, targetId);
        } else if (k === 'i') {
            e.preventDefault();
            window.formatWordDoc('italic', null, targetId);
        } else if (k === 'u') {
            e.preventDefault();
            window.formatWordDoc('underline', null, targetId);
        }
    }
});