# app.py
from flask import Flask, render_template, send_from_directory
from routes import init_routes
from routes.submissions import submissions_bp
from dotenv import load_dotenv
import os
from models import db

load_dotenv(override=True)

app = Flask(__name__)
app.secret_key = 'secret_key'
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(app.config['UPLOAD_FOLDER']): os.makedirs(app.config['UPLOAD_FOLDER'])
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 # 50MB

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

init_routes(app)

@app.route('/')
def index(): return render_template('index.html')

@app.route('/<path:filename>')
def serve_static(filename): return send_from_directory('Models', filename)

app.register_blueprint(submissions_bp)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)

from routes.documents import documents_bp

app.register_blueprint(documents_bp)

from routes.evaluation import evaluation_bp

app.register_blueprint(evaluation_bp)
from routes.progress import progress_bp

app.register_blueprint(progress_bp)

from routes.dashboard import dashboard_bp
app.register_blueprint(dashboard_bp)

from flask import Flask
from flasgger import Swagger

app = Flask(__name__)

app.config['SWAGGER'] = {
    'title': 'HOU-S-RIMS API', 
    'uiversion': 3
}
swagger = Swagger(app)
if __name__ == '__main__':
    app.run(debug=True)