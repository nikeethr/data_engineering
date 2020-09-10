import os
import dash_auth


def add_auth_to_app(app):
    user = os.environ['POAMA_USER']
    passwd = os.environ['POAMA_PASSWD']
    dash_auth.BasicAuth(app, {
        user: passwd
    })
