"""
Routes package - API endpoints
Chứa các route handlers cho Flask app
"""
from API.routes.batches import batches_bp
from API.routes.topics import topics_bp, mentors_bp
from API.routes.groups import groups_bp

def init_api_routes(app):
    app.register_blueprint(batches_bp)
    app.register_blueprint(topics_bp)
    app.register_blueprint(mentors_bp)
    app.register_blueprint(groups_bp)
