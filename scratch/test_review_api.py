import sys
sys.path.insert(0, '.')
from app import app
from flask import session

with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['user_id'] = 19 # TS. Ngô Thị Bích Loan
        sess['role'] = 'lecturer'
        sess['full_name'] = 'TS. Ngô Thị Bích Loan'

    resp = client.post('/api/submissions/24/review', json={
        'status': 'approved',
        'feedback': 'dfere'
    })
    print("Response Status:", resp.status_code)
    print("Response Data:", resp.get_json())

