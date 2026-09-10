# app.py
from flask import Flask, render_template, send_from_directory
from routes import init_routes
from dotenv import load_dotenv
import os
from models import db
from flask_jwt_extended import JWTManager

load_dotenv(override=True)

app = Flask(__name__)
app.secret_key = 'secret_key'
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(app.config['UPLOAD_FOLDER']): os.makedirs(app.config['UPLOAD_FOLDER'])
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 # 50MB

# Cấu hình Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Cấu hình JWT
app.config['JWT_SECRET_KEY'] = 'super-secret-jwt-key' # Nên thay đổi trong thực tế
jwt = JWTManager(app)

db.init_app(app)

with app.app_context():
    db.create_all()

init_routes(app)

@app.route('/')
def index(): return render_template('index.html')

@app.route('/<path:filename>')
def serve_static(filename): return send_from_directory('Models', filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)