import os
import flask
import api
from api.image import image_api

app = flask.Flask(__name__)
app.secret_key = os.environb[b'DASH_SECRET_KEY']
app.register_blueprint(image_api)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8051', debug=True)
