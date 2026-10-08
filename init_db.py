from app import app
from models import db, User

with app.app_context():
    db.create_all()
    # Check if admin user exists
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password='admin123', # In a real app, hash this using werkzeug.security!
            name='Administrator',
            role='admin'
        )
        mentor = User(
            username='mentor1',
            password='mentor123',
            name='Nguyễn Văn Mentor',
            role='lecturer'
        )
        student = User(
            username='student1',
            password='student123',
            name='Lê Thị Sinh Viên',
            role='student'
        )
        db.session.add_all([admin, mentor, student])
        db.session.commit()
        print("Database initialized and mock users (Admin, Mentor, Student) created.")
    else:
        print("Database already initialized.")
