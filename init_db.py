from app import app
from models import db, User

with app.app_context():
    db.create_all()
    # Check if admin user exists
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password_hash='admin123', # In a real app, hash this using werkzeug.security!
            full_name='Administrator',
            email='admin@example.com',
            role='Admin'
        )
        mentor = User(
            username='mentor1',
            password_hash='mentor123',
            full_name='Nguyễn Văn Mentor',
            email='mentor@example.com',
            role='Mentor'
        )
        student = User(
            username='student1',
            password_hash='student123',
            full_name='Lê Thị Sinh Viên',
            email='student@example.com',
            role='Student'
        )
        db.session.add_all([admin, mentor, student])
        db.session.commit()
        print("Database initialized and mock users (Admin, Mentor, Student) created.")
    else:
        print("Database already initialized.")
