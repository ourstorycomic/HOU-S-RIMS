# routes/__init__.py
def init_routes(app):
    from .upload import upload_bp
    from .plot import plot_bp
    from .assistant import assistant_bp
    from .cleaning import clean_bp
    from .document import document_bp
    from .web import web_bp
    from .auth import auth_bp
    from .analysis import analysis_bp
    from .powerbi import powerbi_bp
    from .process import process_bp
    from .student import student_bp
    from .calendar import calendar_bp
    from .chat import chat_bp

    app.register_blueprint(upload_bp)
    app.register_blueprint(plot_bp)
    app.register_blueprint(assistant_bp)
    app.register_blueprint(clean_bp)
    app.register_blueprint(document_bp)
    app.register_blueprint(web_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(powerbi_bp)
    app.register_blueprint(process_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(calendar_bp)
    app.register_blueprint(chat_bp)
