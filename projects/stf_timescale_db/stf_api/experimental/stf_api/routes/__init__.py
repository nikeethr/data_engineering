from .stf_route_test import stf_bp


def init_app(app):
    app.register_blueprint(stf_bp)
