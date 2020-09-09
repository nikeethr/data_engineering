import os
import base64
from poama.app import app, server
from poama.layouts import layout_main
import poama.callbacks


__DEV = True
__VM_HOST = "192.168.56.101"

app.secret_key = os.environb[b'DASH_SECRET_KEY']
print(app.secret_key)
app.layout = layout_main()


if __name__ == '__main__':
    if __DEV:
        app.run_server(debug=True, port=8050, host=__VM_HOST)
    else:
        # TODO
        pass
