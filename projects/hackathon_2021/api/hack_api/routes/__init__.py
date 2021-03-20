from .hack_routes import hack_bp


def init_app(app):
    app.register_blueprint(hack_bp)
