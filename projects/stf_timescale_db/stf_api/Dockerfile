# get base image for 3.7 (slim)
FROM python:3.7-slim

ENV PORT_API=8051

# copy requirements.txt
COPY requirements.txt requirements.txt

# install requirements (no-cache)
RUN pip3 install -r requirements.txt --no-cache-dir

# copy experiment folder
COPY experimental experimental
WORKDIR experimental

# gunicorn command to run the api
CMD gunicorn \
    --bind=0.0.0.0:$PORT_API \
    --worker-class=gevent \
    run_stf_api:app
