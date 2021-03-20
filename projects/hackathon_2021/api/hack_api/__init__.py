from flask import Flask

# Structure from: https://lepture.com/en/2018/structure-of-a-flask-project

def create_app(local=False):
    # from. import models, routes, services
    from . import models, routes
    from .models.model import MONGO_DB

    app = Flask(__name__)

    # TODO: this is a prototype/POC only - these credentials need to be saved
    # somehwere better in prod
    # TODO: move config to file
    # TODO: configure actual user with appropriate permissions
    host = 'mongo_db'
    if local:
        host = 'localhost'
    app.config['MONGO_URI'] = 'mongodb://{user}:{pswd}@{host}:{port}/{db}?authSource=admin'.format(
        user='root', pswd='1234', host=host, port='27017', db=MONGO_DB
    )
    models.init_app(app)
    routes.init_app(app)
    # services.init_app(app)

    return app
