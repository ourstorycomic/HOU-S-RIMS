import sys
content = open('app.py', 'r', encoding='utf-8').read()
new_route = '''
@app.route('/profile/<string:identifier>')
def view_profile(identifier):
    from flask import session, redirect, url_for, render_template
    from models import User, Skill, Achievement, Experience, Topic
    if not session.get('user_id'): return redirect(url_for('auth.login'))
    
    # Try to find by student_id first, then by username, then by ID as string
    user = User.query.filter((User.student_id == identifier) | (User.username == identifier) | (User.id == identifier)).first_or_404()
    
    # Get portfolio data if student
    skills = Skill.query.filter_by(student_id=user.id).all() if user.role == 'student' else []
    achievements = Achievement.query.filter_by(student_id=user.id).all() if user.role == 'student' else []
    experiences = Experience.query.filter_by(student_id=user.id).all() if user.role == 'student' else []
    
    return render_template('profile.html', profile_user=user, skills=skills, achievements=achievements, experiences=experiences)

@app.route('/<path:filename>')
'''
content = content.replace("@app.route('/profile/<int:user_id>')\ndef view_profile(user_id):\n    from flask import session, redirect, url_for, render_template\n    from models import User\n    if not session.get('user_id'): return redirect(url_for('auth.login'))\n    user = User.query.get_or_404(user_id)\n    return render_template('profile.html', profile_user=user)\n\n@app.route('/<path:filename>')", new_route)
open('app.py', 'w', encoding='utf-8').write(content)
