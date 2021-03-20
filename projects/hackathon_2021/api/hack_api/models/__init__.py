from .base import mongo_db

def init_app(app):
    mongo_db.init_app(app)
