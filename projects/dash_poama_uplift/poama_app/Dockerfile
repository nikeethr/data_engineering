FROM python:3.8.5-slim 

LABEL maintainer="Nikeeth Ramanathan <nikeeth.ramanathan@gmail.com>"

RUN [ ! -d "app" ] && mkdir app

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 5000

CMD [ "gunicorn", "-b", "0.0.0.0:5000", "-w", "2", "wsgi:server" ]
