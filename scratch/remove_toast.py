with open('static/assets/js/app.js', 'r', encoding='utf-8') as f:
    text = f.read()

old_block = """        // 2. Check for newly arrived notifications to show live popup toast
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
        window._notifInitDone = true;"""

new_block = """        // 2. Cập nhật cache thông báo toàn cục (không tự ý bắn toast đè mất modal của người dùng)
        if (data.notifications && data.notifications.length > 0) {
            window._allNotifications = window._allNotifications || {};
            data.notifications.forEach(n => {
                window._allNotifications[n.id] = n.content;
                if (window._seenNotifIds) {
                    window._seenNotifIds.add(n.id);
                }
            });
        }
        window._notifInitDone = true;"""

# Normalize CRLF / LF for matching
text_normalized = text.replace('\r\n', '\n')
old_block_normalized = old_block.replace('\r\n', '\n')
new_block_normalized = new_block.replace('\r\n', '\n')

if old_block_normalized in text_normalized:
    text_normalized = text_normalized.replace(old_block_normalized, new_block_normalized)
    with open('static/assets/js/app.js', 'w', encoding='utf-8') as f:
        f.write(text_normalized)
    print("SUCCESS: Removed auto-toast popup from syncNotificationsLive!")
else:
    print("ERROR: old_block_normalized not found in text_normalized")

