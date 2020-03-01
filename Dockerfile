FROM python:3.8
ADD . /code
WORKDIR /code
RUN pip3 install -r requirements.txt
CMD python3 netpalm.py