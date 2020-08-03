import dash
import dash_bootstrap_components as dbc


app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],  # you may need to add css assets manually when deploying through docker
    suppress_callback_exceptions=False       # may need to set to True for dynamic layout
)
server = app.server
