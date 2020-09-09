# Poama dash app


## Rough notes

### TODO

- [ ] Setup repo conda environment etc.
- [ ] Get sample config
- [ ] Create base layout of app

### Setup repo

- `requirements.txt`: contains the requirements of all the packages needed to
  run this app.
- `index.py`: main python file that runs the server
- `.gitignore`: ignore artifacts from building app for git commits
- `Procfile`: This is a heroku thing to determine how to spin up workers etc.
- `runtime.txt`: Which python version to run (will use 3.6.7 if omitted)
- `CHECKS`: Custom checks to be performed on app on deployment
- `poama_app`: where the main app code sits (will not go through details for
  this layout but there is a logical split between layout, data logic etc.)
- `poama/assets`: custom html/js/css to be loaded on render
 
for more info see: https://dash.plotly.com/dash-enterprise/application-structure

### Installation

Assume conda is install then:

```
conda create -n dash-poama python=3
conda activate dash-poama
pip install requirements.txt
```

### Environment setup

You will need to set these up in the docker environment and dump it in
`poama_app/.env-docker-file` 

**!IMPORTANT!:** these should not be commited to the repo/be available
publically

Note: The user/pass uses dash basic auth. It's mainly for development only and
isn't really very secure.

```bash
POAMA_USER=xxx          # username for the app
POAMA_PASSWD=xxx        # password for the app
DASH_SECRET_KEY=xxx     # (bytes) required by flask/gunicorn to run multiple
                        # workers see below regarding csrf key
```

### Local Gunicorn

- needed a csrf key: https://flask.palletsprojects.com/en/1.1.x/quickstart/#sessions
- static stuff is in the assets folder but you can also use nginx to serve via
  reverse proxy.

### nginx reverse proxy

- So `poama_app/poama/assets` will normally contain the assets. But it also
  uses the folder to render the html to expect those assets.
- `nginx/assets` will contain the real assets configured by the directives in
  `nginx/project.conf`
- in order to test that we are using the reverse proxy, simply replace `assets`
  in `poama_app/poama/assets` with the contents of `assets_dummy` (basically
  blank asset files)
- Then via port 5000 (directly to dash) you should see it rendered badly,
  whereas via port 5001 (nginx) it will be fine.

**!IMPORTANT!:** `nginx` (and docker-compose stuff) is for testing purposes
only.  Elastic beanstalk has its own `nginx` setup, so it will not be part of
the deployment. HOWEVER, if there are issues with rendering, then potentially
similar directives need to be setup on the EC2 instances after container boot.

### Running gunicorn + nginx

Simply run the commands 

### Running nginx only

### Deploy to EB using docker

https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/single-container-docker.html


