import sys
sys.path.insert(0, '.')
from app import app
from API.routes.notifications import sync_notifications
from flask import session

with app.test_request_context():
    session['user_id'] = 5
    resp = sync_notifications()
    # sync_notifications returns (jsonify, 200) or jsonify
    if isinstance(resp, tuple):
        data = resp[0].get_json()
        code = resp[1]
    else:
        data = resp.get_json()
        code = 200
    print("Code:", code)
    print("Badge count:", data.get('total_badge_count'))
    print("Invitations returned:", len(data.get('invitations', [])))
    for inv in data.get('invitations', []):
        print("  Inv:", inv)
    print("Notifications returned:", len(data.get('notifications', [])))
    for n in data.get('notifications', [])[:6]:
        print(f"  ID: {n['id']} | Read: {n['is_read']} | Time: {n['created_at']}")
        clean = n['content'].replace('\n', ' ')
        print(f"     {clean[:80]}...")
