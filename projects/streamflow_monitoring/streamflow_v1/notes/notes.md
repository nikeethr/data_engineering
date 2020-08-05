## Create env

```sh
$ conda create -n streamflow-<version> python=3.7
$ conda activate streamflow-<version>
$ pip install -r requirements.txt
```

## Structure project

- Basic project structure:
https://dash.plotly.com/dash-enterprise/application-structure

- Separating concerns (also applicable for multi URL apps):
https://dash.plotly.com/urls

- May need to run `gunicorn` manually in docker container as opposed to
Procfile

## Layout

- Used dash bootstrap components for grid based layout
- potentially need to change this up for side-bar since it's quite a simple app
- example for sidebar: https://dash-bootstrap-components.opensource.faculty.ai/examples/simple-sidebar/
  - It would be good to do it this way eventually

## matrix plot

- Was simple enough using go.Heatmap
- Needed some exploration on how to adjust color scales (colorscale) and how to
adjust legend (colorbar)

## streamflow graph

- extracted plots from v0
- had to do some thought on data storage (currently intermediate div with json dump)
- this is so that hourly/daily data is loaded in one go and so switching
  between hourly/daily does not incur extra compute.
