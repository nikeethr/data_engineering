from stf_app.app import app
from stf_app.layouts import layout_main
import stf_app.callbacks


app.layout = layout_main()


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8051, debug=True)
