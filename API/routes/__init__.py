"""
Routes package - API endpoints
Chứa các route handlers cho Flask app
"""
from API.routes.batches import batches_bp
from API.routes.topics import topics_bp, mentors_bp
from API.routes.groups import groups_bp
from API.routes.submissions import submissions_bp
from API.routes.documents import documents_bp
from API.routes.evaluation import evaluation_bp
from API.routes.progress import progress_bp
from API.routes.dashboard import dashboard_bp
from API.routes.auth import auth_bp
from API.routes.profile import profile_bp
from API.routes.calendar import calendar_bp
from API.routes.notifications import notifications_bp

def init_api_routes(app):
    app.register_blueprint(batches_bp)
    app.register_blueprint(topics_bp)
    app.register_blueprint(mentors_bp)
    app.register_blueprint(groups_bp)
    app.register_blueprint(submissions_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(evaluation_bp)
    app.register_blueprint(progress_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(calendar_bp)
    app.register_blueprint(notifications_bp)
