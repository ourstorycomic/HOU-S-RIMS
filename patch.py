import sys
content = open('app.py', 'r', encoding='utf-8').read()
new_route = '''
@app.route('/profile/<int:user_id>')
def view_profile(user_id):
    from flask import session, redirect, url_for, render_template
    from models import User
    if not session.get('user_id'): return redirect(url_for('auth.login'))
    user = User.query.get_or_404(user_id)
    return render_template('profile.html', profile_user=user)

@app.route('/<path:filename>')
'''
content = content.replace("@app.route('/<path:filename>')", new_route)
open('app.py', 'w', encoding='utf-8').write(content)
