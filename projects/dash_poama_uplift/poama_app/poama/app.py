import dash
import dash_bootstrap_components as dbc


app = dash.Dash(
    __name__,
    # you may need to add css assets manually when deploying through docker:
    external_stylesheets=[dbc.themes.FLATLY, dbc.themes.GRID],
    # may need to set to True for dynamic layout:
    suppress_callback_exceptions=False,
    assets_url_path='/assets'
)
server = app.server
