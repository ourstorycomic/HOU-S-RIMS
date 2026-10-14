import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from app import app
from models import db, User, Batch, Group, Topic, GroupMember, Notification, Message

def setup_database():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database recreated.")

        u_admin = User(username="admin", password_hash=generate_password_hash("admin123"), full_name="Admin Truong HOU", email="admin@hou.edu.vn", role="admin", faculty="Phong Quan ly NCKH")
        u_faculty = User(username="faculty1", password_hash=generate_password_hash("faculty123"), full_name="PGS.TS Khoa CNTT", email="faculty@hou.edu.vn", role="faculty", faculty="Khoa CNTT")
        u_lec1  = User(username="lecturer1", password_hash=generate_password_hash("lecturer123"), full_name="TS. Nguyen Van A", email="nva@hou.edu.vn", role="Lecturer", faculty="Khoa CNTT")
        u_lec2  = User(username="lecturer2", password_hash=generate_password_hash("lecturer123"), full_name="ThS. Le Thi B", email="ltb@hou.edu.vn", role="Lecturer", faculty="Khoa Luat")
        u_sv1   = User(username="student1", password_hash=generate_password_hash("student123"), full_name="Tran Minh Tuan", email="tmt@hou.edu.vn", role="student", student_id="21010001", faculty="Khoa CNTT")
        u_sv2   = User(username="student2", password_hash=generate_password_hash("student123"), full_name="Nguyen Van Hoc", email="nvh@hou.edu.vn", role="student", student_id="21010042", faculty="Khoa CNTT")
        u_sv3   = User(username="student3", password_hash=generate_password_hash("student123"), full_name="Le Thi Lan", email="ltlan@hou.edu.vn", role="student", student_id="21010043", faculty="Khoa CNTT")
        db.session.add_all([u_admin, u_faculty, u_lec1, u_lec2, u_sv1, u_sv2, u_sv3])
        db.session.commit()

if __name__ == "__main__":
    setup_database()
