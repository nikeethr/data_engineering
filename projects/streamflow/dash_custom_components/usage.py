import pandas as pd
import dash_custom_components
import dash
from dash.dependencies import Input, Output
import dash_html_components as html

app = dash.Dash(__name__)

df = pd.read_csv('data/random_data.csv')
data = df.to_dict('records')

app.layout = html.Div([
    dash_custom_components.Calendar(
        id='input',
        value='my-value',
        label='my-label',
        data=data
    ),
    html.Div(id='output')
])


# @app.callback(Output('output', 'children'), [Input('input', 'value')])
# def display_output(value):
#     return 'You have entered {}'.format(value)


if __name__ == '__main__':
    app.run_server(debug=True)
