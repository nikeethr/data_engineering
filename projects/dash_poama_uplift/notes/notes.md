# poama FVT uplift

## TODO

- [ ] Separate image fetching/data fetching stuff into a separate container
  with flask service
    - This is so that the data api container can be updated to source
      images/json and access user database etc. without needing to change the
      view (dash) app.
    - Make sure not to expose the data api - it should only be able to talk to
      the dash container directly
    - Proper authentication needs to be put in place for the dash app (see
      below). Which should translate to fetching stuff using the data container
      which has access to private resources.
- [ ] Change callbacks to be client side js (as much as possible - reduces server load)
- [ ] Change image fetching logic to send a blob instead of entire base64 Data URI
- [ ] Upgrade login in dash app e.g. using flask-login
- [ ] handle data comms between dash-flask container and data-flask container
      (i.e. restrict calling data api)
- [ ] Upgrade elastic beanstalk deployment to multi-container app
- [ ] Add plotly zoom feature on images
- [ ] Make sample plotly graph from dummy data
- [ ] Make sample plotly graph with real data from a product (data needs to be
  hosted somewhere...)
- [ ] Update notes/docs/instructions and comment code a bit better

Done:
- [x] Setup repo conda environment etc.
- [x] Get sample config
- [x] Create base layout of app
- [x] Register callbacks
- [x] Dockerize it
- [x] Deploy to elastic beanstalk


# Rough Notes

## Dash app

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
pip install -r requirements.txt
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

**Advisable to create separate conda environment for EB CLI**:

https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/single-container-docker.html

#### Create CLI user for EB
https://aws.amazon.com/getting-started/hands-on/set-up-command-line-elastic-beanstalk/

#### Environment variables
Create a file in  .ebextensions/environment.config
```
option_settings:
    aws:elasticbeanstalk:application:environment:
        POAMA_USER:xxx
        POAMA_PASSWD:xxx
        DASH_SECRET_KEY:xxx
```

## API

### Create separate environment for API dev

```
conda create -n 'poama-api' python=3
conda activate poama-api
pip install -r requirements.txt
```

### Create flask api to serve image

Initially we will expose the port for dev but will be restricted to only the
dash app

Setup:
- Create flask app with route to GET image using a parameter e.g. `product_id`
- Create secret key + gunicorn instructions to run app in docker (similar to
  dash app)
- Dockerfile


### Run all services together

#### update docker-compose

#### hook up api with dash app

#### update nginx conf

To test out directly accessing API.


### Authentication

There will be two parts:
- The dashboard will require a login which then allows the client to reach the
  API
    - We can use flask-login for this
- The API will require auth (e.g. if we want to access it directly in the
  future). There will be two parts for this:
    - Simple login to generate token (e.g. can use flask login)
    - Token generation: e.g. using JWT - the dash app should store this in the
      browser session
    - API will have to require a valid token

**TODO: at the moment there is no user database and credentials are stored
somewhere secret that the server can access**

#### Add flask-login for dash app

#### Add token authentication for api
