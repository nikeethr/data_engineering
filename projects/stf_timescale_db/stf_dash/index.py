from gevent import monkey
monkey.patch_all()

import stf_app.callbacks
import stf_app.data_fetch
from stf_app.app import app
from stf_app.layouts import layout_main


app.layout = layout_main()
server = app.server


if __name__ == '__main__':
    # debug mode
    stf_app.data_fetch.STF_API_URI = stf_app.data_fetch.DEBUG_STF_API_URI
    app.run_server(host='0.0.0.0', port=8051, debug=True)
