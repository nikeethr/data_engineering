FROM python:3.8-slim

# install systemd for background worker

RUN apt-get update && \
    apt-get install -y systemd

# create api dir to copy things to
RUN mkdir api
WORKDIR api

# copy requirements.txt
COPY requirements.txt requirements.txt

# install requirements (no-cache)
RUN pip3 install -r requirements.txt --no-cache-dir

# copy worker service
COPY rqworker.service /etc/systemd/system/rqworker.service

# copy everythign else
COPY . .

# set env variable
ENV PYTHONPATH="${PYTHON_PATH:-}/api/hack_api"
ENV PORT_API=8052

# docker entry point to do some setup
ENTRYPOINT ["./docker-entrypoint.sh"]

# run systemd to run background stuff
CMD ["/lib/systemd/systemd"]
