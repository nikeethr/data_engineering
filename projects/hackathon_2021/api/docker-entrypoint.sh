#!/bin/bash

# start rq worker
systemctl enable rqworker

# gunicorn command to run the api
gunicorn \
    --bind=0.0.0.0:$PORT_API \
    --worker-class=gevent \
    run_hack_api:app &

exec "$@"
