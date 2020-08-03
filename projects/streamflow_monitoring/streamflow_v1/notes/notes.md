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
