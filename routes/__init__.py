# routes/__init__.py
def init_routes(app):
    from .upload import upload_bp
    from .plot import plot_bp
    from .chat import chat_bp
    from .cleaning import clean_bp
    from .document import document_bp
    from .web import web_bp
    from .auth import auth_bp

    app.register_blueprint(upload_bp)
    app.register_blueprint(plot_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(clean_bp)
    app.register_blueprint(document_bp)
    app.register_blueprint(web_bp)
    app.register_blueprint(auth_bp)