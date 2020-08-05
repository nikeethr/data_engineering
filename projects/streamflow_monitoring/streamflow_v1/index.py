from streamflow.app import app
from streamflow.layouts import layout_main
import streamflow.callbacks


app.layout = layout_main()


if __name__ == '__main__':
    app.run_server(debug=True)
