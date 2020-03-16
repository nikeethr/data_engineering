import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta

import dash_html_components as html
import dash_custom_components
import dash
from dash.dependencies import Input, Output
import dash_html_components as html

app = dash.Dash(__name__)


def random_data():
    YEARS_MAX = 5
    years = np.random.uniform(low=1, high=YEARS_MAX)
    start = pd.to_datetime('2014-01-01')
    end = start + relativedelta(years=int(years))

    date_range = pd.date_range(start, end)
    data = np.abs(np.random.normal(0, 1, size=len(date_range)))
    df = pd.DataFrame({'date': date_range, 'value': data})
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')

    print(date_range)

    return df.to_dict('records')

app.layout = html.Div([
    html.Button('Regenerate', id='button'),
    dash_custom_components.Calendar(
        id='calendar',
        value='my-value',
        label='my-label',
        data=random_data()
    ),
    html.Div(id='output')
])


@app.callback(Output('calendar', 'data'), [Input('button', 'n_clicks')])
def display_output(n_clicks):
    d = random_data()
    return d


if __name__ == '__main__':
    app.run_server(debug=True)
