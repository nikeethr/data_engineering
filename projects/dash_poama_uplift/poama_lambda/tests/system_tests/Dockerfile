FROM python:3.8-slim

WORKDIR /tmp

COPY requirements.txt .
COPY generate_test_data.py .

RUN pip3 install -r requirements.txt

CMD [ "python3", "generate_test_data.py" ]
