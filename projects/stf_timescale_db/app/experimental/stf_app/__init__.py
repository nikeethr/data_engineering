from flask import Flask

# Structure from: https://lepture.com/en/2018/structure-of-a-flask-project

def create_app():
    # from. import models, routes, services
    from . import models

    app = Flask(__name__)
    # TODO: move config to file
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://app_user:1234@localhost:5432/stf_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    models.init_app(app)
    # routes.init_app(app)
    # services.init_app(app)

    return app
