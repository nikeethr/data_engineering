# get base image for 3.7 (slim)
FROM python:3.7-slim

ENV PORT_APP=8051

# copy requirements.txt
COPY requirements.txt requirements.txt

# install requirements (no-cache)
RUN pip3 install -r requirements.txt --no-cache-dir

# copy experiment folder
COPY index.py index.py
COPY stf_app stf_app

# gunicorn command to run the api
CMD gunicorn \
    --bind=0.0.0.0:$PORT_APP \
    --worker-class=gevent \
    index:server
