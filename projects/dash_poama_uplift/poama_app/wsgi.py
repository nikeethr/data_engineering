import os
import base64
from poama.app import app, server
from poama.layouts import layout_main
import poama.callbacks
import poama.auth


# needed for gunicorn + multiple workers
app.secret_key = os.environb[b'DASH_SECRET_KEY']
app.layout = layout_main()
auth = poama.auth.add_auth_to_app(app)

if __name__ == '__main__':
    __DEV = True
    __VM_HOST = "192.168.56.101"

    if __DEV:
        app.run_server(debug=True, port=8050, host=__VM_HOST)
    else:
        # TODO
        pass
