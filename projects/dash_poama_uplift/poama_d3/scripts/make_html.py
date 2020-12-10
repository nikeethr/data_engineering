import os
from jinja2 import Environment, FileSystemLoader, select_autoescape


DIR = os.path.dirname(os.path.realpath(__file__))
TEMPLATES_DIR = os.path.join(DIR, 'templates')
OUT_DIR = os.path.join(DIR, 'out')

env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(['html'])
)


def make_html():
    lat_range = [-70, -40]
    lon_range = [0, 180]
    js_include = '/js/main-svg.js'
    css_include = '/css/style.css'
    plot_data_url = '/data/ovt_data.json'

    index_template = env.get_template('index-template.html')

    with open(os.path.join(OUT_DIR, 'index.html'), 'w') as f:
        out_str = index_template.render(
            lat_range=lat_range,
            lon_range=lon_range,
            js_include=js_include,
            css_include=css_include,
            plot_data_url=plot_data_url
        )
        f.write(out_str)


if __name__ == '__main__':
    make_html()
