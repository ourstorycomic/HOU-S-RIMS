// static/assets/js/chat.js
// ============================================================
// HOU S-RIMS - Chat Module (fully dynamic, no hardcoded data)
// ============================================================

let chatPollInterval = null;
let activeChatId = null;
let activeChatType = "group";
let lastMessageCount = 0;
let pendingUploadFile = null;

// Get current user ID embedded by Jinja in the page via meta tag
function getCurrentUserId() {
    const meta = document.querySelector('meta[name="current-user-id"]');
    return meta ? parseInt(meta.getAttribute('content')) : null;
}

function startChatPolling(groupId) {
    if (!groupId) return; // Never poll without a valid group
    activeChatId = groupId;
    lastMessageCount = -1; // Reset so messages re-render on group switch
    if (document.getElementById('chat-sidebar')?.classList.contains('active')) {
        fetchChatMedia();
    }

    if (chatPollInterval) clearInterval(chatPollInterval);

    fetchChatMessages();
    chatPollInterval = setInterval(fetchChatMessages, 3000);
}

function stopChatPolling() {
    if (chatPollInterval) {
        clearInterval(chatPollInterval);
        chatPollInterval = null;
    }
    activeChatId = null;
}

let currentSearchQuery = '';
async function fetchChatMessages() {
    if (!activeChatId) return;

    try {
        const endpoint = activeChatType === "group" ? activeChatType === "group" ? `/api/chat/${activeChatId}/messages` : `/api/chat/private/${activeChatId}/messages` : `/api/chat/private/${activeChatId}/messages`;
        const response = await fetch(endpoint);
        if (!response.ok) return;

        const messages = await response.json();

        if (messages.length !== lastMessageCount) {
            renderChatMessages(messages);
            lastMessageCount = messages.length;
            if (activeChatType === 'private') {
                fetchPrivateConversations();
            }
        }
    } catch (error) {
        console.error('Error fetching chat messages:', error);
    }
}

function renderChatMessages(messages) {
    const container = document.getElementById('chat-messages-container');
    if (!container) return;

    const myUserId = getCurrentUserId();

    if (!messages || messages.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5 text-muted">
                <i class="fa-regular fa-comment-dots fs-1 mb-3 d-block opacity-25"></i>
                <div class="small fw-bold">Chưa có tin nhắn nào</div>
                <div class="small">Hãy bắt đầu cuộc trò chuyện!</div>
            </div>`;
        return;
    }

    container.innerHTML = '';

    let lastDate = null;

    messages.forEach(msg => {
        // msg.timestamp is expected to be "HH:MM DD/MM/YYYY"
        const parts = msg.timestamp.split(' ');
        const timeStr = parts[0];
        const dateStr = parts.length > 1 ? parts[1] : 'Hôm nay';
        
        if (dateStr !== lastDate) {
            const dateDivider = document.createElement('div');
            dateDivider.className = 'w-100 text-center mb-4';
            dateDivider.innerHTML = `<span class="small text-muted fw-bold bg-light d-inline-block px-3 py-1 rounded-pill">${dateStr}</span>`;
            container.appendChild(dateDivider);
            lastDate = dateStr;
        }
        const isMe = myUserId ? (msg.sender_id === myUserId) : false;
        const bubbleWrap = document.createElement('div');
        
        let contentHtml = msg.content;
        
        let isSticker = false;
        // Render different media types
        if (msg.message_type === 'image' && msg.file_url) {
            contentHtml = `<div>${msg.content}</div><img src="${msg.file_url}" class="img-fluid rounded mt-2" style="max-height: 200px; cursor: pointer;" onclick="window.open('${msg.file_url}')">`;
        } else if (msg.message_type === 'video' && msg.file_url) {
            contentHtml = `<div>${msg.content}</div><video src="${msg.file_url}" controls class="w-100 rounded mt-2" style="max-height: 250px;"></video>`;
        } else if (msg.message_type === 'file' && msg.file_url) {
            contentHtml = `<div>${msg.content}</div><div class="mt-2 p-2 bg-light rounded text-dark d-flex align-items-center"><i class="fa-solid fa-file me-2 fs-3 text-primary"></i> <a href="${msg.file_url}" target="_blank" class="text-truncate" style="max-width:150px;">${msg.file_name || 'Tài liệu'}</a></div>`;
        } else if (msg.message_type === 'sticker' && msg.file_url) {
            contentHtml = `<img src="${msg.file_url}" class="img-fluid" style="width: 120px; height: 120px; object-fit: contain;">`;
            isSticker = true;
        }

        if (isMe) {
            bubbleWrap.className = 'd-flex gap-3 mb-4 flex-row-reverse ';
            const bubbleBg = isSticker ? 'bg-transparent' : 'bg-primary text-white shadow-sm';
            const styleAttr = isSticker ? '' : 'style="background-color:#6366f1!important; word-break: break-word;"';
            
            bubbleWrap.innerHTML = `
                <div style="max-width: 70%;">
                    <div class="text-end"><small class="text-muted fw-bold me-1">Bạn - ${timeStr}</small></div>
                    <div class="mt-1 text-start p-3 rounded-3 chat-bubble-content ${bubbleBg}" ${styleAttr}>
                        ${contentHtml}
                    </div>
                </div>
            `;
        } else {
            const isLecturerMsg = msg.sender_role === 'Lecturer';
            const roleColor = isLecturerMsg ? 'bg-danger' : 'bg-secondary';
            const shortName = (msg.sender_name || '?').substring(0, 2).toUpperCase();

            bubbleWrap.className = 'd-flex gap-3 mb-4 ';
            const bubbleBg = isSticker ? 'bg-transparent' : 'bg-white shadow-sm border';
            
            bubbleWrap.innerHTML = `
                <div class="${roleColor} text-white rounded-circle d-flex align-items-center justify-content-center fw-bold flex-shrink-0 cursor-pointer" style="width:35px;height:35px;" onclick="startPrivateChat(${msg.sender_id}, '${msg.sender_name}')">${shortName}</div>
                <div style="max-width: 75%;">
                    <small class="text-muted fw-bold ms-1 text-uppercase" style="font-size:11px;">${msg.sender_name} - ${timeStr}</small>
                    <div class="mt-1 p-3 rounded-3 chat-bubble-content ${bubbleBg}" style="word-break: break-word;">${contentHtml}</div>
                </div>
            `;
        }
        container.appendChild(bubbleWrap);
    });

    container.scrollTop = container.scrollHeight;
}

function cancelChatUpload() {
    pendingUploadFile = null;
    const fileInput = document.getElementById('chat-file-input');
    if (fileInput) fileInput.value = '';
    const preview = document.getElementById('chat-upload-preview');
    if (preview) preview.classList.add('d-none');
}

async function sendChatMessage(groupId) {
    const targetGroup = groupId || activeChatId;
    if (!targetGroup) {
        Swal.fire('Chưa chọn nhóm', 'Vui lòng chọn nhóm chat trước khi gửi.', 'warning');
        return;
    }

    const inputField = document.getElementById('chat-input-field');
    const content = (inputField ? inputField.value : '').trim();
    
    if (!content && !pendingUploadFile) return;

    // Determine message type
    let messageType = 'text';
    let fileUrl = null;
    let fileName = null;

    if (pendingUploadFile) {
        // Upload the file first
        const formData = new FormData();
        formData.append('file', pendingUploadFile);

        try {
            const uploadRes = await fetch(activeChatType === "group" ? `/api/chat/${targetGroup}/upload` : `/api/chat/private/${targetGroup}/upload`, {
                method: 'POST',
                body: formData
            });

            if (!uploadRes.ok) {
                const err = await uploadRes.json();
                Swal.fire('Lỗi upload', err.error || 'Lỗi khi tải file lên', 'error');
                return;
            }

            const uploadData = await uploadRes.json();
            fileUrl = uploadData.file_url;
            fileName = uploadData.file_name;

            // detect type
            const ext = fileName.split('.').pop().toLowerCase();
            if (['jpg','jpeg','png','gif','webp'].includes(ext)) {
                messageType = 'image';
            } else if (['mp4','webm','ogg'].includes(ext)) {
                messageType = 'video';
            } else {
                messageType = 'file';
            }
        } catch (error) {
            console.error('Error uploading file:', error);
            Swal.fire('Lỗi upload', 'Lỗi kết nối khi tải file lên', 'error');
            return;
        }
    }

    // Clear UI early for better UX
    if (inputField) inputField.value = '';
    cancelChatUpload();

    try {
        const response = await fetch(activeChatType === "group" ? `/api/chat/${targetGroup}/messages` : `/api/chat/private/${targetGroup}/messages`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                content: content,
                message_type: messageType,
                file_url: fileUrl,
                file_name: fileName
            })
        });

        if (response.ok) {
            fetchChatMessages();
        } else {
            const err = await response.json();
            Swal.fire('Lỗi', err.error || 'Không gửi được tin nhắn', 'error');
        }
    } catch (error) {
        console.error('Error sending message:', error);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    var inputField = document.getElementById('chat-input-field');
    if (inputField) {
        inputField.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                var btn = document.getElementById('chat-send-btn');
                if (btn) btn.click();
            }
        });
    }

    // File input handler
    const fileInput = document.getElementById('chat-file-input');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                pendingUploadFile = e.target.files[0];
                const preview = document.getElementById('chat-upload-preview');
                const previewName = document.getElementById('chat-preview-name');
                const previewIcon = document.getElementById('chat-preview-icon');
                
                if (preview && previewName && previewIcon) {
                    previewName.textContent = pendingUploadFile.name;
                    // change icon based on file type
                    const ext = pendingUploadFile.name.split('.').pop().toLowerCase();
                    if (['jpg','jpeg','png','gif','webp'].includes(ext)) {
                        previewIcon.innerHTML = '<i class="fa-regular fa-image"></i>';
                    } else if (['mp4','webm','ogg'].includes(ext)) {
                        previewIcon.innerHTML = '<i class="fa-solid fa-film"></i>';
                    } else {
                        previewIcon.innerHTML = '<i class="fa-solid fa-file"></i>';
                    }
                    
                    preview.classList.remove('d-none');
                }
            }
        });
    }

    // Emoji and Sticker picker handlers
    const emojiBtn = document.getElementById('emoji-picker-btn');
    const emojiContainer = document.getElementById('emoji-picker-container');
    
    if (emojiBtn && emojiContainer) {
        emojiBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            emojiContainer.classList.toggle('d-none');
        });
        
        // Tab switching
        const tabs = emojiContainer.querySelectorAll('.picker-tab');
        const tabContents = emojiContainer.querySelectorAll('.picker-tab-content');
        
        tabs.forEach(tab => {
            tab.addEventListener('click', function(e) {
                e.stopPropagation();
                // Remove active from all tabs
                tabs.forEach(t => t.classList.remove('active'));
                tabContents.forEach(c => c.classList.add('d-none'));
                
                // Add active to clicked
                this.classList.add('active');
                const targetId = this.getAttribute('data-target');
                const targetContent = document.getElementById(targetId);
                if (targetContent) targetContent.classList.remove('d-none');
            });
        });
        
        // Add emoji to input
        const emojis = emojiContainer.querySelectorAll('.emoji-item');
        emojis.forEach(item => {
            item.addEventListener('click', function(e) {
                e.stopPropagation();
                const emoji = this.textContent;
                if (inputField) {
                    inputField.value += emoji;
                    inputField.focus();
                }
            });
        });
        
        // Send sticker
        const stickers = emojiContainer.querySelectorAll('.sticker-item');
        stickers.forEach(item => {
            item.addEventListener('click', async function(e) {
                e.stopPropagation();
                emojiContainer.classList.add('d-none');
                
                const stickerUrl = this.getAttribute('data-url');
                if (!stickerUrl || !activeChatId) return;
                
                // Send sticker directly
                try {
                    const response = await fetch(activeChatType === "group" ? `/api/chat/${activeChatId}/messages` : `/api/chat/private/${activeChatId}/messages`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 
                            content: 'Đã gửi một nhãn dán',
                            message_type: 'sticker',
                            file_url: stickerUrl,
                            file_name: 'sticker.png'
                        })
                    });

                    if (response.ok) {
                        fetchChatMessages();
                    }
                } catch (error) {
                    console.error('Error sending sticker:', error);
                }
            });
        });
        
        // Close when clicking outside
        document.addEventListener('click', function(e) {
            if (!emojiContainer.contains(e.target) && e.target !== emojiBtn) {
                emojiContainer.classList.add('d-none');
            }
        });
    }

    // Auto-start polling is disabled on page load — user must click a group
    window.addEventListener('beforeunload', stopChatPolling);
});

function updateChatHeader(chatName, chatId, chatType="group") {
    activeChatType = chatType;
    var headerName = document.getElementById('chat-header-name');
    var headerAvatar = document.getElementById('chat-header-avatar');
    if (headerName) headerName.textContent = chatName;
    if (headerAvatar) {
        headerAvatar.innerHTML = chatType === 'group' ? '<i class="fa-solid fa-users"></i>' : '<i class="fa-solid fa-user"></i>';
    }
    
    // Switch UI tab based on type
    const tabId = chatType === 'group' ? 'groups-tab' : 'private-tab';
    const tabBtn = document.getElementById(tabId);
    if(tabBtn) {
        const bsTab = new bootstrap.Tab(tabBtn);
        bsTab.show();
    }
    
    startChatPolling(chatId);
}

function startPrivateChat(userId, userName) {
    updateChatHeader(userName, userId, "private");
}


// Search toggle and debounce
const chatSearchBtn = document.getElementById('chat-search-btn');
const chatSearchContainer = document.getElementById('chat-search-container');
const chatSearchInput = document.getElementById('chat-search-input');

if (chatSearchBtn && chatSearchContainer && chatSearchInput) {
    chatSearchBtn.addEventListener('click', () => {
        const isClosed = chatSearchContainer.style.width === '0px' || chatSearchContainer.style.width === '';
        if (isClosed) {
            chatSearchContainer.style.width = '250px';
            chatSearchContainer.style.opacity = '1';
            setTimeout(() => chatSearchInput.focus(), 300);
        } else {
            chatSearchContainer.style.width = '0px';
            chatSearchContainer.style.opacity = '0';
            chatSearchInput.value = '';
            
            const bubbles = document.querySelectorAll('.chat-bubble-content');
            bubbles.forEach(el => {
                if (el.dataset.originalBg) {
                    el.style.backgroundColor = el.dataset.originalBg;
                    el.style.color = el.dataset.originalColor;
                    el.dataset.originalBg = '';
                }
            });
            const container = document.getElementById('chat-messages-container');
            if (container) container.scrollTop = container.scrollHeight;
        }
    });


    let searchTimeout = null;
    chatSearchInput.addEventListener('input', (e) => {
        if (searchTimeout) clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            const query = e.target.value.trim().toLowerCase();
            const bubbles = document.querySelectorAll('.chat-bubble-content');
            let firstMatch = null;
            
            bubbles.forEach(el => {
                // Restore original if we modified it before
                if (el.dataset.originalBg) {
                    el.style.backgroundColor = el.dataset.originalBg;
                    el.style.color = el.dataset.originalColor;
                    el.dataset.originalBg = '';
                }
                
                if (query && el.textContent.toLowerCase().includes(query)) {
                    if (!firstMatch) firstMatch = el;
                    el.dataset.originalBg = el.style.backgroundColor || '';
                    el.dataset.originalColor = el.style.color || '';
                    el.style.backgroundColor = '#ffeb3b';
                    el.style.color = '#000';
                }
            });
            
            if (firstMatch) {
                firstMatch.scrollIntoView({behavior: 'smooth', block: 'center'});
            }
        }, 300);
    });

}

// Sidebar toggle logic
const chatInfoBtn = document.getElementById('chat-info-btn');
const chatSidebar = document.getElementById('chat-sidebar');
const mainChatArea = document.getElementById('main-chat-area');

if (chatInfoBtn && chatSidebar && mainChatArea) {
    chatInfoBtn.addEventListener('click', () => {
        chatSidebar.classList.toggle('active');
        if (chatSidebar.classList.contains('active')) {
            // Adjust columns if needed
            if (mainChatArea.classList.contains('col-md-9')) {
                mainChatArea.classList.replace('col-md-9', 'col-md-6');
            } else if (mainChatArea.classList.contains('col-md-8')) {
                mainChatArea.classList.replace('col-md-8', 'col-md-5');
            }
            if (activeChatId) fetchChatMedia();
        } else {
            if (mainChatArea.classList.contains('col-md-6')) {
                mainChatArea.classList.replace('col-md-6', 'col-md-9');
            } else if (mainChatArea.classList.contains('col-md-5')) {
                mainChatArea.classList.replace('col-md-5', 'col-md-8');
            }
        }
    });
}

async function fetchChatMedia() {
    if (!activeChatId) return;
    try {
        const endpoint = activeChatType === "group" ? `/api/chat/${activeChatId}/media` : `/api/chat/private/${activeChatId}/media`;
        const response = await fetch(endpoint);
        if (!response.ok) return;
        const data = await response.json();
        
        // Populate media grid
        const mediaGrid = document.getElementById('sidebar-media-grid');
        if (mediaGrid) {
            if (data.images_videos.length === 0) {
                mediaGrid.innerHTML = '<div class="text-muted small text-center w-100 py-3">Không có ảnh/video</div>';
            } else {
                mediaGrid.innerHTML = data.images_videos.map(m => {
                    if (m.type === 'video') {
                        return `<video src="${m.url}" class="media-item" onclick="window.open('${m.url}')"></video>`;
                    } else {
                        return `<img src="${m.url}" class="media-item" onclick="window.open('${m.url}')">`;
                    }
                }).join('');
            }
        }

        // Populate files
        const fileList = document.getElementById('sidebar-file-list');
        if (fileList) {
            if (data.files.length === 0) {
                fileList.innerHTML = '<div class="text-muted small text-center w-100 py-3">Không có file</div>';
            } else {
                fileList.innerHTML = data.files.map(f => `
                    <div class="file-list-item">
                        <i class="fa-solid fa-file text-primary fs-4 me-3"></i>
                        <div class="overflow-hidden">
                            <div class="text-truncate text-dark fw-bold" style="font-size:13px;"><a href="${f.url}" target="_blank" class="text-dark text-decoration-none">${f.name}</a></div>
                            <small class="text-muted">${f.timestamp}</small>
                        </div>
                    </div>
                `).join('');
            }
        }

        // Populate links
        const linkList = document.getElementById('sidebar-link-list');
        if (linkList) {
            if (data.links.length === 0) {
                linkList.innerHTML = '<div class="text-muted small text-center w-100 py-3">Không có link</div>';
            } else {
                linkList.innerHTML = data.links.map(l => `
                    <div class="link-list-item">
                        <a href="${l.url}" target="_blank" class="text-primary text-truncate d-block small">${l.url}</a>
                        <small class="text-muted">${l.timestamp}</small>
                    </div>
                `).join('');
            }
        }
    } catch (e) {
        console.error('Error fetching media:', e);
    }
}

function startPrivateChat(userId, userName) {
    const myUserId = getCurrentUserId();
    if (userId === myUserId) return; // Can't chat with self
    
    activeChatType = "private";
    startChatPolling(userId);
    
    // Switch UI to private tab
    const privateTabBtn = document.getElementById('private-tab');
    if(privateTabBtn) {
        const bsTab = new bootstrap.Tab(privateTabBtn);
        bsTab.show();
    }
    
    // Update Header
    document.getElementById('chat-header-name').textContent = userName;
    document.getElementById('chat-header-name').nextElementSibling.textContent = 'Trò chuyện riêng';
    document.getElementById('chat-header-avatar').innerHTML = '<i class="fa-solid fa-user"></i>';
    
    fetchPrivateConversations();
}

// User Search Autocomplete
const userSearchInput = document.getElementById('user-search-input');
const userSearchDropdown = document.getElementById('user-search-dropdown');
let userSearchTimeout = null;

if (userSearchInput && userSearchDropdown) {
    userSearchInput.addEventListener('input', (e) => {
        const q = e.target.value.trim();
        if (!q) {
            userSearchDropdown.classList.remove('show');
            return;
        }
        
        if (userSearchTimeout) clearTimeout(userSearchTimeout);
        userSearchTimeout = setTimeout(async () => {
            try {
                const res = await fetch(`/api/chat/users/search?q=${encodeURIComponent(q)}`);
                const users = await res.json();
                if (users.length === 0) {
                    userSearchDropdown.innerHTML = '<div class="px-3 py-2 text-muted small">Không tìm thấy kết quả</div>';
                } else {
                    userSearchDropdown.innerHTML = users.map(u => `
                        <a href="javascript:void(0)" class="dropdown-item py-2 border-bottom" onclick="startPrivateChat(${u.id}, '${u.name}'); document.getElementById('user-search-input').value=''; document.getElementById('user-search-dropdown').classList.remove('show');">
                            <div class="fw-bold">${u.name}</div>
                            <small class="text-muted">${u.code} - ${u.role}</small>
                        </a>
                    `).join('');
                }
                userSearchDropdown.classList.add('show');
            } catch (err) {
                console.error(err);
            }
        }, 300);
    });
    
    // Hide dropdown on click outside
    document.addEventListener('click', (e) => {
        if (!userSearchInput.contains(e.target) && !userSearchDropdown.contains(e.target)) {
            userSearchDropdown.classList.remove('show');
        }
    });
}

async function fetchPrivateConversations() {
    const list = document.getElementById('private-chat-list');
    if (!list) return;
    
    try {
        const res = await fetch('/api/chat/private/conversations');
        const data = await res.json();
        
        if (data.length === 0) {
            list.innerHTML = '<div class="text-center text-muted p-4 small">Chưa có tin nhắn riêng nào</div>';
            return;
        }
        
        list.innerHTML = data.map(c => `
            <a href="javascript:void(0)" class="list-group-item list-group-item-action py-3 border-0 border-bottom" onclick="startPrivateChat(${c.id}, '${c.name}')">
                <div class="d-flex w-100 justify-content-between align-items-center">
                    <div class="d-flex align-items-center gap-3">
                        <div class="bg-secondary text-white rounded-circle d-flex align-items-center justify-content-center fw-bold" style="width: 45px; height: 45px;">
                            ${c.name.substring(0, 2).toUpperCase()}
                        </div>
                        <div>
                            <h6 class="mb-1 fw-bold text-dark" style="font-size: 15px;">${c.name}</h6>
                            <small class="text-muted text-truncate d-inline-block" style="max-width: 150px;">${c.last_message}</small>
                        </div>
                    </div>
                    <small class="text-muted" style="font-size: 11px;">${c.timestamp}</small>
                </div>
            </a>
        `).join('');
        
    } catch (err) {
        console.error(err);
    }
}

// Fetch on load if tabs exist
const privateTabBtn = document.getElementById('private-tab');
if (privateTabBtn) {
    privateTabBtn.addEventListener('shown.bs.tab', fetchPrivateConversations);
}


