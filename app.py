# app.py
from flask import Flask, render_template, send_from_directory
from routes import init_routes
from routes.submissions import submissions_bp
from dotenv import load_dotenv
import os

load_dotenv(override=True)

app = Flask(__name__)
app.secret_key = 'secret_key'
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(app.config['UPLOAD_FOLDER']): os.makedirs(app.config['UPLOAD_FOLDER'])
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 # 50MB

init_routes(app)

@app.route('/')
def index(): return render_template('index.html')

@app.route('/<path:filename>')
def serve_static(filename): return send_from_directory('Models', filename)

app.register_blueprint(submissions_bp)
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

from routes.documents import documents_bp

app.register_blueprint(documents_bp)

from routes.evaluation import evaluation_bp

app.register_blueprint(evaluation_bp)
from routes.progress import progress_bp

app.register_blueprint(progress_bp)

from routes.dashboard import dashboard_bp
app.register_blueprint(dashboard_bp)