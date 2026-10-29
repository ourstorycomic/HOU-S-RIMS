# 1. Update API/routes/notifications.py
with open('API/routes/notifications.py', 'r', encoding='utf-8') as f:
    api_notifs = f.read()

# Change sorting in get_notifications
api_notifs = api_notifs.replace(
    "notifs = Notification.query.filter_by(user_id=user_id).order_by(Notification.is_read.asc(), Notification.created_at.desc()).all()",
    "notifs = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()"
)

# Change sorting in sync_notifications
api_notifs = api_notifs.replace(
    "notifs = Notification.query.filter_by(user_id=user_id).order_by(\n        Notification.is_read.asc(), Notification.created_at.desc()\n    ).limit(30).all()",
    "notifs = Notification.query.filter_by(user_id=user_id).order_by(\n        Notification.created_at.desc()\n    ).limit(30).all()"
)

# Change received_invitations to only include pending/invited
old_inv_block = """    memberships = GroupMember.query.filter_by(student_id=user_id).all()
    for m in memberships:
        if m.group and m.group.leader_id != user_id:"""

new_inv_block = """    memberships = GroupMember.query.filter_by(student_id=user_id).all()
    for m in memberships:
        if m.group and m.group.leader_id != user_id and m.status in ['pending', 'invited']:"""

api_notifs = api_notifs.replace(old_inv_block, new_inv_block)

with open('API/routes/notifications.py', 'w', encoding='utf-8') as f:
    f.write(api_notifs)
print("Updated API/routes/notifications.py")

# 2. Update routes/student_bp.py
with open('routes/student_bp.py', 'r', encoding='utf-8') as f:
    s_bp = f.read()
s_bp = s_bp.replace(
    "Notification.query.filter_by(user_id=user_id).order_by(Notification.is_read.asc(), Notification.created_at.desc()).all()",
    "Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()"
)
with open('routes/student_bp.py', 'w', encoding='utf-8') as f:
    f.write(s_bp)
print("Updated routes/student_bp.py")

# 3. Update routes/faculty_bp.py
with open('routes/faculty_bp.py', 'r', encoding='utf-8') as f:
    f_bp = f.read()
f_bp = f_bp.replace(
    "Notification.query.filter_by(user_id=user_id).order_by(Notification.is_read.asc(), Notification.created_at.desc()).all()",
    "Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()"
)
with open('routes/faculty_bp.py', 'w', encoding='utf-8') as f:
    f.write(f_bp)
print("Updated routes/faculty_bp.py")

# 4. Update routes/web.py
with open('routes/web.py', 'r', encoding='utf-8') as f:
    w_bp = f.read()
w_bp = w_bp.replace(
    "Notification.query.filter_by(user_id=user_id).order_by(Notification.is_read.asc(), Notification.created_at.desc()).all()",
    "Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()"
)
with open('routes/web.py', 'w', encoding='utf-8') as f:
    f.write(w_bp)
print("Updated routes/web.py")

# 5. Update templates/student.html & templates/layouts/student_layout.html
for tpath in ['templates/student.html', 'templates/layouts/student_layout.html']:
    with open(tpath, 'r', encoding='utf-8') as f:
        thtml = f.read()
    
    old_tpl_inv = "{% for inv in received_invitations %}\n                    {% set topic = inv.group.topics[0] if inv.group and inv.group.topics else None %}\n                    {% set is_pending = inv.status in ['pending', 'invited'] %}"
    new_tpl_inv = "{% for inv in received_invitations if inv.status in ['pending', 'invited'] %}\n                    {% set topic = inv.group.topics[0] if inv.group and inv.group.topics else None %}\n                    {% set is_pending = true %}"
    
    if old_tpl_inv in thtml:
        thtml = thtml.replace(old_tpl_inv, new_tpl_inv)
        with open(tpath, 'w', encoding='utf-8') as f:
            f.write(thtml)
        print(f"Updated {tpath}")
    else:
        # try CRLF or check alternative
        thtml = thtml.replace("{% for inv in received_invitations %}", "{% for inv in received_invitations if inv.status in ['pending', 'invited'] %}")
        with open(tpath, 'w', encoding='utf-8') as f:
            f.write(thtml)
        print(f"Updated {tpath} (generic replace)")

# 6. Update static/assets/js/app.js to only render pending invitations
with open('static/assets/js/app.js', 'r', encoding='utf-8') as f:
    js_code = f.read()

old_js_inv = """            // Render invitations
            if (data.invitations && data.invitations.length > 0) {
                data.invitations.forEach(inv => {
                    const isPending = inv.status === 'pending' || inv.status === 'invited';"""

new_js_inv = """            // Render invitations (Chỉ hiển thị lời mời đang chờ phản hồi - pending)
            if (data.invitations && data.invitations.length > 0) {
                data.invitations.forEach(inv => {
                    const isPending = inv.status === 'pending' || inv.status === 'invited';
                    if (!isPending) return;"""

if old_js_inv in js_code:
    js_code = js_code.replace(old_js_inv, new_js_inv)
    with open('static/assets/js/app.js', 'w', encoding='utf-8') as f:
        f.write(js_code)
    print("Updated static/assets/js/app.js")
else:
    print("Warning: old_js_inv pattern not found in app.js")

print("ALL UPDATES COMPLETED!")

