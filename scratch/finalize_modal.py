with open('static/assets/js/app.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Add window._isReadingNotifModal in readNotification
part_old = """    const isFromAll = Boolean(fromAll);
    const htmlModal = buildModernNotificationHtml(id, content, isFromAll);

    Swal.fire({
        html: htmlModal,
        showConfirmButton: false,
        showCloseButton: false,
        width: 580,
        padding: '0',
        background: '#ffffff',
        customClass: {
            popup: 'rounded-4 shadow-lg border-0 overflow-hidden p-0'
        }
    }).then(() => {
        if (typeof _refreshNotifBadge === 'function') {
            _refreshNotifBadge();
        }
    });"""

part_new = """    const isFromAll = Boolean(fromAll);
    const htmlModal = buildModernNotificationHtml(id, content, isFromAll);

    window._isReadingNotifModal = true;
    Swal.fire({
        html: htmlModal,
        showConfirmButton: false,
        showCloseButton: false,
        width: 580,
        padding: '0',
        background: '#ffffff',
        allowOutsideClick: true,
        customClass: {
            popup: 'rounded-4 shadow-lg border-0 overflow-hidden p-0'
        }
    }).then(() => {
        window._isReadingNotifModal = false;
        if (typeof _refreshNotifBadge === 'function') {
            _refreshNotifBadge();
        }
    });"""

text = text.replace(part_old, part_new)

with open('static/assets/js/app.js', 'w', encoding='utf-8') as f:
    f.write(text)

print("SUCCESS: Modal persistence finalized in app.js!")

